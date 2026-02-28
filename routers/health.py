"""GET /health — confirms Tavily and Cohere keys are configured."""
from fastapi import APIRouter

import config

router = APIRouter(tags=["utility"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "cohere_ready": bool(config.COHERE_API_KEY),
        "tavily_ready": bool(config.TAVILY_API_KEY),
    }
