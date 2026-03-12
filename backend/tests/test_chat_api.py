from __future__ import annotations

from uuid import uuid4

from app.extensions import db
from app.models.orm import ChatAttachment, ConversationSession, Document, DocumentChunk, Message
from app.rag.embeddings import embed_text
from app.services import chat_service as chat_service_module


def _seed_session(user_id: str, *, kb_id: str | None = "kb-chat") -> ConversationSession:
    session = ConversationSession(
        user_id=user_id,
        kb_id=kb_id,
        title="Chat session",
        summary=None,
        thread_id=f"thread-{uuid4().hex}",
        model_name="qwen-plus",
        retrieval_mode="hybrid",
        web_search_enabled=True,
    )
    db.session.add(session)
    db.session.commit()
    return session


def _seed_indexed_document(user_id: str, kb_id: str) -> None:
    document = Document(
        user_id=user_id,
        kb_id=kb_id,
        file_name="retrieval-notes.txt",
        file_type="txt",
        storage_key=f"documents/{kb_id}/retrieval-notes.txt",
        status="indexed",
        parsed_type="text",
        chunk_count=1,
    )
    db.session.add(document)
    db.session.flush()

    parent_content = (
        "Parent document retrieval fetches a small matching child chunk first and then restores the broader "
        "parent context so the answer keeps more structure and supporting detail."
    )
    parent_chunk = DocumentChunk(
        document_id=document.id,
        user_id=user_id,
        kb_id=kb_id,
        chunk_type="parent",
        content=parent_content,
        token_count=32,
        metadata_json={
            "file_name": document.file_name,
            "source_locators": {"page_number": 1},
            "document_title": "Retrieval Notes",
        },
        embedding=embed_text(parent_content),
    )
    db.session.add(parent_chunk)
    db.session.flush()

    child_content = "Parent document retrieval restores the broader parent context around the matched child chunk."
    db.session.add(
        DocumentChunk(
            document_id=document.id,
            user_id=user_id,
            kb_id=kb_id,
            parent_id=parent_chunk.id,
            chunk_type="child",
            content=child_content,
            token_count=18,
            metadata_json={
                "file_name": document.file_name,
                "source_locators": {"page_number": 1},
                "document_title": "Retrieval Notes",
            },
            embedding=embed_text(child_content),
        )
    )
    db.session.commit()


def test_stream_chat_persists_messages_and_updates_session(client, app, test_user_id):
    with app.app_context():
        session = _seed_session(test_user_id)
        _seed_indexed_document(test_user_id, session.kb_id or "kb-chat")
        session_id = session.id

    response = client.post(
        "/api/chat/stream",
        json={
            "user_id": test_user_id,
            "session_id": session_id,
            "message": "What is parent document retrieval?",
            "debug": True,
        },
        buffered=True,
    )

    assert response.status_code == 200
    payload = response.get_data(as_text=True)
    assert "event: token" in payload
    assert "event: tool_call" in payload
    assert "event: retrieval_debug" in payload
    assert "event: final_answer" in payload

    with app.app_context():
        messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at.asc()).all()
        assert [message.role for message in messages] == ["user", "assistant"]
        assert messages[0].content == "What is parent document retrieval?"
        assert "broader parent context" in messages[1].content
        assert messages[1].citations
        assert messages[1].citations[0]["file_name"] == "retrieval-notes.txt"

        refreshed = db.session.get(ConversationSession, session_id)
        assert refreshed is not None
        assert refreshed.summary
        assert refreshed.last_message_at is not None


def test_stream_chat_rejects_attachment_from_other_session(client, app, test_user_id):
    with app.app_context():
        target_session = _seed_session(test_user_id)
        foreign_session = _seed_session(test_user_id)
        attachment = ChatAttachment(
            user_id=test_user_id,
            session_id=foreign_session.id,
            file_name="draft.md",
            file_type="md",
            mime_type="text/markdown",
            size_bytes=12,
            storage_key=f"chat_attachments/{foreign_session.id}/draft.md",
            status="uploaded",
        )
        db.session.add(attachment)
        db.session.commit()
        target_session_id = target_session.id
        attachment_id = attachment.id

    response = client.post(
        "/api/chat/stream",
        json={
            "user_id": test_user_id,
            "session_id": target_session_id,
            "message": "Use my attachment",
            "attachment_ids": [attachment_id],
        },
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["code"] == "validation_error"
    assert "attachments" in payload["error"]


def test_stream_chat_uses_agent_answer_when_enabled(client, app, monkeypatch, test_user_id):
    class FakeAgentRunner:
        def __init__(self, _: dict) -> None:
            pass

        def invoke(self, payload: dict) -> dict:
            assert payload["retrieved_context"]
            return {
                "answer": "Agent says hybrid retrieval combines dense and sparse recall before reranking.",
                "tool_trace": [
                    {
                        "name": "list_documents",
                        "status": "completed",
                        "input": {"kb_id": payload["kb_id"], "user_id": payload["user_id"]},
                        "output": {"documents": [{"file_name": "retrieval-notes.txt"}]},
                    }
                ],
            }

    monkeypatch.setattr(chat_service_module, "is_agent_enabled", lambda _: True)
    monkeypatch.setattr(chat_service_module, "AgentRunner", FakeAgentRunner)

    with app.app_context():
        session = _seed_session(test_user_id)
        _seed_indexed_document(test_user_id, session.kb_id or "kb-chat")
        session_id = session.id

    response = client.post(
        "/api/chat/stream",
        json={
            "user_id": test_user_id,
            "session_id": session_id,
            "message": "Explain hybrid retrieval.",
        },
        buffered=True,
    )

    assert response.status_code == 200
    payload = response.get_data(as_text=True)
    assert "Agent says hybrid retrieval" in payload
    assert '"name": "list_documents"' in payload
