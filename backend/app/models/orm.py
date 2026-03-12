from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


def new_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    external_user_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)


class ConversationSession(TimestampMixin, db.Model):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    kb_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(160), default="New conversation")
    thread_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[list["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Message(TimestampMixin, db.Model):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    tool_trace: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)

    session: Mapped["ConversationSession"] = relationship(back_populates="messages")


class Document(TimestampMixin, db.Model):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    kb_id: Mapped[str] = mapped_column(String(64), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(32))
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    parsed_type: Mapped[str] = mapped_column(String(64), default="unknown")
    chunk_count: Mapped[int] = mapped_column(default=0)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(TimestampMixin, db.Model):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_doc_parent", "document_id", "parent_id"),
        Index("ix_document_chunks_user_kb_type", "user_id", "kb_id", "chunk_type"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    kb_id: Mapped[str] = mapped_column(String(64), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    chunk_type: Mapped[str] = mapped_column(String(16), default="child")
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(default=0)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(3072), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Memory(TimestampMixin, db.Model):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    summary: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    source_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pinned: Mapped[bool] = mapped_column(default=False)
    score: Mapped[float | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(3072), nullable=True)


class RetrievalLog(TimestampMixin, db.Model):
    __tablename__ = "retrieval_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    kb_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    query: Mapped[str] = mapped_column(Text)
    vector_hits: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    bm25_hits: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    rerank_hits: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    final_context: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
