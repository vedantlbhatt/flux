from pydantic import BaseModel


class Citation(BaseModel):
    title: str
    url: str
    score: float
    rank_flux: int


class AnswerResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation]
    model: str = "gemini-2.5-flash-lite"
