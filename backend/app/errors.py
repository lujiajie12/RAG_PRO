from __future__ import annotations

from typing import Any


class APIError(Exception):
    def __init__(
        self,
        error: str,
        code: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(error)
        self.error = error
        self.code = code
        self.status_code = status_code
        self.details = details or {}
