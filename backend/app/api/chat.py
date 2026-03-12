from __future__ import annotations

from flask import Blueprint, Response, jsonify, request, stream_with_context

from ._utils import require_form_arg
from ..errors import APIError
from ..models.schemas import ChatRequest
from ..services import ChatAttachmentService, ChatService

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.post("/attachments")
def upload_chat_attachment():
    file = request.files.get("file")
    if file is None:
        raise APIError("file is required", "validation_error", 400)

    user_id = require_form_arg(request, "user_id")
    session_id = require_form_arg(request, "session_id")
    attachment = ChatAttachmentService().upload_attachment(user_id=user_id, session_id=session_id, file=file)
    return jsonify(attachment.model_dump(mode="json")), 201


@chat_bp.post("/stream")
def stream_chat() -> Response:
    payload = ChatRequest.model_validate(request.get_json(force=True))
    service = ChatService()
    return Response(
        stream_with_context(service.start_stream(payload)),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
