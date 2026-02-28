"""Flux API — live web search with semantic reranking."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from routers import health, search, answer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Flux",
    description="Live web search with semantic reranking for AI apps",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(search.router)
app.include_router(answer.router)


from fastapi.responses import JSONResponse
from utils.responses import PrettyJSONResponse


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc: RequestValidationError):
    return PrettyJSONResponse(status_code=400, content={"error": str(exc), "code": "INVALID_BODY"})


@app.exception_handler(Exception)
async def global_handler(request, exc: Exception):
    logger.exception("Unhandled exception")
    return PrettyJSONResponse(status_code=500, content={"error": str(exc), "code": "INTERNAL"})
