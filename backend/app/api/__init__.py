from __future__ import annotations

from flask import Flask

from .chat import chat_bp
from .documents import documents_bp
from .health import health_bp
from .memory import memory_bp
from .retrieval import retrieval_bp
from .sessions import sessions_bp


def register_blueprints(app: Flask) -> None:
    for blueprint in (health_bp, sessions_bp, documents_bp, memory_bp, retrieval_bp, chat_bp):
        app.register_blueprint(blueprint)
