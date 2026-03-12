from __future__ import annotations

from pathlib import Path


class DocumentLoaderFactory:
    """Route local files to the correct parser implementation."""

    def get_loader(self, file_path: str) -> dict:
        suffix = Path(file_path).suffix.lower()
        return {"path": file_path, "loader": suffix or "unknown"}
