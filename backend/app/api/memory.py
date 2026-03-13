from __future__ import annotations

from flask import Blueprint, jsonify, request

from ._utils import require_query_arg
from ..errors import APIError
from ..models.schemas import CreateMemoryRequest
from ..services import MemoryService

memory_bp = Blueprint("memory", __name__, url_prefix="/api")


@memory_bp.get("/memory")
def list_memory():
    user_id = require_query_arg(request, "user_id")
    memories = MemoryService().list_memories(user_id)
    return jsonify([item.model_dump(mode="json") for item in memories])


@memory_bp.post("/memory")
def create_memory():
    payload = CreateMemoryRequest.model_validate(request.get_json(force=True))
    memory = MemoryService().create_memory(payload)
    return jsonify(memory.model_dump(mode="json")), 201


@memory_bp.delete("/memory/<memory_id>")
def delete_memory(memory_id: str):
    deleted = MemoryService().delete_memory(memory_id)
    if not deleted:
        raise APIError("memory not found", "resource_not_found", 404)
    return "", 204
