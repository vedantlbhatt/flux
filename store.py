"""In-memory conversation store. Single source of truth for conversation data."""
from typing import Any

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


def create_conversation(conversation_id: str, created_at: str) -> dict[str, Any]:
    """Create and store a new conversation. Returns the created object."""
    conv = {
        "id": conversation_id,
        "created_at": created_at,
        "message_count": 0,
        "messages": [],
    }
    _conversations[conversation_id] = conv
    return conv


def update_conversation(conversation_id: str, message_count: int, messages: list[dict[str, Any]]) -> None:
    """Update a conversation's message count and messages list."""
    conv = _conversations.get(conversation_id)
    if conv:
        conv["message_count"] = message_count
        conv["messages"] = messages


def delete_conversation(conversation_id: str) -> bool:
    """Remove a conversation. Returns True if deleted, False if not found."""
    if conversation_id in _conversations:
        del _conversations[conversation_id]
        return True
    return False
