from __future__ import annotations

from langchain.agents.middleware import SummarizationMiddleware


def build_agent_middleware(app_config: dict) -> list:
    return [
        SummarizationMiddleware(
            model=app_config["CHAT_MODEL"],
            max_tokens_before_summary=10_000,
            messages_to_keep=12,
        )
    ]
