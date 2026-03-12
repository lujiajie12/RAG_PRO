from __future__ import annotations

from flask import Blueprint, jsonify, request

from ._utils import require_form_arg, require_query_arg
from ..errors import APIError
from ..services import DocumentService

documents_bp = Blueprint("documents", __name__, url_prefix="/api")


@documents_bp.post("/upload")
def upload_document():
    file = request.files.get("file")
    if file is None:
        raise APIError("file is required", "validation_error", 400)

    user_id = require_form_arg(request, "user_id")
    kb_id = require_form_arg(request, "kb_id")
    response = DocumentService().upload_document(user_id=user_id, kb_id=kb_id, file=file)
    return jsonify(response.model_dump(mode="json")), 201


@documents_bp.get("/documents")
def list_documents():
    user_id = require_query_arg(request, "user_id")
    kb_id = require_query_arg(request, "kb_id")
    documents = DocumentService().list_documents(user_id=user_id, kb_id=kb_id)
    return jsonify([item.model_dump(mode="json") for item in documents])


@documents_bp.delete("/documents/<document_id>")
def delete_document(document_id: str):
    deleted = DocumentService().delete_document(document_id)
    if not deleted:
        raise APIError("document not found", "resource_not_found", 404)
    return "", 204
