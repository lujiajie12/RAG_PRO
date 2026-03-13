from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.datastructures import FileStorage

from ..errors import APIError
from ..ingestion.parsers import ParserRegistry
from ..ingestion.pipeline import IngestionPipeline
from ..ingestion.storage import ObjectStorage
from ..models.orm import Document
from ..models.schemas import DocumentSummary, DocumentUploadResponse
from ..repos.documents import DocumentRepository


SUPPORTED_DOCUMENT_TYPES = {"pdf", "docx", "md", "txt", "html", "csv", "pptx"}


class DocumentService:
    def __init__(
        self,
        repo: DocumentRepository | None = None,
        parser_registry: ParserRegistry | None = None,
        pipeline: IngestionPipeline | None = None,
        storage: ObjectStorage | None = None,
    ) -> None:
        self.repo = repo or DocumentRepository()
        self.parser_registry = parser_registry or ParserRegistry()
        self.pipeline = pipeline
        self.storage = storage

    def list_documents(self, user_id: str, kb_id: str) -> list[DocumentSummary]:
        return [self._to_summary(item) for item in self.repo.list_by_kb(user_id, kb_id)]

    def upload_document(self, user_id: str, kb_id: str, file: FileStorage) -> DocumentUploadResponse:
        file_name = Path(file.filename or "untitled").name
        file_type = Path(file_name).suffix.lower().lstrip(".")
        if file_type not in SUPPORTED_DOCUMENT_TYPES:
            raise APIError(
                "unsupported file type",
                "validation_error",
                400,
                {"allowed_types": sorted(SUPPORTED_DOCUMENT_TYPES), "file_type": file_type or "unknown"},
            )

        file_bytes = file.read()
        storage_key = f"documents/{kb_id}/{uuid4().hex}-{file_name}"
        storage = self.storage or self._build_storage()

        document = Document(
            user_id=user_id,
            kb_id=kb_id,
            file_name=file_name,
            file_type=file_type,
            storage_key=storage_key,
            status="uploaded",
            parsed_type=self.parser_registry.resolve(file_name),
        )
        saved = self.repo.create(document)

        try:
            storage.upload_bytes(
                current_app.config["MINIO_BUCKET"],
                storage_key,
                file_bytes,
                content_type=file.mimetype or "application/octet-stream",
            )
        except Exception as exc:
            self.repo.delete(saved)
            raise APIError("failed to store document", "storage_error", 502, {"reason": str(exc)}) from exc

        pipeline = self.pipeline or IngestionPipeline(storage=storage)
        result = pipeline.run(saved.id)

        return DocumentUploadResponse(
            document_id=saved.id,
            kb_id=kb_id,
            status=result["status"],
            parsed_type=result["parsed_type"],
            file_name=saved.file_name,
            file_type=saved.file_type,
        )

    def delete_document(self, document_id: str) -> bool:
        document = self.repo.get(document_id)
        if document is None:
            return False
        try:
            (self.storage or self._build_storage()).delete_object(current_app.config["MINIO_BUCKET"], document.storage_key)
        except Exception:
            pass
        self.repo.delete(document)
        return True

    @staticmethod
    def _to_summary(document: Document) -> DocumentSummary:
        metadata = dict(document.metadata_json or {})
        indexing = dict(metadata.get("indexing") or {})
        return DocumentSummary(
            id=document.id,
            user_id=document.user_id,
            kb_id=document.kb_id,
            file_name=document.file_name,
            file_type=document.file_type,
            status=document.status,
            parsed_type=document.parsed_type,
            chunk_count=document.chunk_count,
            parent_count=int(metadata.get("parent_chunk_count") or indexing.get("parent_chunks") or 0),
            child_count=int(metadata.get("child_chunk_count") or indexing.get("child_chunks") or document.chunk_count or 0),
            indexed_at=document.updated_at if document.status == "indexed" else None,
            embedding_status=str(indexing.get("vector") or "pending"),
            bm25_status=str(indexing.get("bm25") or "pending"),
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def _build_storage() -> ObjectStorage:
        return ObjectStorage(
            endpoint=current_app.config["MINIO_ENDPOINT"],
            access_key=current_app.config["MINIO_ACCESS_KEY"],
            secret_key=current_app.config["MINIO_SECRET_KEY"],
            secure=current_app.config["MINIO_SECURE"],
        )
