"""Load API keys and app config from environment."""
import os

from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY: str | None = os.environ.get("TAVILY_API_KEY", "").strip() or None
COHERE_API_KEY: str | None = os.environ.get("COHERE_API_KEY", "").strip() or None
GEMINI_API_KEY: str | None = os.environ.get("GEMINI_API_KEY", "").strip() or None

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
if LOG_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR"):
    LOG_LEVEL = "INFO"

# CORS: comma-separated origins, or "*" for allow all. Empty = no CORS headers.
CORS_ORIGINS: list[str] = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "").strip().split(",") if o.strip()
]

# In-memory store caps (avoid unbounded growth)
MAX_CONVERSATIONS: int = max(1, int(os.environ.get("MAX_CONVERSATIONS", "5000")))
MAX_MESSAGES_PER_CONVERSATION: int = max(1, min(500, int(os.environ.get("MAX_MESSAGES_PER_CONVERSATION", "100"))))
