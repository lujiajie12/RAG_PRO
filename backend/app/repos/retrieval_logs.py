from __future__ import annotations

from ..extensions import db
from ..models.orm import RetrievalLog


class RetrievalLogRepository:
    # Insert one retrieval log row and commit it immediately.
    def create(self, log: RetrievalLog) -> RetrievalLog:
        db.session.add(log)
        db.session.commit()
        return log
