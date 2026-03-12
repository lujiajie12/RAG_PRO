from __future__ import annotations

from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models.orm import Document, DocumentChunk


class DocumentRepository:
    # Insert one document row and commit it immediately.
    def create(self, document: Document) -> Document:
        db.session.add(document)
        db.session.commit()
        return document

    # Query all documents under one user's knowledge base.
    def list_by_kb(self, user_id: str, kb_id: str) -> list[Document]:
        return (
            Document.query.filter_by(user_id=user_id, kb_id=kb_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    # Query one document by its primary key. Returns None when missing.
    def get(self, document_id: str) -> Document | None:
        return db.session.get(Document, document_id)

    # Query one document with all chunk rows eagerly loaded.
    def get_with_chunks(self, document_id: str) -> Document | None:
        return (
            Document.query.options(joinedload(Document.chunks))
            .filter(Document.id == document_id)
            .first()
        )

    # Commit updates on an existing document row.
    def update(self, document: Document) -> Document:
        db.session.add(document)
        db.session.commit()
        return document

    # Delete one document row and commit the change immediately.
    def delete(self, document: Document) -> None:
        db.session.delete(document)
        db.session.commit()

    # Count how many chunk rows belong to a document.
    def count_chunks(self, document_id: str) -> int:
        return DocumentChunk.query.filter_by(document_id=document_id).count()

    # Replace all stored chunks for one document in a single transaction.
    def replace_chunks(self, document_id: str, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        DocumentChunk.query.filter_by(document_id=document_id).delete(synchronize_session=False)
        if chunks:
            db.session.add_all(chunks)
        db.session.commit()
        return chunks

    # Query child or parent chunks for one user and one knowledge base.
    def list_chunks_by_kb(self, user_id: str, kb_id: str, chunk_type: str = "child") -> list[DocumentChunk]:
        return (
            DocumentChunk.query.options(joinedload(DocumentChunk.document))
            .filter_by(user_id=user_id, kb_id=kb_id, chunk_type=chunk_type)
            .order_by(DocumentChunk.created_at.asc())
            .all()
        )

    # Query a set of chunks by their ids, eagerly loading the parent document.
    def list_chunks_by_ids(self, chunk_ids: list[str]) -> list[DocumentChunk]:
        if not chunk_ids:
            return []
        return (
            DocumentChunk.query.options(joinedload(DocumentChunk.document))
            .filter(DocumentChunk.id.in_(chunk_ids))
            .all()
        )
