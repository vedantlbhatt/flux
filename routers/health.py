"""GET /health — confirms Tavily and Cohere keys are configured."""
from fastapi import APIRouter

import config
from utils.responses import PrettyJSONResponse

router = APIRouter(tags=["utility"])


@router.get("/health", response_class=PrettyJSONResponse)
def health() -> dict:
    return {
        "status": "ok",
        "cohere_ready": bool(config.COHERE_API_KEY),
        "tavily_ready": bool(config.TAVILY_API_KEY),
    }
