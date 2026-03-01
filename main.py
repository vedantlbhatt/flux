"""Flux API — live web search with semantic reranking.

Pipeline: query → Tavily retrieval → Cohere rerank → return.
Routers: health, search, answer, contents, conversations.
"""
import logging
import uuid
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

import config
from routers import health, search, answer, contents, conversations
from utils.responses import PrettyJSONResponse
from utils.safe_errors import (
    redact_message,
    safe_internal_message,
    validation_error_message,
)

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO))
# Prevent httpx from logging full request URLs (which include API keys)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan: no startup/shutdown logic; in-memory store resets on restart."""
    yield
    logger.info("Flux API shutting down, waiting for in-flight requests...")
    await asyncio.sleep(3)
    logger.info("Flux API shutdown complete")


app = FastAPI(
    title="Flux",
    description="Live web search with semantic reranking for AI apps",
    version="0.1.0",
    lifespan=lifespan,
)

if config.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS if "*" not in config.CORS_ORIGINS else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


# Max request body size (1MB). Reject early when Content-Length exceeds this.
MAX_BODY_BYTES = 1 * 1024 * 1024


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with Content-Length over MAX_BODY_BYTES with 413."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_BODY_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"error": "Request body too large", "code": "PAYLOAD_TOO_LARGE"},
                    )
            except ValueError:
                pass
        return await call_next(request)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Set X-Request-ID on request and response for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIDMiddleware)
app.add_middleware(BodySizeLimitMiddleware)

app.include_router(health.router)
app.include_router(search.router)
app.include_router(answer.router)
app.include_router(contents.router)
app.include_router(conversations.router)


@app.get("/")
def root():
    return {"message": "Flux API", "docs": "/docs", "demo": "/demo/", "health": "/health"}


@app.get("/demo")
def demo_redirect():
    return RedirectResponse(url="/demo/", status_code=302)


# Serve demo UI at /demo/ (same origin when deployed on Railway etc.)
_demo_dir = Path(__file__).resolve().parent / "demo"
if _demo_dir.is_dir():
    app.mount("/demo", StaticFiles(directory=str(_demo_dir), html=True), name="demo")


# --- Global error handlers: all errors return { error, code } with correct status ---
@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc: RequestValidationError):
    """Invalid request body or query params → 400 INVALID_BODY."""
    return PrettyJSONResponse(status_code=400, content={"error": str(exc), "code": "INVALID_BODY"})


@app.exception_handler(Exception)
async def global_handler(request, exc: Exception):
    """Unhandled exception → 500 INTERNAL; log full traceback."""
    logger.exception("Unhandled exception")
    safe_msg = safe_internal_message()
    return PrettyJSONResponse(status_code=500, content={"error": safe_msg, "code": "INTERNAL"})
