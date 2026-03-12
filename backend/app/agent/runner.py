from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

from .factory import create_contextpilot_agent


class AgentRunner:
    def __init__(self, app_config: dict, agent: object | None = None) -> None:
        self.app_config = app_config
        self.agent = agent or create_contextpilot_agent(app_config)

    def invoke(self, payload: dict) -> dict:
        result = self.agent.invoke({"messages": self._build_messages(payload)})
        return self._parse_result(result)

    async def ainvoke(self, payload: dict) -> dict:
        result = await self.agent.ainvoke({"messages": self._build_messages(payload)})
        return self._parse_result(result)

    def _build_messages(self, payload: dict) -> list[dict[str, str]]:
        history = payload.get("history", [])[-10:]
        memories = payload.get("memories", [])[:5]
        retrieved_context = payload.get("retrieved_context", [])

        messages: list[dict[str, str]] = []
        for message in history:
            role = str(message.get("role", "user"))
            if role not in {"user", "assistant", "system"}:
                role = "user"
            messages.append({"role": role, "content": str(message.get("content", ""))})

        messages.append(
            {
                "role": "user",
                "content": self._compose_user_prompt(
                    query=str(payload.get("query", "")),
                    user_id=str(payload.get("user_id", "")),
                    kb_id=payload.get("kb_id"),
                    retrieval_mode=str(payload.get("retrieval_mode", "hybrid")),
                    web_search_enabled=bool(payload.get("web_search_enabled", False)),
                    memories=memories,
                    retrieved_context=retrieved_context,
                ),
            }
        )
        return messages

    def _compose_user_prompt(
        self,
        *,
        query: str,
        user_id: str,
        kb_id: str | None,
        retrieval_mode: str,
        web_search_enabled: bool,
        memories: list[dict],
        retrieved_context: list[dict],
    ) -> str:
        memory_text = self._format_memories(memories)
        context_text = self._format_context(retrieved_context)
        web_search_text = "enabled" if web_search_enabled else "disabled"
        kb_text = kb_id or "none"

        return (
            "Answer the user using the supplied retrieved context before using tools.\n"
            f"user_id: {user_id}\n"
            f"kb_id: {kb_text}\n"
            f"retrieval_mode: {retrieval_mode}\n"
            f"web_search: {web_search_text}\n\n"
            "<retrieved_context>\n"
            f"{context_text}\n"
            "</retrieved_context>\n\n"
            "<memories>\n"
            f"{memory_text}\n"
            "</memories>\n\n"
            "<instructions>\n"
            "1. Prefer the retrieved context if it already answers the question.\n"
            "2. Use rag_search or list_documents only when the supplied context is insufficient.\n"
            "3. Use memory_recall only when long-term user preferences are relevant.\n"
            "4. If evidence is missing, say what is missing instead of making it up.\n"
            "</instructions>\n\n"
            "<user_query>\n"
            f"{query}\n"
            "</user_query>"
        )

    @staticmethod
    def _format_context(retrieved_context: list[dict]) -> str:
        if not retrieved_context:
            return "None"

        blocks: list[str] = []
        for index, item in enumerate(retrieved_context, start=1):
            metadata = item.get("metadata", {})
            locators = metadata.get("source_locators", {})
            blocks.append(
                (
                    f"[{index}] file={item.get('file_name')} "
                    f"document_id={item.get('document_id')} "
                    f"chunk_id={item.get('chunk_id')} "
                    f"locators={json.dumps(locators, ensure_ascii=False)}\n"
                    f"{item.get('content', '')}"
                ).strip()
            )
        return "\n\n".join(blocks)

    @staticmethod
    def _format_memories(memories: list[dict]) -> str:
        if not memories:
            return "None"
        return "\n".join(
            f"- {memory.get('summary')}: {memory.get('content')}"
            for memory in memories
        )

    def _parse_result(self, result: dict) -> dict:
        messages: Sequence[Any] = result.get("messages", [])
        answer = ""
        tool_traces = self._extract_tool_traces(messages)

        for message in reversed(messages):
            if isinstance(message, AIMessage) and str(message.content).strip():
                answer = str(message.content).strip()
                break

        return {
            "answer": answer,
            "tool_trace": tool_traces,
            "raw_messages": list(messages),
        }

    @staticmethod
    def _extract_tool_traces(messages: Sequence[Any]) -> list[dict]:
        traces_by_id: dict[str, dict] = {}
        ordered_ids: list[str] = []

        for message in messages:
            if isinstance(message, AIMessage):
                for tool_call in message.tool_calls:
                    tool_call_id = str(tool_call.get("id"))
                    if tool_call_id not in traces_by_id:
                        traces_by_id[tool_call_id] = {
                            "name": str(tool_call.get("name", "tool")),
                            "status": "planned",
                            "input": dict(tool_call.get("args", {})),
                            "output": {},
                        }
                        ordered_ids.append(tool_call_id)
            elif isinstance(message, ToolMessage):
                tool_call_id = str(message.tool_call_id)
                trace = traces_by_id.setdefault(
                    tool_call_id,
                    {"name": message.name or "tool", "status": "planned", "input": {}, "output": {}},
                )
                trace["status"] = "completed" if message.status == "success" else "failed"
                trace["name"] = trace.get("name") or message.name or "tool"
                trace["output"] = AgentRunner._tool_output_payload(message)
                if tool_call_id not in ordered_ids:
                    ordered_ids.append(tool_call_id)

        return [traces_by_id[tool_call_id] for tool_call_id in ordered_ids]

    @staticmethod
    def _tool_output_payload(message: ToolMessage) -> dict[str, Any]:
        content = message.content
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {"text": content}
            return {"text": content}
        return {"content": content}
