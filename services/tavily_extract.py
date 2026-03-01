"""Tavily Extract API client. Raises on non-200. Retries on 429/503/500."""
import httpx

from utils.retry import retry_http

TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"


def tavily_extract(api_key: str, urls: list[str], *, format: str = "markdown") -> dict:
    """Extract content from URLs. Raises httpx.HTTPStatusError on failure."""
    body: dict = {
        "api_key": api_key,
        "urls": urls,
        "format": format,
    }
    with httpx.Client(timeout=45.0) as client:
        def do_request():
            resp = client.post(TAVILY_EXTRACT_URL, json=body)
            resp.raise_for_status()
            return resp.json()
        return retry_http(do_request)
