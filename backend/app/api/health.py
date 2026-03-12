from __future__ import annotations

from flask import Blueprint, current_app

health_bp = Blueprint("health", __name__, url_prefix="/api/health")


@health_bp.get("")
def healthcheck() -> dict[str, object]:
    return {
        "service": current_app.config["APP_NAME"],
        "status": "ok",
        "env": "development" if current_app.config["DEBUG"] else "production",
    }
