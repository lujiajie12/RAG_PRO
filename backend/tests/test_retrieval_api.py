from __future__ import annotations

from app.extensions import db
from app.models.orm import Document, DocumentChunk
from app.rag.embeddings import embed_text


def _seed_chunked_document(user_id: str, kb_id: str) -> None:
    document = Document(
        user_id=user_id,
        kb_id=kb_id,
        file_name="hybrid-retrieval.md",
        file_type="md",
        storage_key=f"documents/{kb_id}/hybrid-retrieval.md",
        status="indexed",
        parsed_type="markdown",
        chunk_count=1,
    )
    db.session.add(document)
    db.session.flush()

    parent_content = (
        "Hybrid retrieval combines vector similarity, BM25 lexical matching and reranking so the system can recover "
        "both semantic matches and exact keyword hits before building the final parent context."
    )
    parent_chunk = DocumentChunk(
        document_id=document.id,
        user_id=user_id,
        kb_id=kb_id,
        chunk_type="parent",
        content=parent_content,
        token_count=34,
        metadata_json={"file_name": document.file_name, "source_locators": {"page_number": 2}},
        embedding=embed_text(parent_content),
    )
    db.session.add(parent_chunk)
    db.session.flush()

    child_content = "Hybrid retrieval uses vector search plus BM25 before reranking the final evidence set."
    db.session.add(
        DocumentChunk(
            document_id=document.id,
            user_id=user_id,
            kb_id=kb_id,
            parent_id=parent_chunk.id,
            chunk_type="child",
            content=child_content,
            token_count=17,
            metadata_json={"file_name": document.file_name, "source_locators": {"page_number": 2}},
            embedding=embed_text(child_content),
        )
    )
    db.session.commit()


def test_retrieval_debug_returns_real_hits(client, app, test_user_id):
    with app.app_context():
        _seed_chunked_document(test_user_id, "kb-debug")

    response = client.post(
        "/api/retrieval/debug",
        json={
            "user_id": test_user_id,
            "kb_id": "kb-debug",
            "query": "How does hybrid retrieval use BM25 and vector search?",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["vector_hits"]
    assert payload["bm25_hits"]
    assert payload["rrf_hits"]
    assert payload["rerank_hits"]
    assert payload["final_context"]
    assert payload["final_context"][0]["file_name"] == "hybrid-retrieval.md"
    assert payload["prompt_budget"]["retrieved_context"] > 0
    assert payload["prompt_budget"]["retrieved_context"] <= payload["prompt_budget"]["retrieved_context_budget"]


def test_retrieval_debug_respects_context_budget(client, app, test_user_id):
    app.config["CONTEXT_TOKEN_BUDGET"] = 18
    with app.app_context():
        _seed_chunked_document(test_user_id, "kb-tight-budget")

    response = client.post(
        "/api/retrieval/debug",
        json={
            "user_id": test_user_id,
            "kb_id": "kb-tight-budget",
            "query": "Explain vector search and BM25 in hybrid retrieval.",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["final_context"]
    assert payload["prompt_budget"]["retrieved_context"] <= 18
    assert payload["final_context"][0]["metadata"].get("truncated_for_budget") is True
