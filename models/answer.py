from pydantic import BaseModel, Field


class Citation(BaseModel):
    title: str
    url: str
    score: float
    rank: int = Field(description="Position in results (1-indexed)")


class AnswerResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation]
    model: str = "gemini-2.5-flash"
