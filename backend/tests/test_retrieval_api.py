from __future__ import annotations

from app.extensions import db
from app.models.orm import Document, DocumentChunk
from app.rag.embeddings import embed_text
from app.services.retrieval_service import RetrievalService


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


def _seed_named_document(user_id: str, kb_id: str, *, file_name: str, parent_content: str, child_content: str) -> None:
    document = Document(
        user_id=user_id,
        kb_id=kb_id,
        file_name=file_name,
        file_type=file_name.rsplit(".", 1)[-1],
        storage_key=f"documents/{kb_id}/{file_name}",
        status="indexed",
        parsed_type="pdf" if file_name.endswith(".pdf") else "markdown",
        chunk_count=1,
    )
    db.session.add(document)
    db.session.flush()

    parent_chunk = DocumentChunk(
        document_id=document.id,
        user_id=user_id,
        kb_id=kb_id,
        chunk_type="parent",
        content=parent_content,
        token_count=80,
        metadata_json={"file_name": document.file_name, "source_locators": {"page_number": 1}, "order": 1},
        embedding=embed_text(parent_content),
    )
    db.session.add(parent_chunk)
    db.session.flush()

    db.session.add(
        DocumentChunk(
            document_id=document.id,
            user_id=user_id,
            kb_id=kb_id,
            parent_id=parent_chunk.id,
            chunk_type="child",
            content=child_content,
            token_count=30,
            metadata_json={"file_name": document.file_name, "source_locators": {"page_number": 1}, "order": 1},
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


def test_retrieval_debug_can_focus_on_document_name(client, app, test_user_id):
    with app.app_context():
        _seed_named_document(
            test_user_id,
            "kb-filename",
            file_name="2407.01245v2.pdf",
            parent_content="这篇论文提出了一种新的知识追踪方法，通过多模态特征和动态聚类提升建模能力。",
            child_content="该论文通过多模态特征、动态滑动窗口和个性化能力值建模来提升知识追踪效果。",
        )
        _seed_named_document(
            test_user_id,
            "kb-filename",
            file_name="other-paper.pdf",
            parent_content="这是一篇无关论文，讨论传统推荐系统。",
            child_content="传统推荐系统使用协同过滤和召回排序。",
        )

    response = client.post(
        "/api/retrieval/debug",
        json={
            "user_id": test_user_id,
            "kb_id": "kb-filename",
            "query": "检索下2407.01245v2.pdf这个文档说的什么？简单一百字以内",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["final_context"]
    assert all(item["file_name"] == "2407.01245v2.pdf" for item in payload["final_context"])


def test_retrieval_service_resolves_document_reference_from_history(app, test_user_id):
    with app.app_context():
        _seed_named_document(
            test_user_id,
            "kb-history-doc",
            file_name="2407.01245v2.pdf",
            parent_content="这篇论文介绍了一种新的知识追踪模型，强调多模态行为特征与动态聚类。",
            child_content="模型核心包括多模态行为编码、动态聚类和连续能力值估计。",
        )
        _seed_named_document(
            test_user_id,
            "kb-history-doc",
            file_name="distractor.pdf",
            parent_content="这篇文档主要讨论数据库索引优化。",
            child_content="数据库索引优化与知识追踪无关。",
        )

        result = RetrievalService().search(
            user_id=test_user_id,
            kb_id="kb-history-doc",
            query="这个文档内容总结200字",
            history=[{"role": "user", "content": "帮我看下2407.01245v2.pdf这篇论文"}],
            memories=[],
        )

    assert result["final_context"]
    assert all(item["file_name"] == "2407.01245v2.pdf" for item in result["final_context"])
