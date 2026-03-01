"""Gemini API client for answer synthesis. Retries on 429/503/500."""
import logging

import httpx

import config
from utils.retry import retry_http

logger = logging.getLogger(__name__)

MODEL = config.GEMINI_MODEL  # for response metadata and experiments


def _gemini_url() -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent"


def gemini_generate(api_key: str, prompt: str, *, max_tokens: int = 512) -> str:
    """
    Call Gemini generateContent. Returns the generated text.
    Raises httpx.HTTPStatusError on failure.
    """
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("Gemini prompt must not be empty")

    url = f"{_gemini_url()}?key={api_key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.3,
        },
    }
    with httpx.Client(timeout=60.0) as client:
        def do_request():
            resp = client.post(url, json=body)
            if not resp.is_success:
                try:
                    err_body = resp.text
                    if err_body:
                        logger.warning("Gemini API error response: %s", err_body[:500])
                except Exception:
                    pass
            resp.raise_for_status()
            return resp.json()
        data = retry_http(do_request)
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts") or []
    if not parts:
        raise ValueError("Gemini returned no content")
    return parts[0].get("text", "").strip()
