from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from app.extensions import db
from app.models.orm import ChatAttachment, ConversationSession, Document, DocumentChunk, Memory, Message, RetrievalLog, SessionTag, User


def _cleanup_user_data(user_id: str) -> None:
    session_ids = select(ConversationSession.id).where(ConversationSession.user_id == user_id)
    document_ids = select(Document.id).where(Document.user_id == user_id)

    db.session.execute(delete(ChatAttachment).where(ChatAttachment.user_id == user_id))
    db.session.execute(delete(Message).where(Message.user_id == user_id))
    db.session.execute(delete(SessionTag).where(SessionTag.session_id.in_(session_ids)))
    db.session.execute(delete(ConversationSession).where(ConversationSession.user_id == user_id))
    db.session.execute(delete(DocumentChunk).where(DocumentChunk.document_id.in_(document_ids)))
    db.session.execute(delete(Document).where(Document.user_id == user_id))
    db.session.execute(delete(Memory).where(Memory.user_id == user_id))
    db.session.execute(delete(RetrievalLog).where(RetrievalLog.user_id == user_id))
    db.session.execute(delete(User).where(User.external_user_id == user_id))
    db.session.commit()


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    yield app
    with app.app_context():
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def test_user_id(app):
    user_id = f"test-user-{uuid4().hex}"
    yield user_id
    with app.app_context():
        _cleanup_user_data(user_id)
