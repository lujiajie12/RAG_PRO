from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from ..rag import FinalAnswerPromptBuilder


INVALID_API_KEYS = {"", "replace-me", "your-api-key", "none"}


def is_llm_enabled(app_config: dict[str, Any]) -> bool:
    api_key = str(app_config.get("OPENAI_API_KEY", "") or "").strip()
    return api_key.lower() not in INVALID_API_KEYS


class LLMAnswerService:
    def __init__(
        self,
        app_config: dict[str, Any],
        *,
        model: ChatOpenAI | None = None,
        prompt_builder: FinalAnswerPromptBuilder | None = None,
    ) -> None:
        self.app_config = app_config
        self.model = model or ChatOpenAI(
            base_url=app_config["OPENAI_BASE_URL"],
            api_key=app_config["OPENAI_API_KEY"],
            model=app_config["CHAT_MODEL"],
            temperature=0.2,
        )
        self.prompt_builder = prompt_builder or FinalAnswerPromptBuilder()

    def build_messages(
        self,
        *,
        query: str,
        user_id: str,
        kb_id: str | None,
        retrieval_mode: str,
        web_search_enabled: bool,
        context_plan: dict[str, Any],
    ):
        return self.prompt_builder.build_messages(
            query=query,
            user_id=user_id,
            kb_id=kb_id,
            retrieval_mode=retrieval_mode,
            web_search_enabled=web_search_enabled,
            context_plan=context_plan,
        )

    def stream_answer(
        self,
        *,
        query: str,
        user_id: str,
        kb_id: str | None,
        retrieval_mode: str,
        web_search_enabled: bool,
        context_plan: dict[str, Any],
    ) -> Iterator[str]:
        messages = self.build_messages(
            query=query,
            user_id=user_id,
            kb_id=kb_id,
            retrieval_mode=retrieval_mode,
            web_search_enabled=web_search_enabled,
            context_plan=context_plan,
        )
        for chunk in self.model.stream(messages):
            text = self._extract_text(chunk, strip=False)
            if text:
                yield text

    def generate_answer(
        self,
        *,
        query: str,
        user_id: str,
        kb_id: str | None,
        retrieval_mode: str,
        web_search_enabled: bool,
        context_plan: dict[str, Any],
    ) -> str:
        messages = self.build_messages(
            query=query,
            user_id=user_id,
            kb_id=kb_id,
            retrieval_mode=retrieval_mode,
            web_search_enabled=web_search_enabled,
            context_plan=context_plan,
        )
        response = self.model.invoke(messages)
        answer = self._extract_text(response)
        if not answer:
            raise ValueError("llm returned empty content")
        return answer

    @staticmethod
    def _extract_text(response: AIMessage | Any, *, strip: bool = True) -> str:
        content = getattr(response, "content", "")
        if isinstance(content, str):
            return content.strip() if strip else content

        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                    continue
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        chunks.append(str(item.get("text", "")))
                        continue
                    if "text" in item:
                        chunks.append(str(item["text"]))
            text = "".join(chunks)
            return text.strip() if strip else text

        text = str(content)
        return text.strip() if strip else text
