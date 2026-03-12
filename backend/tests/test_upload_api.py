from __future__ import annotations

from io import BytesIO
from uuid import uuid4

from app.extensions import db
from app.models.orm import ConversationSession, Document, DocumentChunk
from app.services.chat_attachment_service import ChatAttachmentService
from app.services.document_service import DocumentService


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def ensure_bucket(self, bucket_name: str) -> None:
        return None

    def upload_bytes(self, bucket_name: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self.objects[(bucket_name, object_name)] = data

    def download_bytes(self, bucket_name: str, object_name: str) -> bytes:
        return self.objects[(bucket_name, object_name)]

    def delete_object(self, bucket_name: str, object_name: str) -> None:
        self.objects.pop((bucket_name, object_name), None)


def _seed_session(user_id: str) -> ConversationSession:
    session = ConversationSession(
        user_id=user_id,
        kb_id="kb-upload",
        title="Attachment session",
        summary=None,
        thread_id=f"thread-{uuid4().hex}",
        model_name="qwen-plus",
        retrieval_mode="hybrid",
        web_search_enabled=False,
    )
    db.session.add(session)
    db.session.commit()
    return session


def test_upload_document_accepts_supported_type(client, app, monkeypatch, test_user_id):
    storage = FakeStorage()
    monkeypatch.setattr(DocumentService, "_build_storage", staticmethod(lambda: storage))

    response = client.post(
        "/api/upload",
        data={
            "user_id": test_user_id,
            "kb_id": "kb-docs",
            "file": (BytesIO(b"hello knowledge base"), "notes.txt", "text/plain"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["kb_id"] == "kb-docs"
    assert payload["file_name"] == "notes.txt"
    assert payload["file_type"] == "txt"
    assert payload["parsed_type"] == "text"
    assert payload["status"] == "indexed"

    with app.app_context():
        document = db.session.get(Document, payload["document_id"])
        assert document is not None
        assert document.status == "indexed"
        assert document.chunk_count == 1
        stored_chunks = DocumentChunk.query.filter_by(document_id=document.id).all()
        assert len(stored_chunks) == 2
        assert {chunk.chunk_type for chunk in stored_chunks} == {"parent", "child"}


def test_upload_document_rejects_unsupported_type(client, test_user_id):
    response = client.post(
        "/api/upload",
        data={
            "user_id": test_user_id,
            "kb_id": "kb-docs",
            "file": (BytesIO(b"bad"), "archive.zip", "application/zip"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["code"] == "validation_error"
    assert payload["details"]["file_type"] == "zip"


def test_upload_chat_attachment_accepts_supported_type(client, app, monkeypatch, test_user_id):
    storage = FakeStorage()
    monkeypatch.setattr(ChatAttachmentService, "_build_storage", staticmethod(lambda: storage))

    with app.app_context():
        session = _seed_session(test_user_id)
        session_id = session.id

    response = client.post(
        "/api/chat/attachments",
        data={
            "user_id": test_user_id,
            "session_id": session_id,
            "file": (BytesIO(b"temporary note"), "draft.md", "text/markdown"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["session_id"] == session_id
    assert payload["file_name"] == "draft.md"
    assert payload["file_type"] == "md"
    assert payload["status"] == "uploaded"


def test_upload_chat_attachment_rejects_unsupported_type(client, app, test_user_id):
    with app.app_context():
        session = _seed_session(test_user_id)
        session_id = session.id

    response = client.post(
        "/api/chat/attachments",
        data={
            "user_id": test_user_id,
            "session_id": session_id,
            "file": (BytesIO(b"bad"), "archive.zip", "application/zip"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["code"] == "validation_error"
    assert payload["details"]["file_type"] == "zip"
