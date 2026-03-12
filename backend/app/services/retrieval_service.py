from __future__ import annotations

from flask import current_app

from ..models.orm import RetrievalLog
from ..models.schemas import RetrievalDebugRequest, RetrievalDebugResponse, RetrievalHit
from ..rag.context_builder import ContextBuilder
from ..rag.hybrid import HybridRetriever
from ..rag.tokenizer import count_tokens
from ..repos.retrieval_logs import RetrievalLogRepository


class RetrievalService:
    def __init__(
        self,
        retriever: HybridRetriever | None = None,
        log_repo: RetrievalLogRepository | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.retriever = retriever or HybridRetriever()
        self.log_repo = log_repo or RetrievalLogRepository()
        self.context_builder = context_builder or ContextBuilder()

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
        result = self.retriever.retrieve(
            user_id=user_id,
            kb_id=kb_id,
            query=query,
            top_k=top_k or current_app.config.get("DEFAULT_TOP_K", 8),
            retrieval_mode=retrieval_mode,
            recall_top_k=current_app.config.get("RECALL_TOP_K", 40),
            rerank_top_k=current_app.config.get("RERANK_TOP_K", 16),
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
