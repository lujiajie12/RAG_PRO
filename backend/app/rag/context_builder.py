from __future__ import annotations

from .tokenizer import count_tokens, split_text_by_tokens


class ContextBuilder:
    def __init__(
        self,
        *,
        context_token_budget: int = 2400,
        max_history_messages: int = 12,
        max_memories: int = 5,
    ) -> None:
        self.context_token_budget = context_token_budget
        self.max_history_messages = max_history_messages
        self.max_memories = max_memories

    def build(
        self,
        history: list[dict],
        memories: list[dict],
        retrieved_context: list[dict],
        query: str,
        *,
        system_prompt: str = "You are ContextPilot.",
        context_token_budget: int | None = None,
    ) -> dict:
        total_budget = max(1, context_token_budget or self.context_token_budget)

        packed_history = history[-self.max_history_messages :]
        packed_memories = memories[: self.max_memories]

        history_tokens = sum(count_tokens(self._history_text(item)) for item in packed_history)
        memory_tokens = sum(count_tokens(self._memory_text(item)) for item in packed_memories)
        reserved_tokens = history_tokens + memory_tokens
        retrieved_budget = max(0, total_budget - reserved_tokens)

        packed_context, retrieved_tokens = self._pack_retrieved_context(retrieved_context, retrieved_budget)

        return {
            "system_prompt": system_prompt,
            "history": packed_history,
            "memories": packed_memories,
            "retrieved_context": packed_context,
            "query": query,
            "token_budget": total_budget,
            "token_usage": {
                "history": history_tokens,
                "memory": memory_tokens,
                "retrieved_context": retrieved_tokens,
                "remaining": max(0, total_budget - reserved_tokens - retrieved_tokens),
            },
        }

    @staticmethod
    def _pack_retrieved_context(contexts: list[dict], budget: int) -> tuple[list[dict], int]:
        packed: list[dict] = []
        used_tokens = 0

        for context in contexts:
            content = str(context.get("content", ""))
            content_tokens = count_tokens(content)
            if content_tokens <= 0:
                continue
            if packed and used_tokens + content_tokens > budget:
                break
            if not packed and content_tokens > budget and budget > 0:
                truncated = ContextBuilder._truncate_context(context, budget)
                if truncated is None:
                    break
                packed.append(truncated)
                used_tokens += count_tokens(str(truncated.get("content", "")))
                break
            packed.append(context)
            used_tokens += content_tokens

        return packed, used_tokens

    @staticmethod
    def _truncate_context(context: dict, budget: int) -> dict | None:
        if budget <= 0:
            return None
        windows = split_text_by_tokens(str(context.get("content", "")), max_tokens=budget, overlap_tokens=0)
        if not windows:
            return None
        truncated = dict(context)
        truncated["content"] = str(windows[0]["text"])
        truncated["content_preview"] = truncated["content"][:220]
        metadata = dict(truncated.get("metadata", {}))
        metadata["truncated_for_budget"] = True
        metadata["truncated_token_count"] = int(windows[0]["token_count"])
        truncated["metadata"] = metadata
        return truncated

    @staticmethod
    def _history_text(item: dict) -> str:
        role = str(item.get("role", "user"))
        content = str(item.get("content", ""))
        return f"{role}: {content}"

    @staticmethod
    def _memory_text(item: dict) -> str:
        summary = str(item.get("summary", ""))
        content = str(item.get("content", ""))
        return f"{summary}\n{content}".strip()
