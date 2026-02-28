"""Gemini API client for answer synthesis."""
import httpx

MODEL = "gemini-2.5-flash-lite"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def gemini_generate(api_key: str, prompt: str, *, max_tokens: int = 512) -> str:
    """
    Call Gemini generateContent. Returns the generated text.
    Raises httpx.HTTPStatusError on failure.
    """
    url = f"{GEMINI_URL}?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.3,
        },
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts") or []
    if not parts:
        raise ValueError("Gemini returned no content")
    return parts[0].get("text", "").strip()
