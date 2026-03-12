from __future__ import annotations

from pathlib import Path

from .base_loader import BaseLoader
from .csv_loader import CsvLoader
from .docx_loader import DocxLoader
from .html_loader import HtmlLoader
from .md_loader import MarkdownLoader
from .pdf_loader import PdfLoader
from .ppt_loader import PptLoader
from .txt_loader import TxtLoader


DOCUMENT_LOADER_TYPES: dict[str, type[BaseLoader]] = {
    ".pdf": PdfLoader,
    ".docx": DocxLoader,
    ".txt": TxtLoader,
    ".md": MarkdownLoader,
    ".html": HtmlLoader,
    ".csv": CsvLoader,
    ".pptx": PptLoader,
}


class DocumentLoaderFactory:
    def __init__(self, loaders: dict[str, BaseLoader] | None = None) -> None:
        self.loaders = loaders or {suffix: loader_type() for suffix, loader_type in DOCUMENT_LOADER_TYPES.items()}

    def get_loader(self, file_name: str | Path) -> BaseLoader:
        suffix = Path(file_name).suffix.lower()
        loader = self.loaders.get(suffix)
        if loader is None:
            raise ValueError(f"Unsupported file type: {suffix}")
        return loader

    def load(self, file_path: str | Path) -> str:
        return self.get_loader(file_path).load(file_path)
