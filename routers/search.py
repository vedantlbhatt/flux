"""GET /search — live web search, Cohere reranked.

Validate → Tavily → Cohere rerank (or degrade) → SearchResponse. No business logic in router.
"""
import logging
from fastapi import APIRouter, Query
import config
from models.search import SearchResponse
from utils.responses import PrettyJSONResponse
from models.error import ErrorResponse
from services.search_flow import run_search
from utils.safe_errors import redact_message

router = APIRouter(tags=["search"])
logger = logging.getLogger(__name__)


@router.get(
    "/search",
    response_model=SearchResponse,
    response_class=PrettyJSONResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
def search(
    q: str = Query(..., description="Natural language query"),
    limit: int = Query(10, ge=1, le=20),
    topic: str | None = Query(None),
    days: int | None = Query(None, ge=1),
):
    """Live web search: validate params → Tavily → Cohere rerank → SearchResponse."""
    # Validate query and optional filters before any external call
    if not q or not q.strip():
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "Missing required query parameter", "code": "MISSING_QUERY"},
        )
    if len(q) > 500:
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "Query exceeds 500 characters", "code": "QUERY_TOO_LONG"},
        )
    if topic is not None and topic not in ("news", "general"):
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "topic must be 'news' or 'general'", "code": "INVALID_TOPIC"},
        )
    if days is not None and days < 1:
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "days must be >= 1", "code": "INVALID_DAYS"},
        )
    if not config.TAVILY_API_KEY:
        return PrettyJSONResponse(
            status_code=502,
            content={"error": "Tavily API key not configured", "code": "TAVILY_ERROR"},
        )

    try:
        flow = run_search(q.strip(), limit=limit, topic=topic or "general", days=days)
    except ValueError as e:
        return PrettyJSONResponse(status_code=502, content={"error": redact_message(str(e)), "code": "TAVILY_ERROR"})
    except Exception as e:
        logger.warning("Search failed: %s", e)
        return PrettyJSONResponse(status_code=502, content={"error": redact_message(str(e)), "code": "TAVILY_ERROR"})

    if not flow.results:
        return PrettyJSONResponse(
            status_code=404,
            content={"error": "No results found", "code": "NO_RESULTS"},
        )

    return SearchResponse(
        query=q.strip(),
        results=flow.results,
        total=len(flow.results),
        reranked=flow.reranked,
    )
