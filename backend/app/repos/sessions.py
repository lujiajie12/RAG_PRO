from __future__ import annotations

from sqlalchemy import or_

from ..extensions import db
from ..models.orm import ConversationSession, Message, SessionTag


class SessionRepository:
    # Insert one session row and commit it immediately.
    def create(self, session: ConversationSession) -> ConversationSession:
        db.session.add(session)
        db.session.commit()
        return session

    # Query sessions for a user with optional text / kb / tag filters and pagination.
    def list_by_filters(
        self,
        user_id: str,
        q: str | None = None,
        kb_id: str | None = None,
        tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationSession]:
        query = ConversationSession.query.filter(ConversationSession.user_id == user_id)

        if q or tag:
            query = query.outerjoin(SessionTag, ConversationSession.id == SessionTag.session_id)

        if kb_id:
            query = query.filter(ConversationSession.kb_id == kb_id)

        if tag:
            query = query.filter(SessionTag.tag == tag)

        if q:
            pattern = f"%{q}%"
            query = query.filter(
                or_(
                    ConversationSession.id.ilike(pattern),
                    ConversationSession.title.ilike(pattern),
                    ConversationSession.summary.ilike(pattern),
                    ConversationSession.kb_id.ilike(pattern),
                    SessionTag.tag.ilike(pattern),
                )
            )

        return (
            query.distinct()
            .order_by(ConversationSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    # Query one session by primary key and user. Returns None when missing.
    def get_by_user(self, user_id: str, session_id: str) -> ConversationSession | None:
        return ConversationSession.query.filter_by(id=session_id, user_id=user_id).first()

    # Commit updates on an existing session row.
    def update(self, session: ConversationSession) -> ConversationSession:
        db.session.add(session)
        db.session.commit()
        return session


class MessageRepository:
    # Insert one message row and commit it immediately.
    def add(self, message: Message) -> Message:
        db.session.add(message)
        db.session.commit()
        return message

    # Query all messages in a session, ordered from oldest to newest.
    def list_by_session(self, session_id: str) -> list[Message]:
        return Message.query.filter_by(session_id=session_id).order_by(Message.created_at.asc()).all()
