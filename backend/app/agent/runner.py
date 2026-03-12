from __future__ import annotations

from .factory import create_contextpilot_agent


class AgentRunner:
    def __init__(self, app_config: dict) -> None:
        self.agent = create_contextpilot_agent(app_config)

    async def invoke(self, payload: dict) -> dict:
        return await self.agent.ainvoke(payload)
