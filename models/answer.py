"""Answer response and citation models for GET /answer and conversation messages."""
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """One cited source: title, url, relevance score, rank."""

    title: str
    url: str
    score: float
    rank: int = Field(description="Position in results (1-indexed)")


class AnswerResponse(BaseModel):
    """Response for GET /answer: synthesized answer plus citations."""

    query: str
    answer: str
    citations: list[Citation]
    model: str = "gemini-2.5-flash"
