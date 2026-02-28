"""Conversation and message models for stateful multi-turn search."""
from pydantic import BaseModel, Field

from models.answer import Citation
from models.search import SearchResult


class Message(BaseModel):
    """A single message in a conversation."""

    id: str = Field(description="Unique message ID (UUID)")
    query: str = Field(description="User query for this turn")
    answer: str = Field(description="Synthesized answer")
    citations: list[Citation] = Field(description="Source citations")
    results: list[SearchResult] = Field(description="Search results used")
    created_at: str = Field(description="ISO 8601 timestamp")


class Conversation(BaseModel):
    """A multi-turn conversation with context-aware search."""

    id: str = Field(description="Unique conversation ID (UUID)")
    created_at: str = Field(description="ISO 8601 timestamp")
    message_count: int = Field(description="Number of messages")
    messages: list[Message] = Field(description="All messages in order")


class ConversationListItem(BaseModel):
    """Conversation summary for list endpoint (messages omitted)."""

    id: str
    created_at: str
    message_count: int


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""

    conversations: list[ConversationListItem]
    total: int = Field(description="Total conversations in store")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Page size used")


class AddMessageRequest(BaseModel):
    """Request body for adding a message."""

    query: str = Field(description="Natural language query")
