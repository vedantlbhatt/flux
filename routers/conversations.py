"""Conversation endpoints: create, list, get, add message, delete."""
import logging
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Path, Query
from fastapi.responses import Response

import config
from models.answer import Citation
from models.conversation import (
    AddMessageRequest,
    Conversation,
    ConversationListItem,
    ConversationListResponse,
    Message,
)
from models.error import ErrorResponse
from models.search import SearchResult
from services.context import build_context_query
from services.gemini_service import gemini_generate
from services.search_flow import run_search
from store import (
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    update_conversation,
)
from utils.responses import PrettyJSONResponse
from utils.safe_errors import redact_message

router = APIRouter(tags=["conversations"])
logger = logging.getLogger(__name__)

MAX_QUERY_LEN = 500
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _validate_conversation_id(conversation_id: str) -> PrettyJSONResponse | None:
    """Return error response if id is not a valid UUID; else None."""
    if not UUID_PATTERN.match(conversation_id):
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "Invalid conversation ID format", "code": "INVALID_CONVERSATION_ID"},
        )
    return None


SYSTEM_INSTRUCTION = (
    "Reply to the user naturally. Use the sources below only when the user's question actually needs them. "
    "For greetings (e.g. hi, hello), small talk, or simple questions that don't need web results, respond briefly and naturally—do not summarize or cite the sources, and do not give mini-essays on the origin of words or unrelated background from the sources."
)


def _build_message_prompt(current_query: str, history: list[tuple[str, str]], sources: list[tuple[str, str]]) -> str:
    """Build prompt with conversation history and new sources."""
    parts = [
        SYSTEM_INSTRUCTION,
        "",
        "When you do use the sources, cite them by number [1], [2], etc. Be concise.",
        "You have context from previous turns in this conversation.",
        "",
    ]
    if history:
        parts.append("Previous conversation:")
        for q, a in history:
            parts.append(f"Q: {q}")
            parts.append(f"A: {a}")
            parts.append("")
    parts.append(f"Question: {current_query}")
    parts.append("")
    parts.append("Sources:")
    for i, (title, snippet) in enumerate(sources, start=1):
        parts.append(f"[{i}] {title}\n{snippet}")
        parts.append("")
    return "\n".join(parts).strip()


def _store_to_conversation(conv: dict) -> Conversation:
    """Convert store dict to Conversation model."""
    messages = [
        Message(
            id=m["id"],
            query=m["query"],
            answer=m["answer"],
            citations=[Citation(**c) for c in m["citations"]],
            results=[SearchResult(**r) for r in m["results"]],
            created_at=m["created_at"],
        )
        for m in conv.get("messages", [])
    ]
    return Conversation(
        id=conv["id"],
        created_at=conv["created_at"],
        message_count=conv["message_count"],
        messages=messages,
    )


