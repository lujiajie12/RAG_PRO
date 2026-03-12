from __future__ import annotations

from ..extensions import db
from ..models.orm import Memory


class MemoryRepository:
    def create(self, memory: Memory) -> Memory:
        db.session.add(memory)
        db.session.commit()
        return memory

    def list_by_user(self, user_id: str) -> list[Memory]:
        return Memory.query.filter_by(user_id=user_id).order_by(Memory.updated_at.desc()).all()

    def get(self, memory_id: str) -> Memory | None:
        return Memory.query.get(memory_id)

    def delete(self, memory: Memory) -> None:
        db.session.delete(memory)
        db.session.commit()
