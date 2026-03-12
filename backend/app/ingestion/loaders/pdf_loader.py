from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from .base_loader import BaseLoader
from ..types import ParsedDocument


class PdfLoader(BaseLoader):
    def parse_bytes(self, data: bytes, file_name: str) -> ParsedDocument:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            reader.decrypt("")

        segments = []
        for page_index, page in enumerate(reader.pages, start=1):
            text = self.normalize_lines((page.extract_text() or "").splitlines())
            if text:
                segments.append(self.make_segment("page", text, page_number=page_index))

        return ParsedDocument(
            file_name=file_name,
            file_type="pdf",
            parser_name="pdf",
            segments=segments,
            metadata={"page_count": len(reader.pages)},
        )
