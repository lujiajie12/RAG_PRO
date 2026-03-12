from __future__ import annotations

from app.rag.context_builder import ContextBuilder
from app.rag.embeddings import embed_text
from app.rag.hybrid import HybridRetriever
from app.rag.tokenizer import count_tokens


def test_mmr_prefers_diverse_contexts_after_rerank():
    retriever = HybridRetriever(mmr_lambda=0.72)
    candidates = [
        {
            "chunk_id": "p-1",
            "document_id": "doc-1",
            "file_name": "doc-1.md",
            "content": "Hybrid retrieval combines vector search and BM25 before reranking the evidence.",
            "content_preview": "Hybrid retrieval combines vector search and BM25 before reranking the evidence.",
            "score": 0.96,
            "parent_id": None,
            "metadata": {"section_path": ["overview"]},
            "_embedding": embed_text("Hybrid retrieval combines vector search and BM25 before reranking the evidence."),
        },
        {
            "chunk_id": "p-2",
            "document_id": "doc-1",
            "file_name": "doc-1.md",
            "content": "Hybrid retrieval combines vector search and BM25 before reranking the evidence for answers.",
            "content_preview": "Hybrid retrieval combines vector search and BM25 before reranking the evidence for answers.",
            "score": 0.95,
            "parent_id": None,
            "metadata": {"section_path": ["overview"]},
            "_embedding": embed_text(
                "Hybrid retrieval combines vector search and BM25 before reranking the evidence for answers."
            ),
        },
        {
            "chunk_id": "p-3",
            "document_id": "doc-2",
            "file_name": "doc-2.md",
            "content": "MMR improves diversity by reducing near-duplicate contexts from the same document.",
            "content_preview": "MMR improves diversity by reducing near-duplicate contexts from the same document.",
            "score": 0.88,
            "parent_id": None,
            "metadata": {"section_path": ["diversity"]},
            "_embedding": embed_text(
                "MMR improves diversity by reducing near-duplicate contexts from the same document."
            ),
        },
    ]

    selected = retriever._select_diverse_contexts(
        "How do hybrid retrieval and MMR work together?",
        candidates,
        limit=2,
    )

    assert [item["chunk_id"] for item in selected] == ["p-1", "p-3"]


def test_context_builder_packs_within_token_budget():
    builder = ContextBuilder(context_token_budget=24)
    contexts = [
        {
            "chunk_id": "p-1",
            "content": "Hybrid retrieval combines dense recall, sparse recall, reranking and parent document restoration.",
            "metadata": {},
        },
        {
            "chunk_id": "p-2",
            "content": "Context packing should stop once the retrieved context budget is exhausted.",
            "metadata": {},
        },
    ]

    plan = builder.build([], [], contexts, "Explain hybrid retrieval.", context_token_budget=24)
    retrieved_tokens = sum(count_tokens(item["content"]) for item in plan["retrieved_context"])

    assert plan["retrieved_context"]
    assert retrieved_tokens <= 24
    assert plan["token_usage"]["retrieved_context"] == retrieved_tokens
