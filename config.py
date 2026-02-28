"""Load API keys from environment."""
import os

from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY: str | None = os.environ.get("TAVILY_API_KEY", "").strip() or None
COHERE_API_KEY: str | None = os.environ.get("COHERE_API_KEY", "").strip() or None
OPENAI_API_KEY: str | None = os.environ.get("OPENAI_API_KEY", "").strip() or None
