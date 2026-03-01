"""Tavily Search API client. Raises on non-200. Retries on 429/503/500."""
import httpx

from utils.retry import retry_http

TAVILY_URL = "https://api.tavily.com/search"


def tavily_search(
    api_key: str,
    query: str,
    *,
    max_results: int = 20,
    topic: str = "general",
    search_depth: str = "basic",
    days: int | None = None,
) -> dict:
    """Call Tavily search API. Raises httpx.HTTPStatusError on failure."""
    body: dict = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "topic": topic,
        "search_depth": search_depth,
    }
    if days is not None and days >= 1:
        # Map days to Tavily time_range
        if days <= 1:
            body["time_range"] = "day"
        elif days <= 7:
            body["time_range"] = "week"
        elif days <= 31:
            body["time_range"] = "month"
        else:
            body["time_range"] = "year"

    with httpx.Client(timeout=30.0) as client:
        def do_request():
            resp = client.post(TAVILY_URL, json=body)
            resp.raise_for_status()
            return resp.json()
        return retry_http(do_request)
