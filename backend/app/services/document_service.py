from __future__ import annotations

from uuid import uuid4

from werkzeug.datastructures import FileStorage

from ..models.orm import Document
from ..models.schemas import DocumentSummary, DocumentUploadResponse
from ..repos.documents import DocumentRepository


class DocumentService:
    def __init__(self, repo: DocumentRepository | None = None) -> None:
        self.repo = repo or DocumentRepository()

    def list_documents(self, user_id: str, kb_id: str) -> list[DocumentSummary]:
        return [DocumentSummary.model_validate(item) for item in self.repo.list_by_kb(user_id, kb_id)]

    def upload_document(self, user_id: str, kb_id: str, file: FileStorage) -> DocumentUploadResponse:
        file_type = (file.filename or "unknown").split(".")[-1].lower()
        document = Document(
            user_id=user_id,
            kb_id=kb_id,
            file_name=file.filename or "untitled",
            file_type=file_type,
            storage_key=f"{kb_id}/{uuid4().hex}-{file.filename or 'untitled'}",
            status="uploaded",
            parsed_type=file_type,
        )
        saved = self.repo.create(document)
        return DocumentUploadResponse(
            document_id=saved.id,
            kb_id=kb_id,
            status=saved.status,
            parsed_type=saved.parsed_type,
        )

    def delete_document(self, document_id: str) -> bool:
        document = self.repo.get(document_id)
        if document is None:
            return False
        self.repo.delete(document)
        return True
