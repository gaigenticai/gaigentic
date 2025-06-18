from __future__ import annotations

import tiktoken


def split_text(text: str, max_tokens: int = 500) -> list[str]:
    """Split text into token-aware chunks."""

    enc = tiktoken.get_encoding("cl100k_base")
    normalized = " ".join(text.split())
    tokens = enc.encode(normalized)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i : i + max_tokens]
        chunks.append(enc.decode(chunk_tokens))
    return chunks
