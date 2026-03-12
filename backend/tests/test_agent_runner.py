from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.factory import is_agent_enabled
from app.agent.runner import AgentRunner


class FakeAgent:
    def invoke(self, _: dict) -> dict:
        return {
            "messages": [
                HumanMessage(content="Tell me about hybrid retrieval."),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "id": "call-1",
                            "name": "rag_search",
                            "args": {"query": "hybrid retrieval", "kb_id": "kb-1", "top_k": 8},
                        }
                    ],
                ),
                ToolMessage(
                    content='{"final_context": [{"chunk_id": "p-1"}]}',
                    tool_call_id="call-1",
                    name="rag_search",
                    status="success",
                ),
                AIMessage(content="Hybrid retrieval combines vector recall and BM25 before reranking."),
            ]
        }


def test_agent_runner_parses_answer_and_tool_trace():
    runner = AgentRunner({"CHAT_MODEL": "qwen-plus"}, agent=FakeAgent())

    result = runner.invoke(
        {
            "query": "Tell me about hybrid retrieval.",
            "user_id": "demo-user",
            "kb_id": "kb-1",
            "history": [],
            "memories": [],
            "retrieved_context": [],
            "retrieval_mode": "hybrid",
            "web_search_enabled": False,
        }
    )

    assert "Hybrid retrieval" in result["answer"]
    assert result["tool_trace"] == [
        {
            "name": "rag_search",
            "status": "completed",
            "input": {"query": "hybrid retrieval", "kb_id": "kb-1", "top_k": 8},
            "output": {"final_context": [{"chunk_id": "p-1"}]},
        }
    ]


def test_is_agent_enabled_checks_placeholder_keys():
    assert is_agent_enabled({"OPENAI_API_KEY": "sk-live"}) is True
    assert is_agent_enabled({"OPENAI_API_KEY": "replace-me"}) is False
    assert is_agent_enabled({"OPENAI_API_KEY": ""}) is False
