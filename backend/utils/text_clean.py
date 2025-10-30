from __future__ import annotations

import re

WHITESPACE_RE = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse whitespace to single spaces to stabilise matching/snippetting."""
    return WHITESPACE_RE.sub(" ", text or "").strip()


def truncate_for_snippet(text: str, max_chars: int = 400) -> str:
    """Create a bounded snippet without cutting mid-word."""
    normalized = normalize_whitespace(text)
    if len(normalized) <= max_chars:
        return normalized
    cutoff = normalized.rfind(" ", 0, max_chars)
    if cutoff == -1:
        cutoff = max_chars
    return normalized[:cutoff].rstrip() + "…"
