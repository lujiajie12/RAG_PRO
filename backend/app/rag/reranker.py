from __future__ import annotations

from .embeddings import term_frequencies


class Reranker:
    def rerank(self, query: str, candidates: list[dict], limit: int | None = None) -> list[dict]:
        query_terms = term_frequencies(query)
        ranked: list[dict] = []

        for candidate in candidates:
            candidate_terms = term_frequencies(candidate.get("content", ""))
            coverage = sum(min(query_terms[term], candidate_terms.get(term, 0)) for term in query_terms)
            density = coverage / max(1, len(candidate_terms))
            base_score = float(candidate.get("score", 0.0))
            rerank_score = base_score + coverage * 0.08 + density * 0.6
            enriched = dict(candidate)
            enriched["score"] = rerank_score
            enriched["rerank_score"] = rerank_score
            ranked.append(enriched)

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:limit] if limit is not None else ranked
