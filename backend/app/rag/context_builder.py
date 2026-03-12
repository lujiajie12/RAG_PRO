from __future__ import annotations


class ContextBuilder:
    def build(self, history: list[dict], memories: list[dict], retrieved_context: list[dict], query: str) -> dict:
        return {
            "system_prompt": "You are ContextPilot.",
            "history": history[-12:],
            "memories": memories[:5],
            "retrieved_context": retrieved_context[:6],
            "query": query,
        }
