from __future__ import annotations


class ParentChildSplitter:
    def __init__(self, parent_size: int = 1000, child_size: int = 220) -> None:
        self.parent_size = parent_size
        self.child_size = child_size

    def split(self, text: str) -> dict[str, list[dict]]:
        return {
            "parents": [{"id": "p-1", "content": text[: self.parent_size]}],
            "children": [{"id": "c-1", "parent_id": "p-1", "content": text[: self.child_size]}],
        }
