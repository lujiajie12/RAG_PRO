from __future__ import annotations

from flask import Request

from ..errors import APIError


def require_query_arg(request: Request, key: str) -> str:
    value = (request.args.get(key) or "").strip()
    if not value:
        raise APIError(f"{key} is required", "validation_error", 400)
    return value


def require_form_arg(request: Request, key: str) -> str:
    value = (request.form.get(key) or "").strip()
    if not value:
        raise APIError(f"{key} is required", "validation_error", 400)
    return value
