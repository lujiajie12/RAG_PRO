from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.extensions import db
from app.models.orm import ConversationSession, Message, SessionTag


def _seed_session(
    user_id: str,
    *,
    title: str,
    kb_id: str | None = None,
    summary: str | None = None,
    tags: list[str] | None = None,
    updated_at: datetime | None = None,
) -> ConversationSession:
    session = ConversationSession(
        user_id=user_id,
        kb_id=kb_id,
        title=title,
        summary=summary,
        thread_id=f"thread-{uuid4().hex}",
        model_name="qwen-plus",
        retrieval_mode="hybrid",
        web_search_enabled=False,
    )
    session.tags = [SessionTag(tag=tag) for tag in tags or []]
    if updated_at is not None:
        session.updated_at = updated_at
    db.session.add(session)
    db.session.commit()
    return session


def test_create_and_get_session(client, test_user_id):
    response = client.post(
        "/api/sessions",
        json={
            "user_id": test_user_id,
            "kb_id": "kb-guide",
            "title": "  Onboarding  ",
            "tags": ["Work", "work", " Guide "],
            "model_name": "qwen-max",
            "retrieval_mode": "vector",
            "web_search_enabled": True,
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["title"] == "Onboarding"
    assert payload["tags"] == ["work", "guide"]
    assert payload["model_name"] == "qwen-max"
    assert payload["retrieval_mode"] == "vector"
    assert payload["web_search_enabled"] is True

    detail = client.get(f"/api/sessions/{payload['id']}?user_id={test_user_id}")

    assert detail.status_code == 200
    assert detail.get_json()["id"] == payload["id"]


def test_list_sessions_supports_filters_and_pagination(client, app, test_user_id):
    with app.app_context():
        now = datetime.utcnow()
        older = now - timedelta(minutes=10)
        oldest = now - timedelta(minutes=20)
        _seed_session(
            test_user_id,
            title="Python Notes",
            kb_id="kb-a",
            summary="hybrid retrieval walkthrough",
            tags=["guide"],
            updated_at=now,
        )
        _seed_session(
            test_user_id,
            title="Java Notes",
            kb_id="kb-b",
            summary="vector search design",
            tags=["reference"],
            updated_at=older,
        )
        _seed_session(
            test_user_id,
            title="Tag Search",
            kb_id="kb-a",
            summary="misc",
            tags=["focus"],
            updated_at=oldest,
        )

    listed = client.get(f"/api/sessions?user_id={test_user_id}")
    assert listed.status_code == 200
    listed_payload = listed.get_json()
    assert [item["title"] for item in listed_payload] == ["Python Notes", "Java Notes", "Tag Search"]

    by_query = client.get(f"/api/sessions?user_id={test_user_id}&q=vector")
    assert by_query.status_code == 200
    assert [item["title"] for item in by_query.get_json()] == ["Java Notes"]

    by_kb = client.get(f"/api/sessions?user_id={test_user_id}&kb_id=kb-a")
    assert by_kb.status_code == 200
    assert [item["title"] for item in by_kb.get_json()] == ["Python Notes", "Tag Search"]

    by_tag = client.get(f"/api/sessions?user_id={test_user_id}&tag=focus")
    assert by_tag.status_code == 200
    assert [item["title"] for item in by_tag.get_json()] == ["Tag Search"]

    paged = client.get(f"/api/sessions?user_id={test_user_id}&limit=1&offset=1")
    assert paged.status_code == 200
    assert [item["title"] for item in paged.get_json()] == ["Java Notes"]


def test_patch_session_updates_partial_fields(client, app, test_user_id):
    with app.app_context():
        session = _seed_session(
            test_user_id,
            title="Before",
            kb_id="kb-before",
            summary="old summary",
            tags=["legacy"],
        )
        session_id = session.id

    response = client.patch(
        f"/api/sessions/{session_id}",
        json={
            "user_id": test_user_id,
            "title": "After",
            "kb_id": "kb-after",
            "tags": ["Alpha", "alpha", "Focus"],
            "model_name": "qwen-turbo",
            "retrieval_mode": "bm25",
            "web_search_enabled": True,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["title"] == "After"
    assert payload["kb_id"] == "kb-after"
    assert payload["tags"] == ["alpha", "focus"]
    assert payload["model_name"] == "qwen-turbo"
    assert payload["retrieval_mode"] == "bm25"
    assert payload["web_search_enabled"] is True


def test_list_messages_returns_citations_and_tool_trace(client, app, test_user_id):
    with app.app_context():
        session = _seed_session(
            test_user_id,
            title="Conversation",
            kb_id="kb-history",
        )
        session_id = session.id
        db.session.add_all(
            [
                Message(
                    session_id=session_id,
                    user_id=test_user_id,
                    role="user",
                    content="Explain hybrid retrieval",
                ),
                Message(
                    session_id=session_id,
                    user_id=test_user_id,
                    role="assistant",
                    content="Hybrid retrieval combines dense and sparse recall.",
                    citations=[
                        {
                            "document_id": "doc-1",
                            "file_name": "retrieval.txt",
                            "page": 2,
                            "chunk_id": "chunk-1",
                            "rerank_score": 0.91,
                        }
                    ],
                    tool_trace=[
                        {
                            "name": "rag_search",
                            "status": "completed",
                            "input": {"query": "Explain hybrid retrieval"},
                            "output": {"final_context": 3},
                        }
                    ],
                ),
            ]
        )
        db.session.commit()

    response = client.get(f"/api/sessions/{session_id}/messages?user_id={test_user_id}")

    assert response.status_code == 200
    payload = response.get_json()
    assert [item["role"] for item in payload] == ["user", "assistant"]
    assert payload[1]["citations"][0]["file_name"] == "retrieval.txt"
    assert payload[1]["tool_trace"][0]["name"] == "rag_search"
