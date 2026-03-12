from __future__ import annotations

import json
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import current_app

from ..agent import AgentRunner, is_agent_enabled
from ..errors import APIError
from ..models.orm import ChatAttachment, Message
from ..models.schemas import ChatAnswer, ChatRequest, ChatStreamEnvelope, Citation, ToolTrace
from ..repos.chat_attachments import ChatAttachmentRepository
from ..repos.sessions import MessageRepository
from .memory_service import MemoryService
from .retrieval_service import RetrievalService
from .session_service import SessionService


@dataclass(slots=True)
class PreparedChatRequest:
    payload: ChatRequest
    attachments: list[ChatAttachment]


class ChatService:
    def __init__(
        self,
        retrieval_service: RetrievalService | None = None,
        session_service: SessionService | None = None,
        message_repo: MessageRepository | None = None,
        attachment_repo: ChatAttachmentRepository | None = None,
        memory_service: MemoryService | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service or RetrievalService()
        self.session_service = session_service or SessionService()
        self.message_repo = message_repo or MessageRepository()
        self.attachment_repo = attachment_repo or ChatAttachmentRepository()
        self.memory_service = memory_service or MemoryService()

    def start_stream(self, payload: ChatRequest) -> Generator[str, None, None]:
        prepared = self._prepare_request(payload)
        return self._stream(prepared)

    def _prepare_request(self, payload: ChatRequest) -> PreparedChatRequest:
        self.session_service.get_session_entity(payload.user_id, payload.session_id)
        attachments = self.attachment_repo.list_by_ids(payload.user_id, payload.session_id, payload.attachment_ids)
        if len(attachments) != len(payload.attachment_ids):
            raise APIError("one or more attachments are invalid for this session", "validation_error", 400)
        return PreparedChatRequest(payload=payload, attachments=attachments)

    def _stream(self, prepared: PreparedChatRequest) -> Generator[str, None, None]:
        payload = prepared.payload
        session = self.session_service.get_session_entity(payload.user_id, payload.session_id)
        user_message = Message(
            session_id=session.id,
            user_id=payload.user_id,
            role="user",
            content=payload.message,
        )
        user_message = self.message_repo.add(user_message)
        if prepared.attachments:
            self.attachment_repo.attach_to_message(prepared.attachments, user_message.id)
        self.session_service.touch_after_user_message(session, payload.message, user_message.created_at or datetime.utcnow())

        try:
            history_messages = self.message_repo.list_by_session(session.id)
            prior_history = history_messages[:-1] if history_messages else []
            retrieval_result = self._retrieve_context(
                payload,
                session.kb_id,
                session.id,
                session.retrieval_mode,
                prior_history,
            )
            answer_text, agent_tool_traces = self._generate_answer(
                query=payload.message,
                user_id=payload.user_id,
                kb_id=session.kb_id,
                history=prior_history,
                memories=[memory.model_dump(mode="json") for memory in self.memory_service.list_memories(payload.user_id)],
                contexts=retrieval_result["final_context"],
                attachment_count=len(prepared.attachments),
                retrieval_mode=session.retrieval_mode,
                web_search_enabled=session.web_search_enabled,
            )
            retrieval_tool_trace = ToolTrace(
                name="rag_search",
                status="completed",
                input={
                    "query": payload.message,
                    "kb_id": session.kb_id,
                    "retrieval_mode": session.retrieval_mode,
                    "web_search_enabled": session.web_search_enabled,
                    "attachment_ids": payload.attachment_ids,
                },
                output={
                    "top_k": current_app.config.get("DEFAULT_TOP_K", 8),
                    "recall_top_k": retrieval_result.get("recall_top_k", current_app.config.get("RECALL_TOP_K", 40)),
                    "rerank_top_k": retrieval_result.get("rerank_top_k", current_app.config.get("RERANK_TOP_K", 16)),
                    "strategy": f"{session.retrieval_mode}+rerank",
                    "vector_hits": len(retrieval_result["vector_hits"]),
                    "bm25_hits": len(retrieval_result["bm25_hits"]),
                    "diverse_contexts": len(retrieval_result.get("diverse_hits", [])),
                    "final_context": len(retrieval_result["final_context"]),
                    "retrieved_context_tokens": retrieval_result["prompt_budget"].get("retrieved_context", 0),
                    "web_search": "not_implemented" if session.web_search_enabled else "disabled",
                },
            )
            tool_traces = [retrieval_tool_trace, *agent_tool_traces]
            citations = self._build_citations(retrieval_result["final_context"])

            for trace in tool_traces:
                yield self._to_sse(ChatStreamEnvelope(event="tool_call", data=trace.model_dump(mode="json")))

            for token in self._chunk_text(answer_text):
                yield self._to_sse(ChatStreamEnvelope(event="token", data={"text": token}))

            if payload.debug and session.kb_id:
                debug_payload = self.retrieval_service.build_debug_response(
                    payload.message,
                    retrieval_result,
                )
                yield self._to_sse(ChatStreamEnvelope(event="retrieval_debug", data=debug_payload.model_dump(mode="json")))

            assistant_message = Message(
                session_id=session.id,
                user_id=payload.user_id,
                role="assistant",
                content=answer_text,
                citations=[citation.model_dump(mode="json") for citation in citations],
                tool_trace=[tool_trace.model_dump(mode="json") for tool_trace in tool_traces],
            )
            assistant_message = self.message_repo.add(assistant_message)
            self.session_service.touch_after_assistant_message(
                session,
                answer_text,
                assistant_message.created_at or datetime.utcnow(),
            )

            final_answer = ChatAnswer(
                session_id=session.id,
                answer=answer_text,
                citations=citations,
                tool_trace=tool_traces,
            )
            yield self._to_sse(ChatStreamEnvelope(event="final_answer", data=final_answer.model_dump(mode="json")))
        except APIError as exc:
            yield self._to_sse(
                ChatStreamEnvelope(
                    event="error",
                    data={"error": exc.error, "code": exc.code, "details": exc.details},
                )
            )
        except Exception as exc:
            yield self._to_sse(
                ChatStreamEnvelope(
                    event="error",
                    data={"error": "chat stream failed", "code": "stream_error", "details": {"reason": str(exc)}},
                )
            )

    @staticmethod
    def _to_sse(event: ChatStreamEnvelope) -> str:
        return f"event: {event.event}\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"

    @staticmethod
    def _chunk_text(text: str, size: int = 14) -> list[str]:
        return [text[index : index + size] for index in range(0, len(text), size)]

    def _retrieve_context(
        self,
        payload: ChatRequest,
        kb_id: str | None,
        session_id: str,
        retrieval_mode: str,
        history_messages: list[Message],
    ) -> dict:
        if not kb_id:
            return {
                "vector_hits": [],
                "bm25_hits": [],
                "rrf_hits": [],
                "rerank_hits": [],
                "diverse_hits": [],
                "final_context": [],
                "context_plan": {"system_prompt": "You are ContextPilot.", "history": [], "memories": [], "retrieved_context": [], "query": payload.message, "token_budget": current_app.config.get("CONTEXT_TOKEN_BUDGET", 2400), "token_usage": {"history": 0, "memory": 0, "retrieved_context": 0, "remaining": current_app.config.get("CONTEXT_TOKEN_BUDGET", 2400)}},
                "prompt_budget": {
                    "system": 600,
                    "history": 0,
                    "memory": 0,
                    "retrieved_context": 0,
                    "user_query": 0,
                    "retrieved_context_budget": current_app.config.get("CONTEXT_TOKEN_BUDGET", 2400),
                },
            }

        return self.retrieval_service.search(
            user_id=payload.user_id,
            kb_id=kb_id,
            query=payload.message,
            session_id=session_id,
            retrieval_mode=retrieval_mode,
            top_k=current_app.config.get("DEFAULT_TOP_K", 8),
            history=[{"role": message.role, "content": message.content} for message in history_messages],
            memories=[memory.model_dump(mode="json") for memory in self.memory_service.list_memories(payload.user_id)],
        )

    def _generate_answer(
        self,
        *,
        query: str,
        user_id: str,
        kb_id: str | None,
        history: list[Message],
        memories: list[dict],
        contexts: list[dict],
        attachment_count: int,
        retrieval_mode: str,
        web_search_enabled: bool,
    ) -> tuple[str, list[ToolTrace]]:
        if is_agent_enabled(current_app.config):
            try:
                runner = AgentRunner(current_app.config)
                agent_result = runner.invoke(
                    {
                        "query": query,
                        "user_id": user_id,
                        "kb_id": kb_id,
                        "history": [{"role": message.role, "content": message.content} for message in history],
                        "memories": memories,
                        "retrieved_context": contexts,
                        "retrieval_mode": retrieval_mode,
                        "web_search_enabled": web_search_enabled,
                    }
                )
                answer_text = str(agent_result.get("answer", "")).strip()
                if answer_text:
                    if attachment_count:
                        answer_text += (
                            f" {attachment_count} chat attachment(s) were received for this session. "
                            "They are stored and associated with the message, but they are not indexed into the knowledge base yet."
                        )
                    traces = [
                        ToolTrace(
                            name=str(item.get("name", "tool")),
                            status=item.get("status", "completed"),
                            input=dict(item.get("input", {})),
                            output=dict(item.get("output", {})),
                        )
                        for item in agent_result.get("tool_trace", [])
                    ]
                    return answer_text, traces
            except Exception:
                pass

        return self._build_fallback_answer(query=query, contexts=contexts, attachment_count=attachment_count), []

    def _build_fallback_answer(self, *, query: str, contexts: list[dict], attachment_count: int) -> str:
        if not contexts:
            answer = (
                "I could not find grounded evidence for this question in the selected knowledge base yet. "
                "Try uploading a more relevant document or switching to a different knowledge base."
            )
        else:
            lead_files = ", ".join(dict.fromkeys(context["file_name"] for context in contexts[:3]))
            evidence_lines = [self._render_context_line(query, item) for item in contexts[:3]]
            answer = (
                f"Based on the retrieved documents ({lead_files}), the strongest evidence is: "
                + " ".join(line for line in evidence_lines if line)
            ).strip()

        if attachment_count:
            answer += (
                f" {attachment_count} chat attachment(s) were received for this session. "
                "They are stored and associated with the message, but they are not indexed into the knowledge base yet."
            )
        return answer

    @staticmethod
    def _render_context_line(query: str, context: dict[str, Any]) -> str:
        content = " ".join(str(context.get("content", "")).split())
        if not content:
            return ""

        sentences = [sentence.strip() for sentence in content.replace("\n", " ").split(".") if sentence.strip()]
        query_terms = {term.lower() for term in query.split() if term.strip()}
        for sentence in sentences:
            lowered = sentence.lower()
            if any(term in lowered for term in query_terms):
                return sentence[:220] + ("" if sentence.endswith(".") else ".")

        snippet = content[:220]
        return snippet + ("" if snippet.endswith(".") else ".")

    @staticmethod
    def _build_citations(contexts: list[dict]) -> list[Citation]:
        citations: list[Citation] = []
        for item in contexts[:3]:
            metadata = item.get("metadata", {})
            locators = metadata.get("source_locators", {})
            page = locators.get("page_number")
            if isinstance(page, list):
                page = page[0] if page else None
            citations.append(
                Citation(
                    document_id=str(item["document_id"]),
                    file_name=str(item["file_name"]),
                    page=page if isinstance(page, int) else None,
                    chunk_id=str(item["chunk_id"]),
                    rerank_score=float(item.get("score", 0.0)),
                )
            )
        return citations
