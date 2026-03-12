from __future__ import annotations

from pathlib import Path

from .loaders.loader_factory import DocumentLoaderFactory
from .types import LoadedDocument, ParsedDocument


class ParserRegistry:
    def __init__(self, loader_factory: DocumentLoaderFactory | None = None) -> None:
        self.loader_factory = loader_factory or DocumentLoaderFactory()

    def resolve(self, file_name: str) -> str:
        suffix = Path(file_name).suffix.lower()
        parser_types = {
            ".md": "markdown",
            ".txt": "text",
            ".html": "html",
            ".pdf": "pdf",
            ".docx": "docx",
            ".csv": "csv",
            ".pptx": "pptx",
        }
        return parser_types.get(suffix, suffix.lstrip(".") or "unknown")

    def parse(self, loaded_document: LoadedDocument) -> ParsedDocument:
        parser = self.loader_factory.get_loader(loaded_document.file_name)
        return parser.parse_bytes(loaded_document.content_bytes, loaded_document.file_name)
