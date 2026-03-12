from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services import DocumentService

documents_bp = Blueprint("documents", __name__, url_prefix="/api")


@documents_bp.post("/upload")
def upload_document():
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "file is required"}), 400

    user_id = request.form.get("user_id", "demo-user")
    kb_id = request.form.get("kb_id", "default-kb")
    response = DocumentService().upload_document(user_id=user_id, kb_id=kb_id, file=file)
    return jsonify(response.model_dump(mode="json")), 201


@documents_bp.get("/documents")
def list_documents():
    user_id = request.args.get("user_id", "demo-user")
    kb_id = request.args.get("kb_id", "default-kb")
    documents = DocumentService().list_documents(user_id=user_id, kb_id=kb_id)
    return jsonify([item.model_dump(mode="json") for item in documents])


@documents_bp.delete("/documents/<document_id>")
def delete_document(document_id: str):
    deleted = DocumentService().delete_document(document_id)
    if not deleted:
        return jsonify({"error": "document not found"}), 404
    return "", 204
