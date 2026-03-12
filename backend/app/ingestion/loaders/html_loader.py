from __future__ import annotations

from bs4 import BeautifulSoup

from .base_loader import BaseLoader
from ..types import ParsedDocument


class HtmlLoader(BaseLoader):
    def parse_bytes(self, data: bytes, file_name: str) -> ParsedDocument:
        soup = BeautifulSoup(self.decode_text(data), "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        segments = []
        for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "th", "td"]):
            text = " ".join(element.get_text(" ", strip=True).split())
            if not text:
                continue

            if element.name and element.name.startswith("h"):
                segments.append(self.make_segment("heading", text, heading_level=int(element.name[1])))
            elif element.name == "li":
                segments.append(self.make_segment("list_item", text))
            elif element.name in {"th", "td"}:
                segments.append(self.make_segment("table_cell", text, tag=element.name))
            else:
                segments.append(self.make_segment("paragraph", text))

        return ParsedDocument(file_name=file_name, file_type="html", parser_name="html", segments=segments)
