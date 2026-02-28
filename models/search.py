from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    id: str = Field(description="Stable hash of url")
    url: str
    title: str
    snippet: str = Field(description="Clean extracted text excerpt, 150–300 chars")
    score: float = Field(description="Cohere relevance score, 0.0–1.0")
    rank: int = Field(description="Position in results (1-indexed)")


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
    reranked: bool = Field(description="False only if Cohere call failed")
