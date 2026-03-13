from __future__ import annotations

from flask import Flask, jsonify
from pydantic import ValidationError

from .api import register_blueprints
from .config import get_settings
from .errors import APIError
from .extensions import init_extensions


def create_app() -> Flask:
    settings = get_settings()
    app = Flask(__name__)
    app.config.update(settings.to_flask_config())

    init_extensions(app)
    register_blueprints(app)

    @app.errorhandler(APIError)
    def handle_api_error(exc: APIError):
        return (
            jsonify(
                {
                    "error": exc.error,
                    "code": exc.code,
                    "details": exc.details,
                }
            ),
            exc.status_code,
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return (
            jsonify(
                {
                    "error": "request validation failed",
                    "code": "validation_error",
                    "details": {"errors": exc.errors()},
                }
            ),
            400,
        )

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": app.config["APP_NAME"],
            "status": "ok",
            "docs": "See the /api/health endpoint and the docs directory for implementation details.",
        }

    return app
