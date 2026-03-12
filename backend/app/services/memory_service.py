from __future__ import annotations

from ..models.orm import Memory
from ..models.schemas import CreateMemoryRequest, MemoryRecord
from ..repos.memory import MemoryRepository


class MemoryService:
    def __init__(self, repo: MemoryRepository | None = None) -> None:
        self.repo = repo or MemoryRepository()

    def list_memories(self, user_id: str) -> list[MemoryRecord]:
        return [MemoryRecord.model_validate(item) for item in self.repo.list_by_user(user_id)]

    def create_memory(self, payload: CreateMemoryRequest) -> MemoryRecord:
        memory = Memory(
            user_id=payload.user_id,
            category=payload.category,
            summary=payload.summary,
            content=payload.content,
            pinned=payload.pinned,
            source_session_id=payload.source_session_id,
        )
        return MemoryRecord.model_validate(self.repo.create(memory))

    def delete_memory(self, memory_id: str) -> bool:
        memory = self.repo.get(memory_id)
        if memory is None:
            return False
        self.repo.delete(memory)
        return True
