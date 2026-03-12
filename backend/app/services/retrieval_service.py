from __future__ import annotations

from ..models.schemas import RetrievalDebugRequest, RetrievalDebugResponse, RetrievalHit


def _hit(chunk_id: str, file_name: str, score: float, parent_id: str | None = None) -> RetrievalHit:
    return RetrievalHit(
        chunk_id=chunk_id,
        file_name=file_name,
        content_preview="Parent Document Retrieval improves answer quality by returning a larger parent block.",
        score=score,
        parent_id=parent_id,
        metadata={"page": 12},
    )


class RetrievalService:
    def debug(self, payload: RetrievalDebugRequest) -> RetrievalDebugResponse:
        vector_hits = [_hit("c-101", "langchain-notes.md", 0.88, "p-11"), _hit("c-102", "rag-handbook.pdf", 0.84, "p-22")]
        bm25_hits = [_hit("c-203", "tutorial-guide.pdf", 15.2, "p-31"), _hit("c-101", "langchain-notes.md", 13.8, "p-11")]
        rrf_hits = [_hit("c-101", "langchain-notes.md", 0.93, "p-11"), _hit("c-203", "tutorial-guide.pdf", 0.91, "p-31")]
        rerank_hits = [_hit("c-101", "langchain-notes.md", 0.96, "p-11"), _hit("c-203", "tutorial-guide.pdf", 0.92, "p-31")]
        final_context = [_hit("p-11", "langchain-notes.md", 0.96), _hit("p-31", "tutorial-guide.pdf", 0.92)]
        return RetrievalDebugResponse(
            query=payload.query,
            vector_hits=vector_hits,
            bm25_hits=bm25_hits,
            rrf_hits=rrf_hits,
            rerank_hits=rerank_hits,
            final_context=final_context,
            prompt_budget={
                "system": 600,
                "history": 1200,
                "memory": 800,
                "retrieved_context": 2400,
                "user_query": 1000,
            },
        )
