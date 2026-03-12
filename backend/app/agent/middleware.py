from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, SummarizationMiddleware
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI


class ToolRetryMiddleware(AgentMiddleware):
    def __init__(self, retries: int = 2) -> None:
        self.retries = max(0, retries)

    def wrap_tool_call(self, request, handler: Callable):
        last_error: Exception | None = None
        for _ in range(self.retries + 1):
            try:
                return handler(request)
            except Exception as exc:  # pragma: no cover - exercised via async path in runtime
                last_error = exc
        return self._tool_error_message(request, last_error)

    async def awrap_tool_call(self, request, handler: Callable[[Any], Awaitable]):
        last_error: Exception | None = None
        for _ in range(self.retries + 1):
            try:
                return await handler(request)
            except Exception as exc:
                last_error = exc
        return self._tool_error_message(request, last_error)

    @staticmethod
    def _tool_error_message(request, error: Exception | None) -> ToolMessage:
        tool_name = request.tool_call.get("name", "tool")
        reason = str(error) if error is not None else "unknown tool failure"
        return ToolMessage(
            content=json.dumps({"error": f"{tool_name} failed", "reason": reason}, ensure_ascii=False),
            tool_call_id=request.tool_call["id"],
            name=tool_name,
            status="error",
        )


class EmptyResponseGuardMiddleware(AgentMiddleware):
    def wrap_model_call(self, request, handler: Callable):
        response = handler(request)
        return self._ensure_content(response)

    async def awrap_model_call(self, request, handler: Callable[[Any], Awaitable]):
        response = await handler(request)
        return self._ensure_content(response)

    @staticmethod
    def _ensure_content(response):
        result = getattr(response, "result", None)
        if result:
            first = result[0]
            if isinstance(first, AIMessage) and not str(first.content).strip() and not first.tool_calls:
                return AIMessage(
                    content=(
                        "I could not produce a grounded answer from the available context. "
                        "Try refining the question or retrieving more evidence first."
                    )
                )
        return response


def build_agent_middleware(app_config: dict, model: ChatOpenAI | None = None) -> list:
    summary_model = model or ChatOpenAI(
        base_url=app_config["OPENAI_BASE_URL"],
        api_key=app_config["OPENAI_API_KEY"],
        model=app_config["CHAT_MODEL"],
        temperature=0,
    )
    return [
        ToolRetryMiddleware(retries=2),
        EmptyResponseGuardMiddleware(),
        SummarizationMiddleware(
            model=summary_model,
            trigger=("messages", 24),
            keep=("messages", 12),
        ),
    ]
