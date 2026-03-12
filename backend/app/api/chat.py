from __future__ import annotations

from flask import Blueprint, Response, request, stream_with_context

from ..models.schemas import ChatRequest
from ..services import ChatService

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.post("/stream")
def stream_chat() -> Response:
    payload = ChatRequest.model_validate(request.get_json(force=True))
    service = ChatService()
    return Response(
        stream_with_context(service.stream(payload)),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
