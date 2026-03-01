"""Page content model for GET /contents (Tavily extract)."""
from pydantic import BaseModel


class PageContent(BaseModel):
    """Extracted page: url, title, cleaned content, word count, success flag."""

    url: str
    title: str
    content: str
    word_count: int
    success: bool
