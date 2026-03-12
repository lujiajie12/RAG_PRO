from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..models.schemas import CreateSessionRequest
from ..services import SessionService

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")


@sessions_bp.get("")
def list_sessions():
    user_id = request.args.get("user_id", "demo-user")
    sessions = SessionService().list_sessions(user_id)
    return jsonify([item.model_dump(mode="json") for item in sessions])


@sessions_bp.post("")
def create_session():
    payload = CreateSessionRequest.model_validate(request.get_json(force=True))
    session = SessionService().create_session(payload)
    return jsonify(session.model_dump(mode="json")), 201
