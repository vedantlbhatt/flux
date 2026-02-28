"""Merge Tavily results + Cohere scores into ranked SearchResult list."""
import hashlib
from models.search import SearchResult


def _url_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def tavily_only_results(tavily_results: list[dict]) -> list[SearchResult]:
    """Build SearchResult list from Tavily only (no Cohere). rank_original = rank_flux."""
    out: list[SearchResult] = []
    for i, r in enumerate(tavily_results):
        url = r.get("url", "")
        title = r.get("title", "")
        content = r.get("content", "")[:300]
        pos = i + 1
        out.append(
            SearchResult(
                id=_url_id(url),
                url=url,
                title=title,
                snippet=content,
                score=0.0,
                rank_original=pos,
                rank_flux=pos,
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
    # Cohere returns results in reranked order; index points to original position
    out: list[SearchResult] = []
    for rank_flux, (orig_idx, score) in enumerate(cohere_scores, start=1):
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
                rank_original=orig_idx + 1,
                rank_flux=rank_flux,
            )
        )
    return out
