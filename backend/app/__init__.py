from __future__ import annotations

from flask import Flask

from .api import register_blueprints
from .config import get_settings
from .extensions import init_extensions


def create_app() -> Flask:
    settings = get_settings()
    app = Flask(__name__)
    app.config.update(settings.to_flask_config())

    init_extensions(app)
    register_blueprints(app)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": app.config["APP_NAME"],
            "status": "ok",
            "docs": "See the /api/health endpoint and the docs directory for implementation details.",
        }

    return app
