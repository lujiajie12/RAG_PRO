from __future__ import annotations

from pathlib import Path


class ParserRegistry:
    def resolve(self, file_name: str) -> str:
        return Path(file_name).suffix.lower().lstrip(".") or "unknown"
