from __future__ import annotations

from langchain.tools import tool


@tool
def rag_search(query: str, kb_id: str, top_k: int = 8, debug: bool = False) -> dict:
    """Retrieve evidence from the knowledge base using hybrid retrieval and reranking."""
    return {"query": query, "kb_id": kb_id, "top_k": top_k, "debug": debug}


@tool
def memory_recall(query: str, user_id: str) -> dict:
    """Recall relevant long-term memories for the current user."""
    return {"query": query, "user_id": user_id}


@tool
def save_memory(content: str, user_id: str, kind: str) -> dict:
    """Persist user preferences or durable facts to long-term memory."""
    return {"saved": True, "content": content, "user_id": user_id, "kind": kind}


@tool
def web_search(query: str) -> dict:
    """Fallback external search for questions not covered by the knowledge base."""
    return {"query": query, "result_count": 0}


@tool
def list_documents(kb_id: str, user_id: str) -> dict:
    """Return metadata for documents inside the current knowledge base."""
    return {"kb_id": kb_id, "user_id": user_id, "documents": []}


def build_tools(_: dict) -> list:
    return [rag_search, memory_recall, save_memory, web_search, list_documents]
