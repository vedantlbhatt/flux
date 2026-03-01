"""In-memory conversation store. Single source of truth for conversation data.

Only this module reads/writes the store. Resets on server restart; no persistence.
"""
from typing import Any

# conversation_id -> { id, created_at, message_count, messages }
_conversations: dict[str, dict[str, Any]] = {}


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    """Retrieve a conversation by ID. Returns None if not found."""
    return _conversations.get(conversation_id)


def list_conversations(page: int = 1, page_size: int = 20) -> tuple[list[dict[str, Any]], int]:
    """
    List conversations sorted by created_at descending.
    Returns (paginated_conversations, total_count).
    """
    all_convs = list(_conversations.values())
    all_convs.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    total = len(all_convs)
    start = (page - 1) * page_size
    end = start + page_size
    return all_convs[start:end], total


def _evict_oldest_if_over_cap() -> None:
    """If over MAX_CONVERSATIONS, remove oldest by created_at."""
    if len(_conversations) <= config.MAX_CONVERSATIONS:
        return
    by_date = sorted(_conversations.items(), key=lambda x: x[1].get("created_at", ""))
    to_remove = len(_conversations) - config.MAX_CONVERSATIONS
    for i in range(to_remove):
        if i < len(by_date):
            del _conversations[by_date[i][0]]


def create_conversation(conversation_id: str, created_at: str) -> dict[str, Any]:
    """Create and store a new conversation. Evicts oldest if over cap. Returns the created object."""
    _evict_oldest_if_over_cap()
    conv = {
        "id": conversation_id,
        "created_at": created_at,
        "message_count": 0,
        "messages": [],
    }
    _conversations[conversation_id] = conv
    return conv


def update_conversation(conversation_id: str, message_count: int, messages: list[dict[str, Any]]) -> None:
    """Update a conversation's message count and messages list. Caps messages at MAX_MESSAGES_PER_CONVERSATION."""
    conv = _conversations.get(conversation_id)
    if conv:
        capped = messages[-config.MAX_MESSAGES_PER_CONVERSATION:] if len(messages) > config.MAX_MESSAGES_PER_CONVERSATION else messages
        conv["message_count"] = len(capped)
        conv["messages"] = capped


def delete_conversation(conversation_id: str) -> bool:
    """Remove a conversation. Returns True if deleted, False if not found."""
    if conversation_id in _conversations:
        del _conversations[conversation_id]
        return True
    return False
