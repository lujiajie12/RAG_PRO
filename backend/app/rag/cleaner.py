from __future__ import annotations

import re
from collections import Counter, defaultdict

from ..ingestion.types import CleanedDocument, CleanedSegment, ParsedDocument, ParsedSegment


PROTECTED_SEGMENT_KINDS = {"heading", "list_item", "table_row", "table_cell", "slide_title"}
CONTROL_CHARS_RE = re.compile(r"[\u0000-\u0008\u000b-\u001f\u007f-\u009f\u200b\u200c\u200d\ufeff]")
MULTISPACE_RE = re.compile(r"[ \t]+")
BAD_PLACEHOLDER_RE = re.compile(r"[�]{2,}")


class TextCleaner:
    def clean(self, parsed: ParsedDocument) -> CleanedDocument:
        cleaned_segments: list[CleanedSegment] = []
        stats = Counter(
            {
                "removed_control_chars": 0,
                "merged_lines": 0,
                "dropped_repeated_headers": 0,
                "dropped_repeated_footers": 0,
            }
        )

        for segment in parsed.segments:
            cleaned_text, segment_stats = self._clean_segment(segment)
            stats.update(segment_stats)
            if cleaned_text:
                cleaned_segments.append(
                    CleanedSegment(
                        kind=segment.kind,
                        raw_text=segment.raw_text,
                        cleaned_text=cleaned_text,
                        metadata=dict(segment.metadata),
                    )
                )

        self._drop_repeated_page_headers_and_footers(cleaned_segments, stats)
        cleaned_segments = [segment for segment in cleaned_segments if segment.cleaned_text]

        return CleanedDocument(
            file_name=parsed.file_name,
            file_type=parsed.file_type,
            parser_name=parsed.parser_name,
            segments=cleaned_segments,
            metadata=dict(parsed.metadata),
            cleaning_stats=dict(stats),
        )

    def _clean_segment(self, segment: ParsedSegment) -> tuple[str, Counter]:
        stats = Counter()
        text = segment.raw_text

        removed = len(CONTROL_CHARS_RE.findall(text))
        if removed:
            stats["removed_control_chars"] += removed
            text = CONTROL_CHARS_RE.sub("", text)

        text = BAD_PLACEHOLDER_RE.sub("", text)
        normalized_lines = [self._normalize_line(line) for line in text.splitlines()]
        normalized_lines = [line for line in normalized_lines if line]

        if segment.kind not in PROTECTED_SEGMENT_KINDS and segment.kind not in {"page", "slide_text"} and len(normalized_lines) > 1:
            stats["merged_lines"] += len(normalized_lines) - 1
            cleaned_text = " ".join(normalized_lines)
        elif segment.kind == "paragraph" and len(normalized_lines) > 1:
            stats["merged_lines"] += len(normalized_lines) - 1
            cleaned_text = " ".join(normalized_lines)
        else:
            cleaned_text = "\n".join(normalized_lines)

        return cleaned_text.strip(), stats

    @staticmethod
    def _normalize_line(line: str) -> str:
        stripped = line.strip()
        if not stripped:
            return ""
        return MULTISPACE_RE.sub(" ", stripped)

    def _drop_repeated_page_headers_and_footers(self, segments: list[CleanedSegment], stats: Counter) -> None:
        page_segments = [segment for segment in segments if segment.kind == "page" and "page_number" in segment.metadata]
        if len(page_segments) < 3:
            return

        header_counter = defaultdict(list)
        footer_counter = defaultdict(list)

        for segment in page_segments:
            lines = [line for line in segment.cleaned_text.splitlines() if line]
            if not lines:
                continue
            header_counter[lines[0]].append(segment)
            footer_counter[lines[-1]].append(segment)

        repeated_headers = {line for line, occurrences in header_counter.items() if len(occurrences) >= 3}
        repeated_footers = {line for line, occurrences in footer_counter.items() if len(occurrences) >= 3}

        for segment in page_segments:
            lines = [line for line in segment.cleaned_text.splitlines() if line]
            if not lines:
                continue

            if lines and lines[0] in repeated_headers:
                lines = lines[1:]
                stats["dropped_repeated_headers"] += 1
            if lines and lines[-1] in repeated_footers:
                lines = lines[:-1]
                stats["dropped_repeated_footers"] += 1

            segment.cleaned_text = "\n".join(lines).strip()