@router.post(
    "/conversations",
    response_model=Conversation,
    response_class=PrettyJSONResponse,
    summary="Create conversation",
    description="Create a new conversation. Returns the conversation with empty messages. Use the returned `id` for subsequent message requests.",
)
def create_conversation_endpoint():
    """Create a new conversation. Returns the conversation with empty messages."""
    conversation_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conv = create_conversation(conversation_id, created_at)
    return Conversation(
        id=conv["id"],
        created_at=conv["created_at"],
        message_count=conv["message_count"],
        messages=[],
    )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    response_class=PrettyJSONResponse,
    responses={400: {"model": ErrorResponse}},
    summary="List conversations",
    description="List all conversations sorted by creation date (newest first). Messages omitted for performance; use GET /conversations/{id} for full details.",
)
def list_conversations_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Conversations per page"),
):
    """List all conversations with pagination. Messages omitted for brevity."""
    items, total = list_conversations(page=page, page_size=page_size)
    return ConversationListResponse(
        conversations=[
            ConversationListItem(
                id=c["id"],
                created_at=c["created_at"],
                message_count=c["message_count"],
            )
            for c in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=Conversation,
    response_class=PrettyJSONResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get conversation",
    description="Retrieve a full conversation including all messages, answers, and search results.",
)
def get_conversation_endpoint(
    conversation_id: str = Path(..., description="Conversation ID"),
):
    """Retrieve full conversation with all messages and results."""
    err = _validate_conversation_id(conversation_id)
    if err is not None:
        return err
    conv = get_conversation(conversation_id)
    if not conv:
        return PrettyJSONResponse(
            status_code=404,
            content={"error": "Conversation not found", "code": "CONVERSATION_NOT_FOUND"},
        )
    return _store_to_conversation(conv)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=Message,
    response_class=PrettyJSONResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    summary="Add message",
    description="Add a query to the conversation. Runs context-aware search (last 3 queries + current) and synthesizes an answer with citations. Reranking uses the current query only.",
)
def add_message_endpoint(
    conversation_id: str = Path(..., description="Conversation ID"),
    body: AddMessageRequest = ...,
):
    """
    Add a query to the conversation. Runs context-aware search + synthesis.
    Uses last 3 queries for retrieval context; reranks by current query only.
    """
    err = _validate_conversation_id(conversation_id)
    if err is not None:
        return err
    query = (body.query or "").strip()
    if not query:
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "Missing required query field", "code": "MISSING_QUERY"},
        )
    if len(query) > MAX_QUERY_LEN:
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "Query exceeds 500 characters", "code": "QUERY_TOO_LONG"},
        )

    conv = get_conversation(conversation_id)
    if not conv:
        return PrettyJSONResponse(
            status_code=404,
            content={"error": "Conversation not found", "code": "CONVERSATION_NOT_FOUND"},
        )
    if conv.get("message_count", 0) >= config.MAX_MESSAGES_PER_CONVERSATION:
        return PrettyJSONResponse(
            status_code=400,
            content={
                "error": f"Conversation message limit ({config.MAX_MESSAGES_PER_CONVERSATION}) reached",
                "code": "MESSAGE_LIMIT_REACHED",
            },
        )

    if not config.TAVILY_API_KEY:
        return PrettyJSONResponse(
            status_code=502,
            content={"error": "Tavily API key not configured", "code": "TAVILY_ERROR"},
        )
    if not config.GEMINI_API_KEY:
        return PrettyJSONResponse(
            status_code=502,
            content={"error": "Gemini API key not configured", "code": "ANSWER_FAILED"},
        )

    # Context-aware retrieval: last 3 queries + current → Tavily; rerank uses current only
    previous_queries = [m["query"] for m in conv.get("messages", [])]
    context_query = build_context_query(query, previous_queries, max_previous=3)

    try:
        flow = run_search(
            query,
            limit=10,
            topic="general",
            days=None,
            search_query=context_query,
        )
    except Exception as e:
        logger.warning("Search failed: %s", e)
        return PrettyJSONResponse(
            status_code=502,
            content={"error": redact_message(str(e)), "code": "TAVILY_ERROR"},
        )

    if not flow.results:
        return PrettyJSONResponse(
            status_code=404,
            content={"error": "No results found", "code": "NO_RESULTS"},
        )

    top5 = flow.results[:5]
    sources = [(r.title, r.snippet) for r in top5]

    history = [(m["query"], m["answer"]) for m in conv.get("messages", [])]
    prompt = _build_message_prompt(query, history, sources)

    try:
        answer_text = gemini_generate(config.GEMINI_API_KEY, prompt, max_tokens=512)
    except Exception as e:
        logger.warning("Gemini failed: %s", e)
        return PrettyJSONResponse(
            status_code=502,
            content={"error": redact_message(str(e)), "code": "ANSWER_FAILED"},
        )

    citations = [
        Citation(title=r.title, url=r.url, score=r.score, rank=r.rank)
        for r in top5
    ]

    message_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    message_data = {
        "id": message_id,
        "query": query,
        "answer": answer_text,
        "citations": [c.model_dump() for c in citations],
        "results": [r.model_dump() for r in top5],
        "created_at": created_at,
    }

    messages = conv.get("messages", []) + [message_data]
    update_conversation(conversation_id, len(messages), messages)

    return Message(
        id=message_id,
        query=query,
        answer=answer_text,
        citations=citations,
        results=top5,
        created_at=created_at,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
    summary="Delete conversation",
    description="Permanently delete a conversation and all its messages.",
)
def delete_conversation_endpoint(
    conversation_id: str = Path(..., description="Conversation ID"),
):
    """Delete a conversation and all its messages."""
    err = _validate_conversation_id(conversation_id)
    if err is not None:
        return err
    deleted = delete_conversation(conversation_id)
    if not deleted:
        return PrettyJSONResponse(
            status_code=404,
            content={"error": "Conversation not found", "code": "CONVERSATION_NOT_FOUND"},
        )
    return Response(status_code=204)
