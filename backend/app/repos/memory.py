from __future__ import annotations

from ..extensions import db
from ..models.orm import Memory


class MemoryRepository:
    # Insert one memory row and commit it immediately.
    def create(self, memory: Memory) -> Memory:
        db.session.add(memory)
        db.session.commit()
        return memory

    # Query all memories for a user, newest updated first.
    def list_by_user(self, user_id: str) -> list[Memory]:
        return Memory.query.filter_by(user_id=user_id).order_by(Memory.updated_at.desc()).all()

    # Query one memory by its primary key. Returns None when missing.
    def get(self, memory_id: str) -> Memory | None:
        return db.session.get(Memory, memory_id)

    # Delete one memory row and commit the change immediately.
    def delete(self, memory: Memory) -> None:
        db.session.delete(memory)
        db.session.commit()
