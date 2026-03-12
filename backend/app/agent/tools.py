from __future__ import annotations

from langchain.tools import tool

from ..models.schemas import CreateMemoryRequest
from ..rag.embeddings import term_frequencies
from ..services.document_service import DocumentService
from ..services.memory_service import MemoryService
from ..services.retrieval_service import RetrievalService


def build_tools(app_config: dict) -> list:
    default_user_id = str(app_config.get("DEFAULT_USER_ID", "demo-user"))
    retrieval_service = RetrievalService()
    document_service = DocumentService()
    memory_service = MemoryService()

    @tool
    def rag_search(query: str, kb_id: str, top_k: int = 8, debug: bool = False, user_id: str | None = None) -> dict:
        """Retrieve evidence from the knowledge base using hybrid retrieval and reranking."""
        result = retrieval_service.search(
            user_id=user_id or default_user_id,
            kb_id=kb_id,
            query=query,
            retrieval_mode="hybrid",
            top_k=top_k,
        )
        payload = {
            "query": query,
            "kb_id": kb_id,
            "top_k": top_k,
            "recall_top_k": result.get("recall_top_k"),
            "rerank_top_k": result.get("rerank_top_k"),
            "final_context": [
                {
                    "chunk_id": item["chunk_id"],
                    "document_id": item["document_id"],
                    "file_name": item["file_name"],
                    "score": item["score"],
                    "content_preview": item["content_preview"],
                }
                for item in result["final_context"]
            ],
        }
        if debug:
            payload["debug"] = {
                "vector_hits": result["vector_hits"],
                "bm25_hits": result["bm25_hits"],
                "rrf_hits": result["rrf_hits"],
                "rerank_hits": result["rerank_hits"],
                "diverse_hits": result.get("diverse_hits", []),
                "context_plan": result.get("context_plan", {}),
            }
        return payload

    @tool
    def memory_recall(query: str, user_id: str | None = None) -> dict:
        """Recall relevant long-term memories for the current user."""
        resolved_user_id = user_id or default_user_id
        memories = memory_service.list_memories(resolved_user_id)
        query_terms = term_frequencies(query)
        ranked = sorted(
            memories,
            key=lambda memory: sum(query_terms.get(term, 0) for term in term_frequencies(memory.content)),
            reverse=True,
        )
        return {
            "query": query,
            "user_id": resolved_user_id,
            "memories": [memory.model_dump(mode="json") for memory in ranked[:5]],
        }

    @tool
    def save_memory(content: str, user_id: str | None = None, kind: str = "manual_note") -> dict:
        """Persist user preferences or durable facts to long-term memory."""
        resolved_user_id = user_id or default_user_id
        payload = CreateMemoryRequest(
            user_id=resolved_user_id,
            category=kind if kind in {"preference", "long_term_task", "background_fact", "manual_note"} else "manual_note",
            summary=" ".join(content.split())[:120] or "Memory note",
            content=content,
        )
        record = memory_service.create_memory(payload)
        return {"saved": True, "record": record.model_dump(mode="json")}

    @tool
    def web_search(query: str) -> dict:
        """Fallback external search for questions not covered by the knowledge base."""
        return {"query": query, "result_count": 0, "status": "not_implemented"}

    @tool
    def list_documents(kb_id: str, user_id: str | None = None) -> dict:
        """Return metadata for documents inside the current knowledge base."""
        resolved_user_id = user_id or default_user_id
        documents = document_service.list_documents(resolved_user_id, kb_id)
        return {
            "kb_id": kb_id,
            "user_id": resolved_user_id,
            "documents": [document.model_dump(mode="json") for document in documents],
        }

    return [rag_search, memory_recall, save_memory, web_search, list_documents]
