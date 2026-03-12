from __future__ import annotations

import json
from collections.abc import Generator

from ..models.schemas import ChatAnswer, ChatRequest, ChatStreamEnvelope, Citation, RetrievalDebugRequest, ToolTrace
from .retrieval_service import RetrievalService


class ChatService:
    def __init__(self, retrieval_service: RetrievalService | None = None) -> None:
        self.retrieval_service = retrieval_service or RetrievalService()

    def stream(self, payload: ChatRequest) -> Generator[str, None, None]:
        answer_text = (
            "Parent Document Retrieval 更适合教程型文档，因为它用子块做命中、用父块还原上下文，"
            "能同时保留章节逻辑与答案局部相关性。"
        )
        tool_trace = ToolTrace(
            name="rag_search",
            status="completed",
            input={"query": payload.message, "kb_id": payload.kb_id},
            output={"top_k": 8, "strategy": "hybrid+rerank"},
        )
        citation = Citation(
            document_id="doc-langchain-notes",
            file_name="langchain-notes.md",
            page=12,
            chunk_id="p-11",
            rerank_score=0.96,
        )

        for token in answer_text.split("，"):
            if token:
                yield self._to_sse(ChatStreamEnvelope(event="token", data={"text": token + "，"}))

        yield self._to_sse(ChatStreamEnvelope(event="tool_call", data=tool_trace.model_dump()))

        if payload.debug and payload.kb_id:
            debug_payload = self.retrieval_service.debug(
                RetrievalDebugRequest(user_id=payload.user_id, kb_id=payload.kb_id, query=payload.message)
            )
            yield self._to_sse(ChatStreamEnvelope(event="retrieval_debug", data=debug_payload.model_dump(mode="json")))

        final_answer = ChatAnswer(
            session_id=payload.session_id or "demo-session",
            answer=answer_text,
            citations=[citation],
            tool_trace=[tool_trace],
        )
        yield self._to_sse(ChatStreamEnvelope(event="final_answer", data=final_answer.model_dump(mode="json")))

    @staticmethod
    def _to_sse(event: ChatStreamEnvelope) -> str:
        return f"event: {event.event}\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"
