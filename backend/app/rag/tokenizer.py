from __future__ import annotations

from functools import lru_cache

import tiktoken


@lru_cache(maxsize=1)
def get_encoding():
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(get_encoding().encode(text))


def split_text_by_tokens(text: str, max_tokens: int, overlap_tokens: int = 0) -> list[dict[str, int | str]]:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens cannot be negative")
    if overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be smaller than max_tokens")

    token_ids = get_encoding().encode(text)
    if not token_ids:
        return []

    windows: list[dict[str, int | str]] = []
    step = max_tokens - overlap_tokens
    start = 0
    while start < len(token_ids):
        end = min(len(token_ids), start + max_tokens)
        chunk_token_ids = token_ids[start:end]
        chunk_text = get_encoding().decode(chunk_token_ids).strip()
        if chunk_text:
            windows.append(
                {
                    "text": chunk_text,
                    "token_start": start,
                    "token_end": end,
                    "token_count": len(chunk_token_ids),
                }
            )
        if end >= len(token_ids):
            break
        start += step
    return windows
