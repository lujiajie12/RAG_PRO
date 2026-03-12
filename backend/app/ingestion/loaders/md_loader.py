from __future__ import annotations

import re

from .base_loader import BaseLoader
from ..types import ParsedDocument


class MarkdownLoader(BaseLoader):
    def parse_bytes(self, data: bytes, file_name: str) -> ParsedDocument:
        content = self.decode_text(data)
        segments = []
        paragraph_lines: list[str] = []

        def flush_paragraph() -> None:
            if paragraph_lines:
                raw_text = "\n".join(paragraph_lines).strip()
                if raw_text:
                    segments.append(self.make_segment("paragraph", raw_text, raw_text=raw_text))
                paragraph_lines.clear()

        for raw_line in content.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                flush_paragraph()
                continue

            heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading_match:
                flush_paragraph()
                text = heading_match.group(2).strip()
                if text:
                    segments.append(
                        self.make_segment(
                            "heading",
                            text,
                            raw_text=text,
                            heading_level=len(heading_match.group(1)),
                        )
                    )
                continue

            bullet_match = re.match(r"^[-*+]\s+(.*)$", stripped)
            if bullet_match:
                flush_paragraph()
                text = bullet_match.group(1).strip()
                if text:
                    segments.append(self.make_segment("list_item", text, raw_text=text))
                continue

            paragraph_lines.append(line)

        flush_paragraph()
        return ParsedDocument(file_name=file_name, file_type="md", parser_name="markdown", segments=segments)
