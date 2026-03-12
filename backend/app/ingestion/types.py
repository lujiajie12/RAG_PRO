from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LoadedDocument:
    source_uri: str
    file_name: str
    file_type: str
    content_bytes: bytes
    size_bytes: int
    mime_type: str | None = None


@dataclass(slots=True)
class ParsedSegment:
    kind: str
    text: str
    raw_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    file_name: str
    file_type: str
    parser_name: str
    segments: list[ParsedSegment]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return "\n\n".join(segment.text for segment in self.segments if segment.text)

    @property
    def preview(self) -> str:
        return self.text[:200]


@dataclass(slots=True)
class CleanedSegment:
    kind: str
    raw_text: str
    cleaned_text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return self.cleaned_text


@dataclass(slots=True)
class CleanedDocument:
    file_name: str
    file_type: str
    parser_name: str
    segments: list[CleanedSegment]
    metadata: dict[str, Any] = field(default_factory=dict)
    cleaning_stats: dict[str, int] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return "\n\n".join(segment.cleaned_text for segment in self.segments if segment.cleaned_text)

    @property
    def preview(self) -> str:
        return self.text[:200]


@dataclass(slots=True)
class EnrichedDocument:
    loaded: LoadedDocument
    parsed: ParsedDocument
    cleaned: CleanedDocument
    metadata: dict[str, Any]

    @property
    def text(self) -> str:
        return self.cleaned.text
