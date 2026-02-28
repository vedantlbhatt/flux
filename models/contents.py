from pydantic import BaseModel


class PageContent(BaseModel):
    url: str
    title: str
    content: str
    word_count: int
    success: bool
