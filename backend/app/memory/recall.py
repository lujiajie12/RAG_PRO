from __future__ import annotations


class MemoryRecallService:
    def search(self, query: str, user_id: str) -> list[dict]:
        return [{"summary": "User prefers conclusion first.", "query": query, "user_id": user_id}]
