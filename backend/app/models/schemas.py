from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Citation(BaseModel):
    document_id: str
    file_name: str
    page: int | None = None
    chunk_id: str
    rerank_score: float | None = None


class ToolTrace(BaseModel):
    name: str
    status: Literal["planned", "running", "completed", "failed"]
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(APIModel):
    user_id: str
    session_id: str | None = None
    kb_id: str | None = None
    message: str = Field(min_length=1)
    allow_web: bool = False
    debug: bool = False


class ChatAnswer(APIModel):
    session_id: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)


class ChatStreamEnvelope(APIModel):
    event: Literal["token", "tool_call", "retrieval_debug", "final_answer", "error"]
    data: dict[str, Any]


class SessionSummary(APIModel):
    id: str
    user_id: str
    kb_id: str | None = None
    title: str
    thread_id: str
    last_message_at: datetime | None = None
    created_at: datetime


class CreateSessionRequest(APIModel):
    user_id: str
    kb_id: str | None = None
    title: str | None = None


class DocumentUploadResponse(APIModel):
    document_id: str
    kb_id: str
    status: str
    parsed_type: str


class DocumentSummary(APIModel):
    id: str
    user_id: str
    kb_id: str
    file_name: str
    file_type: str
    status: str
    parsed_type: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class MemoryRecord(APIModel):
    id: str
    user_id: str
    category: str
    summary: str
    content: str
    source_session_id: str | None = None
    pinned: bool = False
    score: float | None = None
    created_at: datetime
    updated_at: datetime


class CreateMemoryRequest(APIModel):
    user_id: str
    category: Literal["preference", "long_term_task", "background_fact", "manual_note"]
    summary: str
    content: str
    pinned: bool = False
    source_session_id: str | None = None


class RetrievalHit(APIModel):
    chunk_id: str
    file_name: str
    content_preview: str
    score: float
    parent_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalDebugRequest(APIModel):
    user_id: str
    kb_id: str
    query: str


class RetrievalDebugResponse(APIModel):
    query: str
    vector_hits: list[RetrievalHit]
    bm25_hits: list[RetrievalHit]
    rrf_hits: list[RetrievalHit]
    rerank_hits: list[RetrievalHit]
    final_context: list[RetrievalHit]
    prompt_budget: dict[str, int]
