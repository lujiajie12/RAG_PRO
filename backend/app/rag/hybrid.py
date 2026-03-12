from __future__ import annotations


class HybridRetriever:
    def retrieve(self, query: str, kb_id: str, top_k: int = 20) -> dict:
        return {"query": query, "kb_id": kb_id, "top_k": top_k, "strategy": "rrf"}
