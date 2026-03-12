from __future__ import annotations

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from .middleware import build_agent_middleware
from .tools import build_tools


def is_agent_enabled(app_config: dict) -> bool:
    api_key = str(app_config.get("OPENAI_API_KEY", "") or "").strip()
    return bool(api_key and api_key.lower() not in {"replace-me", "your-api-key", "none"})


def create_contextpilot_agent(app_config: dict) -> object:
    model = ChatOpenAI(
        base_url=app_config["OPENAI_BASE_URL"],
        api_key=app_config["OPENAI_API_KEY"],
        model=app_config["CHAT_MODEL"],
        temperature=0.2,
    )
    return create_agent(
        model=model,
        tools=build_tools(app_config),
        middleware=build_agent_middleware(app_config, model),
        system_prompt=(
            "You are ContextPilot. Prefer retrieved evidence over unsupported claims. "
            "Use the provided retrieved context first, and only call tools when the supplied context is insufficient. "
            "When you do call tools, keep calls minimal and grounded. "
            "If the knowledge base is insufficient, say so clearly."
        ),
        name="contextpilot-agent",
    )
