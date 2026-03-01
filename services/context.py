"""Build context-aware query string from conversation history."""
from typing import Sequence


def build_context_query(
    current_query: str,
    previous_queries: Sequence[str],
    *,
    max_previous: int = 3,
) -> str:
    """
    Build a context-aware query for Tavily search.
    Takes the last N previous queries and appends the current query.
    Tavily results will be relevant to the full conversation, not just the latest turn.
    """
    recent = list(previous_queries)[-max_previous:] if previous_queries else []
    # Tavily gets full context; Cohere rerank still uses current_query only
    parts = list(recent) + [current_query]
    return " ".join(parts).strip()
