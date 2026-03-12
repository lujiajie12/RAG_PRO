from __future__ import annotations

from flask import Blueprint, jsonify, request

from ._utils import require_query_arg
from ..models.schemas import CreateSessionRequest, UpdateSessionRequest
from ..services import SessionService

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")


@sessions_bp.get("")
def list_sessions():
    user_id = require_query_arg(request, "user_id")
    sessions = SessionService().list_sessions(
        user_id=user_id,
        q=request.args.get("q"),
        kb_id=request.args.get("kb_id"),
        tag=request.args.get("tag"),
        limit=request.args.get("limit", default=50, type=int),
        offset=request.args.get("offset", default=0, type=int),
    )
    return jsonify([item.model_dump(mode="json") for item in sessions])


@sessions_bp.get("/<session_id>")
def get_session(session_id: str):
    user_id = require_query_arg(request, "user_id")
    session = SessionService().get_session(user_id=user_id, session_id=session_id)
    return jsonify(session.model_dump(mode="json"))


@sessions_bp.post("")
def create_session():
    payload = CreateSessionRequest.model_validate(request.get_json(force=True))
    session = SessionService().create_session(payload)
    return jsonify(session.model_dump(mode="json")), 201


@sessions_bp.patch("/<session_id>")
def update_session(session_id: str):
    payload = UpdateSessionRequest.model_validate(request.get_json(force=True))
    session = SessionService().update_session(session_id, payload)
    return jsonify(session.model_dump(mode="json"))
