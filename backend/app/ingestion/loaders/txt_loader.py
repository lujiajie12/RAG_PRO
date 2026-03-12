from __future__ import annotations

from .base_loader import BaseLoader
from ..types import ParsedDocument


class TxtLoader(BaseLoader):
    def parse_bytes(self, data: bytes, file_name: str) -> ParsedDocument:
        lines = self.normalize_lines(self.decode_text(data).splitlines())
        segments = [self.make_segment("text", lines)] if lines else []
        return ParsedDocument(file_name=file_name, file_type="txt", parser_name="text", segments=segments)
