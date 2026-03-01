"""Load API keys from environment.

All keys come from config only; no hardcoded keys elsewhere.
Empty or whitespace-only env values are treated as unset (None).
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Tavily: search + extract; required for /search, /answer, /contents
TAVILY_API_KEY: str | None = os.environ.get("TAVILY_API_KEY", "").strip() or None
# Cohere: reranking; optional — degrades to Tavily order if unset or on failure
COHERE_API_KEY: str | None = os.environ.get("COHERE_API_KEY", "").strip() or None
# Gemini: answer synthesis for /answer and conversation messages
GEMINI_API_KEY: str | None = os.environ.get("GEMINI_API_KEY", "").strip() or None
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

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
