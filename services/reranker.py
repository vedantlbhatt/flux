"""Merge Tavily results + Cohere scores into ranked SearchResult list."""
import hashlib
from models.search import SearchResult


def _url_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def tavily_only_results(tavily_results: list[dict]) -> list[SearchResult]:
    """Build SearchResult list from Tavily only (no Cohere)."""
    out: list[SearchResult] = []
    for i, r in enumerate(tavily_results):
        url = r.get("url", "")
        title = r.get("title", "")
        content = r.get("content", "")[:300]
        out.append(
            SearchResult(
                id=_url_id(url),
                url=url,
                title=title,
                snippet=content,
                score=0.0,
                rank=i + 1,
            )
        )
    return out


def merge_and_rank(
    tavily_results: list[dict],
    cohere_scores: list[tuple[int, float]],
) -> list[SearchResult]:
    """
    Build SearchResult list from Tavily + Cohere.
    cohere_scores: [(original_index, relevance_score), ...] in reranked order.
    """
    # Cohere returns results in reranked order
    out: list[SearchResult] = []
    for rank, (orig_idx, score) in enumerate(cohere_scores, start=1):
        if orig_idx >= len(tavily_results):
            continue
        r = tavily_results[orig_idx]
        url = r.get("url", "")
        title = r.get("title", "")
        content = r.get("content", "")[:300]
        out.append(
            SearchResult(
                id=_url_id(url),
                url=url,
                title=title,
                snippet=content,
                score=round(score, 4),
                rank=rank,
            )
        )
    return out
