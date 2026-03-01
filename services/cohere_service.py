"""Cohere Rerank API client. Returns list of (index, relevance_score). Retries on 429/503/500."""
import httpx

from utils.retry import retry_http

COHERE_RERANK_URL = "https://api.cohere.com/v2/rerank"


def cohere_rerank(
    api_key: str,
    query: str,
    documents: list[str],
    *,
    model: str = "rerank-v3.5",
    top_n: int | None = None,
) -> list[tuple[int, float]]:
    """
    Rerank documents by relevance. Returns list of (original_index, relevance_score).
    Raises httpx.HTTPStatusError on failure.
    """
    if not documents:
        return []

    top_n = top_n if top_n is not None else min(len(documents), 20)
    # Cross-encoder: scores query-document relevance directly (not cosine on embeddings)
    payload = {
        "model": model,
        "query": query,
        "documents": documents,
        "top_n": top_n,
    }

    with httpx.Client(timeout=30.0) as client:
        def do_request():
            resp = client.post(
                COHERE_RERANK_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
        data = retry_http(do_request)
        results = data.get("results", [])
        return [(r["index"], r["relevance_score"]) for r in results]
