from __future__ import annotations

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from .middleware import build_agent_middleware
from .tools import build_tools


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
        middleware=build_agent_middleware(app_config),
        system_prompt=(
            "You are ContextPilot. Prefer retrieved evidence, cite sources when available, "
            "and say when the knowledge base is insufficient."
        ),
    )
