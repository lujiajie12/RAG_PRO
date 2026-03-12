from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.datastructures import FileStorage

from ..errors import APIError
from ..ingestion.storage import ObjectStorage
from ..models.orm import ChatAttachment
from ..models.schemas import ChatAttachmentUploadResponse
from ..repos.chat_attachments import ChatAttachmentRepository
from .session_service import SessionService


SUPPORTED_CHAT_ATTACHMENT_TYPES = {"pdf", "docx", "md", "txt", "html", "csv", "pptx", "png", "jpg", "jpeg", "webp"}


class ChatAttachmentService:
    def __init__(
        self,
        repo: ChatAttachmentRepository | None = None,
        session_service: SessionService | None = None,
        storage: ObjectStorage | None = None,
    ) -> None:
        self.repo = repo or ChatAttachmentRepository()
        self.session_service = session_service or SessionService()
        self.storage = storage

    def upload_attachment(self, user_id: str, session_id: str, file: FileStorage) -> ChatAttachmentUploadResponse:
        session = self.session_service.get_session_entity(user_id, session_id)

        file_name = Path(file.filename or "untitled").name
        file_type = Path(file_name).suffix.lower().lstrip(".")
        if file_type not in SUPPORTED_CHAT_ATTACHMENT_TYPES:
            raise APIError(
                "unsupported file type",
                "validation_error",
                400,
                {"allowed_types": sorted(SUPPORTED_CHAT_ATTACHMENT_TYPES), "file_type": file_type or "unknown"},
            )

        file_bytes = file.read()
        storage_key = f"chat_attachments/{session.id}/{uuid4().hex}-{file_name}"
        storage = self.storage or self._build_storage()

        attachment = ChatAttachment(
            user_id=user_id,
            session_id=session.id,
            file_name=file_name,
            file_type=file_type,
            mime_type=file.mimetype or "application/octet-stream",
            size_bytes=len(file_bytes),
            storage_key=storage_key,
            status="uploaded",
        )
        saved = self.repo.create(attachment)

        try:
            storage.upload_bytes(
                current_app.config["MINIO_BUCKET"],
                storage_key,
                file_bytes,
                content_type=attachment.mime_type,
            )
        except Exception as exc:
            self.repo.delete(saved)
            raise APIError("failed to store attachment", "storage_error", 502, {"reason": str(exc)}) from exc

        return ChatAttachmentUploadResponse(
            attachment_id=saved.id,
            session_id=session.id,
            file_name=saved.file_name,
            file_type=saved.file_type,
            mime_type=saved.mime_type,
            size_bytes=saved.size_bytes,
            status=saved.status,
        )

    @staticmethod
    def _build_storage() -> ObjectStorage:
        return ObjectStorage(
            endpoint=current_app.config["MINIO_ENDPOINT"],
            access_key=current_app.config["MINIO_ACCESS_KEY"],
            secret_key=current_app.config["MINIO_SECRET_KEY"],
            secure=current_app.config["MINIO_SECURE"],
        )
