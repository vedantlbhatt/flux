"""Shared search+rerank flow used by /search and /answer."""
import logging
from typing import NamedTuple

import config
from models.search import SearchResult
from services.tavily import tavily_search
from services.cohere_service import cohere_rerank
from services.reranker import merge_and_rank, tavily_only_results

logger = logging.getLogger(__name__)


class SearchFlowResult(NamedTuple):
    results: list[SearchResult]
    reranked: bool


def run_search(query: str, limit: int = 10, topic: str = "general", days: int | None = None) -> SearchFlowResult:
    """
    Run Tavily search + Cohere rerank. Returns ranked SearchResult list.
    Raises on Tavily failure. Degrades to Tavily order on Cohere failure.
    """
    if not config.TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not configured")
    tavily_data = tavily_search(
        config.TAVILY_API_KEY,
        query,
        max_results=20,
        topic=topic,
        days=days,
    )
    results_list = tavily_data.get("results") or []
    documents = [f"{r.get('title', '')}\n{r.get('content', '')}" for r in results_list]

    if config.COHERE_API_KEY:
        try:
            scores = cohere_rerank(config.COHERE_API_KEY, query, documents, top_n=len(documents))
            ranked = merge_and_rank(results_list, scores)
            return SearchFlowResult(results=ranked[:limit], reranked=True)
        except Exception as e:
            logger.warning("Cohere rerank failed: %s", e)
            ranked = tavily_only_results(results_list)
            return SearchFlowResult(results=ranked[:limit], reranked=False)
    ranked = tavily_only_results(results_list)
    return SearchFlowResult(results=ranked[:limit], reranked=False)
