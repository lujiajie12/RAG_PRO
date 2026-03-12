from __future__ import annotations


class KnowledgeIndexer:
    def build_indexes(self, document_id: str) -> dict:
        return {"document_id": document_id, "vector": "pending", "bm25": "pending"}
