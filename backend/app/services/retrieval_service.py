from __future__ import annotations

import re
from pathlib import Path

from flask import current_app

from ..models.orm import RetrievalLog
from ..models.schemas import RetrievalDebugRequest, RetrievalDebugResponse, RetrievalHit
from ..rag.context_builder import ContextBuilder
from ..rag.hybrid import HybridRetriever
from ..rag.tokenizer import count_tokens
from ..repos.documents import DocumentRepository
from ..repos.retrieval_logs import RetrievalLogRepository


class RetrievalService:
    def __init__(
        self,
        retriever: HybridRetriever | None = None,
        log_repo: RetrievalLogRepository | None = None,
        context_builder: ContextBuilder | None = None,
        document_repo: DocumentRepository | None = None,
    ) -> None:
        self.retriever = retriever or HybridRetriever()
        self.log_repo = log_repo or RetrievalLogRepository()
        self.context_builder = context_builder or ContextBuilder()
        self.document_repo = document_repo or DocumentRepository()

    def search(
        self,
        *,
        user_id: str,
        kb_id: str,
        query: str,
        session_id: str | None = None,
        retrieval_mode: str = "hybrid",
        top_k: int | None = None,
        history: list[dict] | None = None,
        memories: list[dict] | None = None,
    ) -> dict:
        document_focus = self._resolve_document_focus(
            user_id=user_id,
            kb_id=kb_id,
            query=query,
            history=history or [],
        )
        result = self.retriever.retrieve(
            user_id=user_id,
            kb_id=kb_id,
            query=query,
            top_k=top_k or current_app.config.get("DEFAULT_TOP_K", 8),
            retrieval_mode=retrieval_mode,
            recall_top_k=current_app.config.get("RECALL_TOP_K", 40),
            rerank_top_k=current_app.config.get("RERANK_TOP_K", 16),
            document_ids=document_focus["document_ids"] if document_focus else None,
            document_summary_mode=bool(document_focus and document_focus["summary_mode"]),
        )
        context_plan = self.context_builder.build(
            history or [],
            memories or [],
            result["diverse_hits"],
            query,
            context_token_budget=current_app.config.get("CONTEXT_TOKEN_BUDGET", 2400),
        )
        result["context_plan"] = context_plan
        result["final_context"] = context_plan["retrieved_context"]
        result["prompt_budget"] = self._prompt_budget(query, context_plan)
        result["document_focus"] = document_focus
        self._log_search(user_id=user_id, session_id=session_id, kb_id=kb_id, query=query, result=result)
        return result

    def debug(self, payload: RetrievalDebugRequest) -> RetrievalDebugResponse:
        result = self.search(
            user_id=payload.user_id,
            kb_id=payload.kb_id,
            query=payload.query,
            retrieval_mode="hybrid",
        )
        return self.build_debug_response(payload.query, result)

    def build_debug_response(self, query: str, result: dict) -> RetrievalDebugResponse:
        return RetrievalDebugResponse(
            query=query,
            vector_hits=self._to_hits(result["vector_hits"]),
            bm25_hits=self._to_hits(result["bm25_hits"]),
            rrf_hits=self._to_hits(result["rrf_hits"]),
            rerank_hits=self._to_hits(result["rerank_hits"]),
            final_context=self._to_hits(result["final_context"]),
            prompt_budget=result["prompt_budget"],
        )

    @staticmethod
    def _to_hits(items: list[dict]) -> list[RetrievalHit]:
        hits: list[RetrievalHit] = []
        for item in items:
            metadata = dict(item.get("metadata", {}))
            hits.append(
                RetrievalHit(
                    chunk_id=str(item["chunk_id"]),
                    file_name=str(item.get("file_name", "unknown")),
                    content_preview=str(item.get("content_preview", "")),
                    score=float(item.get("score", 0.0)),
                    parent_id=item.get("parent_id"),
                    metadata=metadata,
                )
            )
        return hits

    @staticmethod
    def _prompt_budget(query: str, context_plan: dict) -> dict[str, int]:
        token_usage = context_plan.get("token_usage", {})
        return {
            "system": 600,
            "history": int(token_usage.get("history", 0)),
            "memory": int(token_usage.get("memory", 0)),
            "retrieved_context": int(token_usage.get("retrieved_context", 0)),
            "user_query": count_tokens(query),
            "retrieved_context_budget": int(context_plan.get("token_budget", 0)),
        }

    def _log_search(
        self,
        *,
        user_id: str,
        session_id: str | None,
        kb_id: str,
        query: str,
        result: dict,
    ) -> None:
        log = RetrievalLog(
            user_id=user_id,
            session_id=session_id,
            kb_id=kb_id,
            query=query,
            vector_hits=self._log_items(result["vector_hits"]),
            bm25_hits=self._log_items(result["bm25_hits"]),
            rerank_hits=self._log_items(result["rerank_hits"]),
            final_context=self._log_items(result["final_context"]),
        )
        self.log_repo.create(log)

    def _resolve_document_focus(
        self,
        *,
        user_id: str,
        kb_id: str,
        query: str,
        history: list[dict],
    ) -> dict | None:
        documents = self.document_repo.list_by_kb(user_id, kb_id)
        if not documents:
            return None

        matched = self._match_documents(query, documents)
        source = "query"

        if not matched and self._is_deictic_document_query(query):
            for message in reversed(history):
                matched = self._match_documents(str(message.get("content", "")), documents)
                if matched:
                    source = "history"
                    break

        if not matched:
            return None

        return {
            "document_ids": [document.id for document in matched],
            "file_names": [document.file_name for document in matched],
            "source": source,
            "summary_mode": self._is_document_summary_query(query),
        }

    @staticmethod
    def _match_documents(text: str, documents: list) -> list:
        lowered_text = text.lower()
        normalized_text = RetrievalService._normalize_reference_text(text)
        matched = []
        for document in documents:
            file_name = str(document.file_name)
            file_name_lower = file_name.lower()
            file_stem = Path(file_name).stem
            normalized_file_name = RetrievalService._normalize_reference_text(file_name)
            normalized_stem = RetrievalService._normalize_reference_text(file_stem)

            if (
                file_name_lower in lowered_text
                or (file_stem and file_stem.lower() in lowered_text)
                or (normalized_file_name and normalized_file_name in normalized_text)
                or (normalized_stem and normalized_stem in normalized_text)
            ):
                matched.append(document)
        return matched

    @staticmethod
    def _normalize_reference_text(text: str) -> str:
        return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text.lower())

    @staticmethod
    def _is_deictic_document_query(query: str) -> bool:
        phrases = (
            "这个文档",
            "该文档",
            "这份文档",
            "这个文件",
            "该文件",
            "这篇论文",
            "该论文",
            "这个pdf",
            "这份pdf",
            "this document",
            "that document",
            "the paper",
        )
        lowered = query.lower()
        for phrase in phrases:
            if phrase in lowered:
                return True
        return False

    @staticmethod
    def _is_document_summary_query(query: str) -> bool:
        phrases = (
            "说的什么",
            "讲的什么",
            "主要讲",
            "内容总结",
            "总结",
            "摘要",
            "概述",
            "简述",
            "介绍了什么",
            "内容是什么",
            "总结一下",
            "summarize",
            "summary",
            "what is this document about",
        )
        lowered = query.lower()
        for phrase in phrases:
            if phrase in lowered:
                return True
        return False

    @staticmethod
    def _log_items(items: list[dict]) -> list[dict]:
        return [
            {
                "chunk_id": item["chunk_id"],
                "document_id": item.get("document_id"),
                "file_name": item.get("file_name"),
                "score": item.get("score"),
                "parent_id": item.get("parent_id"),
                "metadata": item.get("metadata", {}),
            }
            for item in items
        ]
