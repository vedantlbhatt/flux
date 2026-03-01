"""Sanitize error messages for production: redact secrets, generic 500 text."""
import re


def redact_message(text: str) -> str:
    """Redact API keys and tokens from error messages before returning to client or logging."""
    if not text:
        return ""
    # API key in URL query (?key=... or &key=...)
    text = re.sub(r"([?&]key=)[^&\s'\"\n]+", r"\1<redacted>", text, flags=re.IGNORECASE)
    # Bearer token
    text = re.sub(r"(Bearer\s+)[^\s]+", r"\1<redacted>", text, flags=re.IGNORECASE)
    # api_key= or apikey= in text
    text = re.sub(r"(api[_-]?key['\"]?\s*[:=]\s*['\"]?)[^'\"]+", r"\1<redacted>", text, flags=re.IGNORECASE)
    return text


def safe_internal_message() -> str:
    """Generic message for 500 responses. Do not leak exception details."""
    return "An internal error occurred."


def validation_error_message(exc: Exception) -> str:
    """User-safe validation error summary without file paths or internal details."""
    s = str(exc)
    # Remove file paths (e.g. "File \"/app/routers/search.py\", line 14")
    s = re.sub(r'File "[^"]+", line \d+[^\n]*', "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:500] if s else "Validation failed."
