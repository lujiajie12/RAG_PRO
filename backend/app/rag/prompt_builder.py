from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from .context_builder import DEFAULT_CONTEXT_SYSTEM_PROMPT


class FinalAnswerPromptBuilder:
    def build_messages(
        self,
        *,
        query: str,
        user_id: str,
        kb_id: str | None,
        retrieval_mode: str,
        web_search_enabled: bool,
        context_plan: dict[str, Any],
    ) -> list[SystemMessage | HumanMessage]:
        system_prompt = self._compose_system_prompt(str(context_plan.get("system_prompt") or DEFAULT_CONTEXT_SYSTEM_PROMPT))
        user_prompt = self._compose_user_prompt(
            query=query,
            user_id=user_id,
            kb_id=kb_id,
            retrieval_mode=retrieval_mode,
            web_search_enabled=web_search_enabled,
            context_plan=context_plan,
        )
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

    @staticmethod
    def _compose_system_prompt(system_prompt: str) -> str:
        return (
            f"{system_prompt}\n\n"
            "你是 ContextPilot，一名面向知识库问答的 AI 助手。\n"
            "回答规则：\n"
            "1. 优先依据检索到的上下文回答，禁止把没有证据的内容说成事实。\n"
            "2. memory 主要用于用户偏好和稳定背景信息，不能覆盖检索证据。\n"
            "3. 如果检索证据不足，请明确说明“当前知识库证据不足”，并指出还缺什么信息。\n"
            "4. 回答尽量结构化、直接，默认使用与用户问题相同的语言。\n"
            "5. 如果引用证据，请优先使用上下文编号，如 [CTX-1]、[CTX-2]。"
        )

    def _compose_user_prompt(
        self,
        *,
        query: str,
        user_id: str,
        kb_id: str | None,
        retrieval_mode: str,
        web_search_enabled: bool,
        context_plan: dict[str, Any],
    ) -> str:
        history_text = self._format_history(context_plan.get("history", []))
        memory_text = self._format_memories(context_plan.get("memories", []))
        context_text = self._format_context(context_plan.get("retrieved_context", []))
        token_usage = context_plan.get("token_usage", {})

        return (
            "[会话元数据]\n"
            f"user_id: {user_id}\n"
            f"kb_id: {kb_id or 'none'}\n"
            f"retrieval_mode: {retrieval_mode}\n"
            f"web_search_enabled: {'true' if web_search_enabled else 'false'}\n"
            f"history_tokens: {token_usage.get('history', 0)}\n"
            f"memory_tokens: {token_usage.get('memory', 0)}\n"
            f"retrieved_context_tokens: {token_usage.get('retrieved_context', 0)}\n\n"
            "[最近对话历史]\n"
            f"{history_text}\n\n"
            "[长期记忆]\n"
            f"{memory_text}\n\n"
            "[检索上下文]\n"
            f"{context_text}\n\n"
            "[用户问题]\n"
            f"{query}\n\n"
            "[输出要求]\n"
            "请直接给出最终回答。\n"
            "如果证据足够，先给结论，再给关键依据。\n"
            "如果证据不足，明确说明不足，不要编造。"
        )

    @staticmethod
    def _format_history(history: list[dict[str, Any]]) -> str:
        if not history:
            return "无"

        blocks: list[str] = []
        for index, message in enumerate(history, start=1):
            role = str(message.get("role", "user"))
            content = " ".join(str(message.get("content", "")).split())
            blocks.append(f"{index}. {role}: {content}")
        return "\n".join(blocks)

    @staticmethod
    def _format_memories(memories: list[dict[str, Any]]) -> str:
        if not memories:
            return "无"

        blocks: list[str] = []
        for memory in memories:
            category = str(memory.get("category", "memory"))
            summary = " ".join(str(memory.get("summary", "")).split())
            content = " ".join(str(memory.get("content", "")).split())
            blocks.append(f"- [{category}] {summary}: {content}".strip())
        return "\n".join(blocks)

    @staticmethod
    def _format_context(retrieved_context: list[dict[str, Any]]) -> str:
        if not retrieved_context:
            return "无"

        blocks: list[str] = []
        for index, item in enumerate(retrieved_context, start=1):
            metadata = dict(item.get("metadata", {}))
            locators = metadata.get("source_locators", {})
            locators_json = json.dumps(locators, ensure_ascii=False) if locators else "{}"
            score = item.get("score")
            header = (
                f"[CTX-{index}] file={item.get('file_name', 'unknown')} "
                f"document_id={item.get('document_id', 'unknown')} "
                f"chunk_id={item.get('chunk_id', 'unknown')} "
                f"score={score if score is not None else 'n/a'} "
                f"locators={locators_json}"
            )
            content = str(item.get("content", "")).strip()
            blocks.append(f"{header}\n{content}".strip())
        return "\n\n".join(blocks)
