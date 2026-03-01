"""Flux API — live web search with semantic reranking."""
import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

import config
from routers import health, search, answer, contents, conversations
from utils.responses import PrettyJSONResponse
from utils.safe_errors import (
    redact_message,
    safe_internal_message,
    validation_error_message,
)

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: log. Shutdown: brief wait for in-flight requests."""
    logger.info("Flux API starting")
    if config.CORS_ORIGINS:
        logger.info("CORS enabled for origins: %s", config.CORS_ORIGINS)
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


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    msg = validation_error_message(exc)
    return PrettyJSONResponse(status_code=400, content={"error": msg, "code": "INVALID_BODY"})


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    safe_msg = safe_internal_message()
    return PrettyJSONResponse(status_code=500, content={"error": safe_msg, "code": "INTERNAL"})
