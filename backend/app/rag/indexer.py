from __future__ import annotations

from flask import current_app

from ..models.orm import Document, DocumentChunk, new_id
from ..repos.documents import DocumentRepository
from .embeddings import embed_text


class KnowledgeIndexer:
    def __init__(self, repo: DocumentRepository | None = None) -> None:
        self.repo = repo or DocumentRepository()

    def build_indexes(self, document: Document, chunks: dict[str, list[dict]]) -> dict:
        parent_chunks, parent_id_map = self._build_parent_chunks(document, chunks.get("parents", []))
        child_chunks = self._build_child_chunks(document, chunks.get("children", []), parent_id_map)
        stored_chunks = self.repo.replace_chunks(document.id, parent_chunks + child_chunks)
        return {
            "document_id": document.id,
            "vector": "ready",
            "bm25": "ready",
            "stored_chunks": len(stored_chunks),
            "parent_chunks": len(parent_chunks),
            "child_chunks": len(child_chunks),
        }

    def _build_parent_chunks(
        self,
        document: Document,
        chunk_payloads: list[dict],
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        chunks: list[DocumentChunk] = []
        temp_to_persisted: dict[str, str] = {}
        for payload in chunk_payloads:
            chunk_id = new_id()
            temp_to_persisted[str(payload["id"])] = chunk_id
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=document.id,
                    user_id=document.user_id,
                    kb_id=document.kb_id,
                    parent_id=None,
                    chunk_type="parent",
                    content=str(payload["content"]),
                    token_count=int(payload["metadata"].get("token_count", 0)),
                    metadata_json=self._metadata_payload(document, payload["metadata"]),
                    embedding=embed_text(str(payload["content"])),
                )
            )
        return chunks, temp_to_persisted

    def _build_child_chunks(
        self,
        document: Document,
        chunk_payloads: list[dict],
        parent_id_map: dict[str, str],
    ) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for payload in chunk_payloads:
            parent_id = parent_id_map.get(str(payload.get("parent_id")))
            chunks.append(
                DocumentChunk(
                    document_id=document.id,
                    user_id=document.user_id,
                    kb_id=document.kb_id,
                    parent_id=parent_id,
                    chunk_type="child",
                    content=str(payload["content"]),
                    token_count=int(payload["metadata"].get("token_count", 0)),
                    metadata_json=self._metadata_payload(document, payload["metadata"]),
                    embedding=embed_text(str(payload["content"])),
                )
            )
        return chunks

    @staticmethod
    def _metadata_payload(document: Document, metadata: dict) -> dict:
        payload = dict(metadata)
        payload["document_id"] = document.id
        payload["file_name"] = document.file_name
        payload["file_type"] = document.file_type
        payload["kb_id"] = document.kb_id
        payload["user_id"] = document.user_id
        payload["embedding_model"] = current_app.config.get("EMBEDDING_MODEL", "local-hash-v1")
        payload["embedding_backend"] = "local-hash-v1"
        return payload
