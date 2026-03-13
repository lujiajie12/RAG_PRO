from __future__ import annotations

from flask import Blueprint, jsonify, request

from ._utils import require_query_arg
from ..models.schemas import CreateSessionRequest, UpdateSessionRequest
from ..services import SessionService

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")


@sessions_bp.get("")
def list_sessions():
    user_id = require_query_arg(request, "user_id")
    q = request.args.get("q")
    kb_id = request.args.get("kb_id")
    tag = request.args.get("tag")
    limit = request.args.get("limit", type=int) or 50
    offset = request.args.get("offset", type=int) or 0
    sessions = SessionService().list_sessions(
        user_id=user_id,
        q=q,
        kb_id=kb_id,
        tag=tag,
        limit=limit,
        offset=offset,
    )
    return jsonify([item.model_dump(mode="json") for item in sessions])


@sessions_bp.post("")
def create_session():
    payload = CreateSessionRequest.model_validate(request.get_json(force=True))
    session = SessionService().create_session(payload)
    return jsonify(session.model_dump(mode="json")), 201


@sessions_bp.get("/<session_id>")
def get_session(session_id: str):
    user_id = require_query_arg(request, "user_id")
    session = SessionService().get_session(user_id, session_id)
    return jsonify(session.model_dump(mode="json"))


@sessions_bp.patch("/<session_id>")
def patch_session(session_id: str):
    payload = UpdateSessionRequest.model_validate(request.get_json(force=True))
    session = SessionService().update_session(session_id, payload)
    return jsonify(session.model_dump(mode="json"))


@sessions_bp.get("/<session_id>/messages")
def list_messages(session_id: str):
    user_id = require_query_arg(request, "user_id")
    messages = SessionService().list_messages(user_id, session_id)
    return jsonify([item.model_dump(mode="json") for item in messages])
