"""GET /answer — synthesized answer from live web sources with citations."""
import logging
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

import config
from models.answer import AnswerResponse, Citation
from models.error import ErrorResponse
from services.search_flow import run_search
from services.gemini_service import gemini_generate

router = APIRouter(tags=["answer"])
logger = logging.getLogger(__name__)


def _build_prompt(query: str, sources: list[tuple[str, str]]) -> str:
    parts = [
        "Answer the following question using only the sources provided.",
        "Be concise. Cite sources by number [1], [2], etc.",
        "",
        f"Question: {query}",
        "",
        "Sources:",
    ]
    for i, (title, snippet) in enumerate(sources, start=1):
        parts.append(f"[{i}] {title}\n{snippet}")
        parts.append("")
    return "\n".join(parts)


@router.get(
    "/answer",
    response_model=AnswerResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
def answer(
    q: str = Query(..., description="Natural language query"),
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
    if not config.GEMINI_API_KEY:
        return JSONResponse(
            status_code=502,
            content={"error": "Gemini API key not configured", "code": "ANSWER_FAILED"},
        )

    # 1–9. Search + rerank (same as /search with limit=10)
    try:
        flow = run_search(q.strip(), limit=10, topic=topic or "general", days=days)
    except Exception as e:
        logger.warning("Search failed: %s", e)
        return JSONResponse(
            status_code=502,
            content={"error": str(e), "code": "TAVILY_ERROR"},
        )

    if not flow.results:
        return JSONResponse(
            status_code=404,
            content={"error": "No results found", "code": "NO_RESULTS"},
        )

    # 10. Take top 5 by rank_flux
    top5 = flow.results[:5]
    sources = [(r.title, r.snippet) for r in top5]

    # 11–12. Build prompt, call Gemini
    prompt = _build_prompt(q.strip(), sources)
    try:
        answer_text = gemini_generate(config.GEMINI_API_KEY, prompt, max_tokens=512)
    except Exception as e:
        logger.warning("Gemini failed: %s", e)
        return JSONResponse(
            status_code=502,
            content={"error": str(e), "code": "ANSWER_FAILED"},
        )

    # 14. Build citations from top 5
    citations = [
        Citation(title=r.title, url=r.url, score=r.score, rank_flux=r.rank_flux)
        for r in top5
    ]

    return AnswerResponse(query=q.strip(), answer=answer_text, citations=citations)
