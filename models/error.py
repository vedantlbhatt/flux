"""Structured error response: all error endpoints return this shape."""
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """JSON body for 4xx/5xx: human-readable message and machine-readable code."""

    error: str
    code: str
