from __future__ import annotations

from ..extensions import db
from ..models.orm import ChatAttachment


class ChatAttachmentRepository:
    # Insert one chat attachment row and commit it immediately.
    def create(self, attachment: ChatAttachment) -> ChatAttachment:
        db.session.add(attachment)
        db.session.commit()
        return attachment

    # Query attachments by ids for one user and one session.
    def list_by_ids(self, user_id: str, session_id: str, attachment_ids: list[str]) -> list[ChatAttachment]:
        if not attachment_ids:
            return []
        return (
            ChatAttachment.query.filter(
                ChatAttachment.user_id == user_id,
                ChatAttachment.session_id == session_id,
                ChatAttachment.id.in_(attachment_ids),
            )
            .order_by(ChatAttachment.created_at.asc())
            .all()
        )

    # Remove one attachment row and commit immediately.
    def delete(self, attachment: ChatAttachment) -> None:
        db.session.delete(attachment)
        db.session.commit()

    # Attach uploaded files to the user message that references them.
    def attach_to_message(self, attachments: list[ChatAttachment], message_id: str) -> None:
        for attachment in attachments:
            attachment.message_id = message_id
            db.session.add(attachment)
        db.session.commit()
