from __future__ import annotations

import math
import re
from collections import Counter
from hashlib import blake2b


EMBEDDING_DIMENSION = 3072
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]|[a-z0-9_]+", re.IGNORECASE)


def tokenize_text(text: str) -> list[str]:
    if not text:
        return []
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def term_frequencies(text: str) -> Counter[str]:
    return Counter(tokenize_text(text))


def embed_text(text: str, dimension: int = EMBEDDING_DIMENSION) -> list[float]:
    if dimension <= 0:
        raise ValueError("dimension must be positive")

    frequencies = term_frequencies(text)
    if not frequencies:
        return [0.0] * dimension

    vector = [0.0] * dimension
    total_terms = sum(frequencies.values()) or 1

    for term, frequency in frequencies.items():
        weight = 1.0 + math.log1p(frequency / total_terms)
        index = _stable_index(term, dimension)
        vector[index] += weight * _stable_sign(term)

        if len(term) >= 4:
            shingle = term[:4]
            shingle_index = _stable_index(f"shingle:{shingle}", dimension)
            vector[shingle_index] += weight * 0.35

    return _l2_normalize(vector)


def cosine_similarity(left: list[float] | None, right: list[float] | None) -> float:
    if left is None or right is None:
        return 0.0

    left_values = list(left)
    right_values = list(right)
    if not left_values or not right_values or len(left_values) != len(right_values):
        return 0.0

    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for left_value, right_value in zip(left_values, right_values, strict=False):
        dot += left_value * right_value
        left_norm += left_value * left_value
        right_norm += right_value * right_value

    if left_norm <= 0 or right_norm <= 0:
        return 0.0
    return dot / math.sqrt(left_norm * right_norm)


def _stable_index(text: str, dimension: int) -> int:
    digest = blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dimension


def _stable_sign(text: str) -> float:
    digest = blake2b(f"sign:{text}".encode("utf-8"), digest_size=1).digest()
    return 1.0 if digest[0] % 2 == 0 else -1.0


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return vector
    return [value / norm for value in vector]
