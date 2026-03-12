from __future__ import annotations

import math
from collections import Counter, defaultdict

from ..models.orm import DocumentChunk
from ..repos.documents import DocumentRepository
from .embeddings import cosine_similarity, embed_text, term_frequencies
from .reranker import Reranker


class HybridRetriever:
    def __init__(
        self,
        repo: DocumentRepository | None = None,
        reranker: Reranker | None = None,
        *,
        recall_top_k: int = 40,
        rerank_top_k: int = 16,
        mmr_lambda: float = 0.72,
    ) -> None:
        self.repo = repo or DocumentRepository()
        self.reranker = reranker or Reranker()
        self.recall_top_k = recall_top_k
        self.rerank_top_k = rerank_top_k
        self.mmr_lambda = mmr_lambda

    def retrieve(
        self,
        *,
        user_id: str,
        kb_id: str,
        query: str,
        top_k: int = 20,
        retrieval_mode: str = "hybrid",
        recall_top_k: int | None = None,
        rerank_top_k: int | None = None,
    ) -> dict:
        child_chunks = self.repo.list_chunks_by_kb(user_id=user_id, kb_id=kb_id, chunk_type="child")
        if not child_chunks:
            return {
                "query": query,
                "kb_id": kb_id,
                "retrieval_mode": retrieval_mode,
                "vector_hits": [],
                "bm25_hits": [],
                "rrf_hits": [],
                "rerank_hits": [],
                "diverse_hits": [],
                "final_context": [],
            }

        recall_limit = max(30, min(50, recall_top_k or self.recall_top_k))
        rerank_limit = max(12, min(20, rerank_top_k or self.rerank_top_k, recall_limit))

        vector_hits = self._vector_hits(query, child_chunks, limit=recall_limit)
        bm25_hits = self._bm25_hits(query, child_chunks, limit=recall_limit)

        if retrieval_mode == "vector":
            rrf_hits = list(vector_hits)
            rerank_input = list(vector_hits)
        elif retrieval_mode == "bm25":
            rrf_hits = list(bm25_hits)
            rerank_input = list(bm25_hits)
        else:
            rrf_hits = self._rrf_hits(vector_hits, bm25_hits, limit=recall_limit)
            rerank_input = list(rrf_hits)

        rerank_hits = self.reranker.rerank(query, rerank_input, limit=rerank_limit)
        parent_candidates = self._expand_parent_context(rerank_hits)
        diverse_hits = self._select_diverse_contexts(query, parent_candidates, limit=rerank_limit)
        final_context = [self._strip_internal_fields(hit) for hit in diverse_hits[:top_k]]

        return {
            "query": query,
            "kb_id": kb_id,
            "retrieval_mode": retrieval_mode,
            "vector_hits": [self._strip_internal_fields(hit) for hit in vector_hits[:recall_limit]],
            "bm25_hits": [self._strip_internal_fields(hit) for hit in bm25_hits[:recall_limit]],
            "rrf_hits": [self._strip_internal_fields(hit) for hit in rrf_hits[:recall_limit]],
            "rerank_hits": [self._strip_internal_fields(hit) for hit in rerank_hits[:rerank_limit]],
            "diverse_hits": [self._strip_internal_fields(hit) for hit in diverse_hits],
            "final_context": final_context,
            "recall_top_k": recall_limit,
            "rerank_top_k": rerank_limit,
        }

    def _vector_hits(self, query: str, chunks: list[DocumentChunk], limit: int) -> list[dict]:
        query_embedding = embed_text(query)
        hits: list[dict] = []
        for chunk in chunks:
            score = cosine_similarity(query_embedding, chunk.embedding)
            if score <= 0:
                continue
            hits.append(self._serialize_chunk(chunk, score))
        hits.sort(key=lambda item: item["score"], reverse=True)
        return hits[:limit]

    def _bm25_hits(self, query: str, chunks: list[DocumentChunk], limit: int) -> list[dict]:
        query_terms = term_frequencies(query)
        if not query_terms:
            return []

        corpus_terms = [term_frequencies(chunk.content) for chunk in chunks]
        document_lengths = [sum(terms.values()) or 1 for terms in corpus_terms]
        avg_document_length = sum(document_lengths) / max(1, len(document_lengths))
        document_frequency = self._document_frequency(query_terms, corpus_terms)
        total_documents = len(chunks)

        hits: list[dict] = []
        for chunk, terms, document_length in zip(chunks, corpus_terms, document_lengths, strict=False):
            score = self._bm25_score(
                query_terms=query_terms,
                document_terms=terms,
                document_length=document_length,
                avg_document_length=avg_document_length,
                total_documents=total_documents,
                document_frequency=document_frequency,
            )
            if score <= 0:
                continue
            hits.append(self._serialize_chunk(chunk, score))

        hits.sort(key=lambda item: item["score"], reverse=True)
        return hits[:limit]

    def _rrf_hits(self, vector_hits: list[dict], bm25_hits: list[dict], limit: int) -> list[dict]:
        fused_scores: dict[str, float] = defaultdict(float)
        merged: dict[str, dict] = {}

        for rank, hit in enumerate(vector_hits, start=1):
            fused_scores[hit["chunk_id"]] += 1.0 / (60 + rank)
            merged.setdefault(hit["chunk_id"], dict(hit))

        for rank, hit in enumerate(bm25_hits, start=1):
            fused_scores[hit["chunk_id"]] += 1.0 / (60 + rank)
            merged.setdefault(hit["chunk_id"], dict(hit))

        ranked: list[dict] = []
        for chunk_id, score in fused_scores.items():
            item = dict(merged[chunk_id])
            item["score"] = score
            ranked.append(item)

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:limit]

    def _expand_parent_context(self, rerank_hits: list[dict]) -> list[dict]:
        parent_ids = [str(hit["parent_id"]) for hit in rerank_hits if hit.get("parent_id")]
        parent_chunks = {
            chunk.id: chunk
            for chunk in self.repo.list_chunks_by_ids(parent_ids)
        }

        contexts: list[dict] = []
        seen_context_ids: set[str] = set()
        for hit in rerank_hits:
            context_chunk = parent_chunks.get(str(hit.get("parent_id")))
            if context_chunk is None:
                context_id = str(hit["chunk_id"])
                context_payload = dict(hit)
            else:
                context_id = context_chunk.id
                context_payload = self._serialize_chunk(context_chunk, float(hit["score"]))
                metadata = dict(context_payload["metadata"])
                metadata["supporting_chunk_id"] = hit["chunk_id"]
                metadata["supporting_chunk_preview"] = hit["content_preview"]
                context_payload["metadata"] = metadata

            if context_id in seen_context_ids:
                continue
            seen_context_ids.add(context_id)
            contexts.append(context_payload)

        return contexts

    def _select_diverse_contexts(self, query: str, candidates: list[dict], limit: int) -> list[dict]:
        if not candidates or limit <= 0:
            return []

        query_embedding = embed_text(query)
        selected: list[dict] = []
        remaining = list(candidates)

        while remaining and len(selected) < limit:
            best_index = 0
            best_score = float("-inf")

            for index, candidate in enumerate(remaining):
                score = self._mmr_score(query_embedding, candidate, selected)
                if score > best_score:
                    best_score = score
                    best_index = index

            selected.append(remaining.pop(best_index))

        return selected

    @staticmethod
    def _serialize_chunk(chunk: DocumentChunk, score: float) -> dict:
        metadata = dict(chunk.metadata_json or {})
        return {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "file_name": chunk.document.file_name if chunk.document else metadata.get("file_name", "unknown"),
            "content": chunk.content,
            "content_preview": chunk.content[:220],
            "score": float(score),
            "parent_id": chunk.parent_id,
            "metadata": metadata,
            "_embedding": list(chunk.embedding) if chunk.embedding is not None else None,
        }

    def _mmr_score(self, query_embedding: list[float], candidate: dict, selected: list[dict]) -> float:
        relevance = max(float(candidate.get("score", 0.0)), cosine_similarity(query_embedding, candidate.get("_embedding")))
        redundancy = 0.0
        if selected:
            redundancy = max(cosine_similarity(candidate.get("_embedding"), item.get("_embedding")) for item in selected)

        doc_penalty = 0.08 if any(item.get("document_id") == candidate.get("document_id") for item in selected) else 0.0
        candidate_section = tuple(candidate.get("metadata", {}).get("section_path", []))
        section_penalty = (
            0.04
            if candidate_section
            and any(tuple(item.get("metadata", {}).get("section_path", [])) == candidate_section for item in selected)
            else 0.0
        )
        return self.mmr_lambda * relevance - (1.0 - self.mmr_lambda) * redundancy - doc_penalty - section_penalty

    @staticmethod
    def _strip_internal_fields(item: dict) -> dict:
        payload = dict(item)
        payload.pop("_embedding", None)
        return payload

    @staticmethod
    def _document_frequency(query_terms: Counter[str], corpus_terms: list[Counter[str]]) -> dict[str, int]:
        frequencies: dict[str, int] = {}
        for term in query_terms:
            frequencies[term] = sum(1 for terms in corpus_terms if term in terms)
        return frequencies

    @staticmethod
    def _bm25_score(
        *,
        query_terms: Counter[str],
        document_terms: Counter[str],
        document_length: int,
        avg_document_length: float,
        total_documents: int,
        document_frequency: dict[str, int],
    ) -> float:
        score = 0.0
        k1 = 1.5
        b = 0.75

        for term, query_weight in query_terms.items():
            tf = document_terms.get(term, 0)
            if tf <= 0:
                continue
            df = document_frequency.get(term, 0)
            idf = math.log(1 + (total_documents - df + 0.5) / (df + 0.5))
            denominator = tf + k1 * (1 - b + b * document_length / max(avg_document_length, 1.0))
            score += query_weight * idf * ((tf * (k1 + 1)) / max(denominator, 1e-9))

        return score
