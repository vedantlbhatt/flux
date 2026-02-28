"""GET /search — live web search, Cohere reranked."""
import logging
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

import config
from models.search import SearchResponse
from models.error import ErrorResponse
from services.tavily import tavily_search
from services.cohere_service import cohere_rerank
from services.reranker import merge_and_rank, tavily_only_results

router = APIRouter(tags=["search"])
logger = logging.getLogger(__name__)


@router.get(
    "/search",
    response_model=SearchResponse,
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
    if not q or not q.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Missing required query parameter", "code": "MISSING_QUERY"},
        )
    if len(q) > 500:
        return JSONResponse(
            status_code=400,
            content={"error": "Query exceeds 500 characters", "code": "QUERY_TOO_LONG"},
        )
    if topic is not None and topic not in ("news", "general"):
        return JSONResponse(
            status_code=400,
            content={"error": "topic must be 'news' or 'general'", "code": "INVALID_TOPIC"},
        )
    if days is not None and days < 1:
        return JSONResponse(
            status_code=400,
            content={"error": "days must be >= 1", "code": "INVALID_DAYS"},
        )

    if not config.TAVILY_API_KEY:
        return JSONResponse(
            status_code=502,
            content={"error": "Tavily API key not configured", "code": "TAVILY_ERROR"},
        )

    # 1. Tavily search
    try:
        tavily_data = tavily_search(
            config.TAVILY_API_KEY,
            q.strip(),
            max_results=20,
            topic=topic or "general",
            days=days,
        )
    except Exception as e:
        logger.warning("Tavily API failed: %s", e)
        return JSONResponse(
            status_code=502,
            content={"error": str(e), "code": "TAVILY_ERROR"},
        )

    results_list = tavily_data.get("results") or []
    if not results_list:
        return JSONResponse(
            status_code=404,
            content={"error": "No results found", "code": "NO_RESULTS"},
        )

    # 2. Cohere rerank (or fallback)
    documents = [f"{r.get('title', '')}\n{r.get('content', '')}" for r in results_list]
    reranked = True
    if config.COHERE_API_KEY:
        try:
            scores = cohere_rerank(config.COHERE_API_KEY, q.strip(), documents, top_n=len(documents))
            ranked = merge_and_rank(results_list, scores)
        except Exception as e:
            logger.warning("Cohere rerank failed, returning Tavily order: %s", e)
            ranked = tavily_only_results(results_list)
            reranked = False
    else:
        ranked = tavily_only_results(results_list)
        reranked = False

    # 3. Truncate to limit
    ranked = ranked[:limit]
    return SearchResponse(query=q.strip(), results=ranked, total=len(ranked), reranked=reranked)
