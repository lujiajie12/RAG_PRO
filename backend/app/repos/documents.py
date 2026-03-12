from __future__ import annotations

from ..extensions import db
from ..models.orm import Document, DocumentChunk


class DocumentRepository:
    def create(self, document: Document) -> Document:
        db.session.add(document)
        db.session.commit()
        return document

    def list_by_kb(self, user_id: str, kb_id: str) -> list[Document]:
        return (
            Document.query.filter_by(user_id=user_id, kb_id=kb_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    def get(self, document_id: str) -> Document | None:
        return Document.query.get(document_id)

    def delete(self, document: Document) -> None:
        db.session.delete(document)
        db.session.commit()

    def count_chunks(self, document_id: str) -> int:
        return DocumentChunk.query.filter_by(document_id=document_id).count()
