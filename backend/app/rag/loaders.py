from __future__ import annotations

import mimetypes
from pathlib import Path

from ..ingestion.loaders.base_loader import BaseLoader
from ..ingestion.loaders.loader_factory import DOCUMENT_LOADER_TYPES
from ..ingestion.types import LoadedDocument

DOCUMENT_LOADER_MAPPING: dict[str, str] = {
    suffix: loader_type.__name__ for suffix, loader_type in DOCUMENT_LOADER_TYPES.items()
}

SUPPORTED_DOCUMENT_SUFFIXES = tuple(DOCUMENT_LOADER_MAPPING.keys())


class LocalFileLoader:
    """Load local files into a structured raw-document envelope."""

    def load(self, file_path: str | Path) -> LoadedDocument:
        path = Path(file_path)
        file_name = path.name
        file_type = path.suffix.lower().lstrip(".")
        mime_type = mimetypes.guess_type(file_name)[0]
        content_bytes = path.read_bytes()
        return self.load_bytes(
            content_bytes,
            file_name=file_name,
            source_uri=str(path),
            mime_type=mime_type,
        )

    def load_bytes(
        self,
        content_bytes: bytes,
        *,
        file_name: str,
        source_uri: str,
        mime_type: str | None = None,
    ) -> LoadedDocument:
        file_type = Path(file_name).suffix.lower().lstrip(".")
        return LoadedDocument(
            source_uri=source_uri,
            file_name=file_name,
            file_type=file_type or "unknown",
            content_bytes=content_bytes,
            size_bytes=len(content_bytes),
            mime_type=mime_type,
        )


class DocumentLoaderFactory:
    """RAG-facing source loader plus parser mapping accessor."""

    def __init__(self, source_loader: LocalFileLoader | None = None) -> None:
        self.source_loader = source_loader or LocalFileLoader()

    def describe_mapping(self) -> dict[str, str]:
        return DOCUMENT_LOADER_MAPPING.copy()

    def load_document(self, file_path: str | Path) -> LoadedDocument:
        return self.source_loader.load(file_path)

    def load_bytes(
        self,
        content_bytes: bytes,
        *,
        file_name: str,
        source_uri: str,
        mime_type: str | None = None,
    ) -> LoadedDocument:
        return self.source_loader.load_bytes(
            content_bytes,
            file_name=file_name,
            source_uri=source_uri,
            mime_type=mime_type,
        )


__all__ = [
    "BaseLoader",
    "DOCUMENT_LOADER_MAPPING",
    "DocumentLoaderFactory",
    "SUPPORTED_DOCUMENT_SUFFIXES",
    "LoadedDocument",
    "LocalFileLoader",
]
