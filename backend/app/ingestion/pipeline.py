from __future__ import annotations


class IngestionPipeline:
    def run(self, document_id: str) -> dict:
        return {"document_id": document_id, "status": "queued"}
