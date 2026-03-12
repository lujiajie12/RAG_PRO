from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path

from ..types import ParsedDocument, ParsedSegment


class BaseLoader(ABC):
    def load(self, file_path: str | Path) -> str:
        path = Path(file_path)
        return self.load_bytes(path.read_bytes(), path.name)

    def load_bytes(self, data: bytes, file_name: str) -> str:
        parsed = self.parse_bytes(data, file_name)
        return self.render_text(parsed)

    @abstractmethod
    def parse_bytes(self, data: bytes, file_name: str) -> ParsedDocument:
        """Return structured segments extracted from a file."""

    @staticmethod
    def decode_text(data: bytes) -> str:
        for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="ignore")

    @staticmethod
    def normalize_lines(lines: Iterable[str]) -> str:
        normalized: list[str] = []
        for line in lines:
            collapsed = " ".join(str(line).split())
            if collapsed:
                normalized.append(collapsed)
        return "\n".join(normalized)

    @staticmethod
    def make_segment(kind: str, text: str, *, raw_text: str | None = None, **metadata: object) -> ParsedSegment:
        return ParsedSegment(kind=kind, text=text, raw_text=raw_text if raw_text is not None else text, metadata=dict(metadata))

    @staticmethod
    def render_text(parsed: ParsedDocument) -> str:
        rendered: list[str] = []
        for segment in parsed.segments:
            text = " ".join(segment.text.split())
            if text:
                rendered.append(text)
        return "\n".join(rendered)
