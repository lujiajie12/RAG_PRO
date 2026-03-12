from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..models.schemas import RetrievalDebugRequest
from ..services import RetrievalService

retrieval_bp = Blueprint("retrieval", __name__, url_prefix="/api/retrieval")


@retrieval_bp.post("/debug")
def retrieval_debug():
    payload = RetrievalDebugRequest.model_validate(request.get_json(force=True))
    debug_payload = RetrievalService().debug(payload)
    return jsonify(debug_payload.model_dump(mode="json"))
