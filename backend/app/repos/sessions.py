from __future__ import annotations

from ..extensions import db
from ..models.orm import ConversationSession, Message


class SessionRepository:
    def create(self, session: ConversationSession) -> ConversationSession:
        db.session.add(session)
        db.session.commit()
        return session

    def list_by_user(self, user_id: str) -> list[ConversationSession]:
        return (
            ConversationSession.query.filter_by(user_id=user_id)
            .order_by(ConversationSession.updated_at.desc())
            .all()
        )

    def get(self, session_id: str) -> ConversationSession | None:
        return ConversationSession.query.get(session_id)


class MessageRepository:
    def add(self, message: Message) -> Message:
        db.session.add(message)
        db.session.commit()
        return message

    def list_by_session(self, session_id: str) -> list[Message]:
        return Message.query.filter_by(session_id=session_id).order_by(Message.created_at.asc()).all()
