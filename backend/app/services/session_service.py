from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from flask import current_app

from ..errors import APIError
from ..models.orm import ConversationSession, Message, SessionTag
from ..models.schemas import CreateSessionRequest, MessageRecord, SessionRecord, UpdateSessionRequest
from ..repos.sessions import MessageRepository, SessionRepository


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    for tag in tags:
        clean = tag.strip().lower()
        if clean and clean not in normalized:
            normalized.append(clean)
    return normalized


def _summarize(text: str) -> str:
    return " ".join(text.split())[:120]


class SessionService:
    def __init__(
        self,
        repo: SessionRepository | None = None,
        message_repo: MessageRepository | None = None,
    ) -> None:
        self.repo = repo or SessionRepository()
        self.message_repo = message_repo or MessageRepository()

    def list_sessions(
        self,
        user_id: str,
        q: str | None = None,
        kb_id: str | None = None,
        tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SessionRecord]:
        sessions = self.repo.list_by_filters(
            user_id=user_id,
            q=(q or "").strip() or None,
            kb_id=(kb_id or "").strip() or None,
            tag=((tag or "").strip().lower() or None),
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
        )
        return [self._to_record(session) for session in sessions]

    def get_session(self, user_id: str, session_id: str) -> SessionRecord:
        session = self.get_session_entity(user_id, session_id)
        return self._to_record(session)

    def get_session_entity(self, user_id: str, session_id: str) -> ConversationSession:
        session = self.repo.get_by_user(user_id, session_id)
        if session is None:
            raise APIError("session not found", "resource_not_found", 404)
        return session

    def create_session(self, payload: CreateSessionRequest) -> SessionRecord:
        session = ConversationSession(
            user_id=payload.user_id,
            kb_id=payload.kb_id,
            title=(payload.title or "New conversation").strip() or "New conversation",
            summary=None,
            thread_id=f"thread-{uuid4().hex}",
            model_name=payload.model_name or current_app.config["CHAT_MODEL"],
            retrieval_mode=payload.retrieval_mode or "hybrid",
            web_search_enabled=payload.web_search_enabled,
        )
        session.tags = [SessionTag(tag=tag) for tag in _normalize_tags(payload.tags)]
        return self._to_record(self.repo.create(session))

    def update_session(self, session_id: str, payload: UpdateSessionRequest) -> SessionRecord:
        session = self.get_session_entity(payload.user_id, session_id)
        fields = payload.model_fields_set

        if "title" in fields:
            if payload.title is None or not payload.title.strip():
                raise APIError("title cannot be empty", "validation_error", 400)
            session.title = payload.title.strip()
        if "kb_id" in fields:
            session.kb_id = payload.kb_id
        if "tags" in fields:
            session.tags = [SessionTag(tag=tag) for tag in _normalize_tags(payload.tags or [])]
        if "model_name" in fields:
            if payload.model_name is None or not payload.model_name.strip():
                raise APIError("model_name cannot be empty", "validation_error", 400)
            session.model_name = payload.model_name.strip()
        if "retrieval_mode" in fields and payload.retrieval_mode is not None:
            session.retrieval_mode = payload.retrieval_mode
        if "web_search_enabled" in fields and payload.web_search_enabled is not None:
            session.web_search_enabled = payload.web_search_enabled

        return self._to_record(self.repo.update(session))

    def list_messages(self, user_id: str, session_id: str) -> list[MessageRecord]:
        session = self.get_session_entity(user_id, session_id)
        messages = self.message_repo.list_by_session(session.id)
        return [self._to_message_record(message) for message in messages]

    def touch_after_user_message(self, session: ConversationSession, user_text: str, when: datetime) -> ConversationSession:
        session.summary = _summarize(user_text)
        session.last_message_at = when
        return self.repo.update(session)

    def touch_after_assistant_message(
        self,
        session: ConversationSession,
        assistant_text: str,
        when: datetime,
    ) -> ConversationSession:
        session.summary = _summarize(assistant_text)
        session.last_message_at = when
        return self.repo.update(session)

    @staticmethod
    def _to_record(session: ConversationSession) -> SessionRecord:
        return SessionRecord(
            id=session.id,
            user_id=session.user_id,
            kb_id=session.kb_id,
            title=session.title,
            summary=session.summary,
            thread_id=session.thread_id,
            tags=session.tag_names,
            model_name=session.model_name,
            retrieval_mode=session.retrieval_mode,
            web_search_enabled=session.web_search_enabled,
            last_message_at=session.last_message_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    @staticmethod
    def _to_message_record(message: Message) -> MessageRecord:
        return MessageRecord(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            citations=message.citations or [],
            tool_trace=message.tool_trace or [],
            created_at=message.created_at,
            updated_at=message.updated_at,
        )
