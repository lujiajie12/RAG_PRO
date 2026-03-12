from __future__ import annotations

from ..models.orm import ConversationSession
from ..models.schemas import CreateSessionRequest, SessionSummary
from ..repos.sessions import SessionRepository


class SessionService:
    def __init__(self, repo: SessionRepository | None = None) -> None:
        self.repo = repo or SessionRepository()

    def list_sessions(self, user_id: str) -> list[SessionSummary]:
        sessions = self.repo.list_by_user(user_id)
        return [SessionSummary.model_validate(session) for session in sessions]

    def create_session(self, payload: CreateSessionRequest) -> SessionSummary:
        session = ConversationSession(
            user_id=payload.user_id,
            kb_id=payload.kb_id,
            title=payload.title or "New conversation",
            thread_id=f"{payload.user_id}:{payload.kb_id or 'general'}",
        )
        return SessionSummary.model_validate(self.repo.create(session))
