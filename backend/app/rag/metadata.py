from __future__ import annotations

from collections import Counter

from ..ingestion.types import CleanedDocument, CleanedSegment, EnrichedDocument, LoadedDocument, ParsedDocument
from .tokenizer import count_tokens


class DocumentMetadataExtractor:
    def extract(
        self,
        loaded: LoadedDocument,
        parsed: ParsedDocument,
        cleaned: CleanedDocument,
    ) -> EnrichedDocument:
        enriched_segments = self._enrich_segments(cleaned.segments)
        text = "\n\n".join(segment.cleaned_text for segment in enriched_segments if segment.cleaned_text)
        segment_counter = Counter(segment.kind for segment in enriched_segments)
        metadata = {
            "source_uri": loaded.source_uri,
            "file_name": loaded.file_name,
            "file_type": loaded.file_type,
            "mime_type": loaded.mime_type,
            "size_bytes": loaded.size_bytes,
            "parser_name": cleaned.parser_name,
            "title": self._guess_title(cleaned.file_name, enriched_segments),
            "char_count": len(text),
            "word_count": len(text.split()),
            "token_count": count_tokens(text),
            "segment_count": len(enriched_segments),
            "segment_kinds": dict(segment_counter),
        }
        metadata.update(cleaned.metadata)
        metadata["cleaning"] = dict(cleaned.cleaning_stats)

        enriched_cleaned = CleanedDocument(
            file_name=cleaned.file_name,
            file_type=cleaned.file_type,
            parser_name=cleaned.parser_name,
            segments=enriched_segments,
            metadata=metadata,
            cleaning_stats=dict(cleaned.cleaning_stats),
        )
        return EnrichedDocument(loaded=loaded, parsed=parsed, cleaned=enriched_cleaned, metadata=metadata)

    def _enrich_segments(self, segments: list[CleanedSegment]) -> list[CleanedSegment]:
        enriched: list[CleanedSegment] = []
        heading_stack: list[str] = []
        current_slide_number: int | None = None
        current_slide_title: str | None = None

        for order, segment in enumerate(segments, start=1):
            metadata = dict(segment.metadata)
            section_path = self._resolve_section_path(
                segment=segment,
                metadata=metadata,
                heading_stack=heading_stack,
                current_slide_number=current_slide_number,
                current_slide_title=current_slide_title,
            )

            if segment.kind == "slide_title":
                current_slide_number = metadata.get("slide_number")
                current_slide_title = segment.cleaned_text
            elif metadata.get("slide_number") != current_slide_number:
                current_slide_title = None
                current_slide_number = metadata.get("slide_number")

            metadata["order"] = order
            metadata["token_count"] = count_tokens(segment.cleaned_text)
            metadata["section_path"] = section_path
            metadata["source_locators"] = self._source_locators(metadata)

            enriched.append(
                CleanedSegment(
                    kind=segment.kind,
                    raw_text=segment.raw_text,
                    cleaned_text=segment.cleaned_text,
                    metadata=metadata,
                )
            )

        return enriched

    def _resolve_section_path(
        self,
        *,
        segment: CleanedSegment,
        metadata: dict,
        heading_stack: list[str],
        current_slide_number: int | None,
        current_slide_title: str | None,
    ) -> list[str]:
        if segment.kind == "heading":
            level = int(metadata.get("heading_level") or metadata.get("level") or 1)
            while len(heading_stack) < level:
                heading_stack.append("")
            heading_stack[level - 1] = segment.cleaned_text
            del heading_stack[level:]
            return [item for item in heading_stack if item]

        if segment.kind == "slide_title":
            return [segment.cleaned_text]

        slide_number = metadata.get("slide_number")
        if slide_number is not None:
            if current_slide_number == slide_number and current_slide_title:
                return [current_slide_title]
            return [f"slide-{slide_number}"]

        page_number = metadata.get("page_number")
        if page_number is not None and not heading_stack:
            return [f"page-{page_number}"]

        return [item for item in heading_stack if item]

    @staticmethod
    def _source_locators(metadata: dict) -> dict[str, int]:
        locators: dict[str, int] = {}
        for key in ("page_number", "slide_number", "row_number", "heading_level"):
            value = metadata.get("heading_level") if key == "heading_level" else metadata.get(key)
            if isinstance(value, int):
                locators[key] = value
        return locators

    @staticmethod
    def _guess_title(file_name: str, segments: list[CleanedSegment]) -> str:
        for segment in segments:
            if segment.kind in {"heading", "slide_title"} and segment.cleaned_text.strip():
                return segment.cleaned_text.strip()[:120]
        for segment in segments:
            if segment.cleaned_text.strip():
                return segment.cleaned_text.strip()[:120]
        return file_name
