from __future__ import annotations


class LongTermMemoryStore:
    def save(self, payload: dict) -> dict:
        return {"status": "saved", **payload}
