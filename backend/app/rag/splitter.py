from __future__ import annotations

from typing import Any

from ..ingestion.types import CleanedDocument, CleanedSegment
from .tokenizer import count_tokens, split_text_by_tokens


PROTECTED_CHUNK_KINDS = {"heading", "list_item", "table_row", "slide_title"}


class ParentChildSplitter:
    def __init__(
        self,
        parent_tokens: int = 800,
        child_tokens: int = 180,
        parent_overlap_tokens: int = 120,
        child_overlap_tokens: int = 40,
        *,
        parent_size: int | None = None,
        child_size: int | None = None,
    ) -> None:
        self.parent_tokens = parent_size or parent_tokens
        self.child_tokens = child_size or child_tokens
        self.parent_overlap_tokens = parent_overlap_tokens
        self.child_overlap_tokens = child_overlap_tokens

    def split(self, document: CleanedDocument) -> dict[str, list[dict[str, Any]]]:
        if not isinstance(document, CleanedDocument):
            raise TypeError("ParentChildSplitter expects CleanedDocument input")

        parents = self._build_parent_chunks(document)
        children = self._build_child_chunks(document, parents)
        for parent in parents:
            parent.pop("segments", None)
        for child in children:
            child.pop("segments", None)
        return {"parents": parents, "children": children}

    def _build_parent_chunks(self, document: CleanedDocument) -> list[dict[str, Any]]:
        parents: list[dict[str, Any]] = []
        current_segments: list[CleanedSegment] = []
        current_tokens = 0
        current_section: tuple[str, ...] | None = None

        for segment in document.segments:
            section_path = tuple(segment.metadata.get("section_path", []))
            segment_tokens = int(segment.metadata.get("token_count", count_tokens(segment.cleaned_text)))

            if current_segments and current_section != section_path:
                parents.append(self._make_chunk("p", len(parents) + 1, current_segments, document, "parent"))
                current_segments = []
                current_tokens = 0

            if segment_tokens > self.parent_tokens:
                if current_segments:
                    parents.append(self._make_chunk("p", len(parents) + 1, current_segments, document, "parent"))
                    current_segments = []
                    current_tokens = 0
                for overflow_segment in self._split_oversized_segment(segment, self.parent_tokens, self.parent_overlap_tokens):
                    parents.append(self._make_chunk("p", len(parents) + 1, [overflow_segment], document, "parent"))
                current_section = section_path
                continue

            if current_segments and current_tokens + segment_tokens > self.parent_tokens:
                overlap_segments = self._collect_overlap_segments(current_segments, self.parent_overlap_tokens)
                parents.append(self._make_chunk("p", len(parents) + 1, current_segments, document, "parent"))
                current_segments = self._fit_overlap_segments(overlap_segments, segment, self.parent_tokens)
                current_tokens = self._sum_tokens(current_segments)
            else:
                current_segments.append(segment)
                current_tokens += segment_tokens

            current_section = section_path

        if current_segments:
            parents.append(self._make_chunk("p", len(parents) + 1, current_segments, document, "parent"))

        return parents

    def _build_child_chunks(
        self,
        document: CleanedDocument,
        parents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        children: list[dict[str, Any]] = []

        for parent in parents:
            parent_segments = parent["segments"]
            current_segments: list[CleanedSegment] = []
            current_tokens = 0

            for segment in parent_segments:
                segment_tokens = int(segment.metadata.get("token_count", count_tokens(segment.cleaned_text)))

                if segment_tokens > self.child_tokens:
                    if current_segments:
                        children.append(
                            self._make_chunk("c", len(children) + 1, current_segments, document, "child", parent_id=parent["id"])
                        )
                        current_segments = []
                        current_tokens = 0
                    for overflow_segment in self._split_oversized_segment(segment, self.child_tokens, self.child_overlap_tokens):
                        children.append(
                            self._make_chunk("c", len(children) + 1, [overflow_segment], document, "child", parent_id=parent["id"])
                        )
                    continue

                if current_segments and current_tokens + segment_tokens > self.child_tokens:
                    overlap_segments = self._collect_overlap_segments(current_segments, self.child_overlap_tokens)
                    children.append(
                        self._make_chunk("c", len(children) + 1, current_segments, document, "child", parent_id=parent["id"])
                    )
                    current_segments = self._fit_overlap_segments(overlap_segments, segment, self.child_tokens)
                    current_tokens = self._sum_tokens(current_segments)
                else:
                    current_segments.append(segment)
                    current_tokens += segment_tokens

            if current_segments:
                children.append(
                    self._make_chunk("c", len(children) + 1, current_segments, document, "child", parent_id=parent["id"])
                )

        return children

    def _make_chunk(
        self,
        prefix: str,
        order: int,
        segments: list[CleanedSegment],
        document: CleanedDocument,
        chunk_type: str,
        *,
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        content = "\n\n".join(segment.cleaned_text for segment in segments if segment.cleaned_text)
        metadata = {
            "chunk_type": chunk_type,
            "order": order,
            "token_count": count_tokens(content),
            "section_path": list(segments[0].metadata.get("section_path", [])) if segments else [],
            "segment_kinds": [segment.kind for segment in segments],
            "source_locators": self._aggregate_source_locators(segments),
            "document_title": document.metadata.get("title"),
            "parser_name": document.parser_name,
        }
        chunk = {
            "id": f"{prefix}-{order}",
            "content": content,
            "metadata": metadata,
            "segments": segments,
        }
        if parent_id is not None:
            chunk["parent_id"] = parent_id
        return chunk

    def _split_oversized_segment(
        self,
        segment: CleanedSegment,
        max_tokens: int,
        overlap_tokens: int,
    ) -> list[CleanedSegment]:
        windows = split_text_by_tokens(segment.cleaned_text, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
        if not windows:
            return [segment]

        split_segments: list[CleanedSegment] = []
        for window_index, window in enumerate(windows, start=1):
            metadata = dict(segment.metadata)
            metadata["token_count"] = int(window["token_count"])
            metadata["window_index"] = window_index
            metadata["window_token_start"] = int(window["token_start"])
            metadata["window_token_end"] = int(window["token_end"])
            split_segments.append(
                CleanedSegment(
                    kind=segment.kind,
                    raw_text=segment.raw_text,
                    cleaned_text=str(window["text"]),
                    metadata=metadata,
                )
            )
        return split_segments

    def _collect_overlap_segments(self, segments: list[CleanedSegment], overlap_tokens: int) -> list[CleanedSegment]:
        if overlap_tokens <= 0:
            return []

        overlap: list[CleanedSegment] = []
        collected_tokens = 0
        for segment in reversed(segments):
            segment_tokens = int(segment.metadata.get("token_count", count_tokens(segment.cleaned_text)))
            if collected_tokens >= overlap_tokens:
                break
            if overlap and collected_tokens + segment_tokens > overlap_tokens:
                break
            overlap.insert(0, segment)
            collected_tokens += segment_tokens
        return overlap

    def _fit_overlap_segments(
        self,
        overlap_segments: list[CleanedSegment],
        next_segment: CleanedSegment,
        max_tokens: int,
    ) -> list[CleanedSegment]:
        candidate_segments = list(overlap_segments) + [next_segment]
        while len(candidate_segments) > 1 and self._sum_tokens(candidate_segments) > max_tokens:
            candidate_segments.pop(0)
        return candidate_segments

    @staticmethod
    def _sum_tokens(segments: list[CleanedSegment]) -> int:
        return sum(int(segment.metadata.get("token_count", count_tokens(segment.cleaned_text))) for segment in segments)

    @staticmethod
    def _aggregate_source_locators(segments: list[CleanedSegment]) -> dict[str, int | list[int]]:
        locators: dict[str, set[int]] = {}
        for segment in segments:
            for key, value in segment.metadata.get("source_locators", {}).items():
                if isinstance(value, int):
                    locators.setdefault(key, set()).add(value)

        aggregated: dict[str, int | list[int]] = {}
        for key, values in locators.items():
            ordered = sorted(values)
            aggregated[key] = ordered[0] if len(ordered) == 1 else ordered
        return aggregated
