"""GET /contents — clean extracted text from specific URLs."""
import logging
import re
from urllib.parse import urlparse

from fastapi import APIRouter, Query

import config
from models.contents import PageContent
from models.error import ErrorResponse
from services.tavily_extract import tavily_extract
from utils.safe_errors import redact_message
from utils.responses import PrettyJSONResponse

router = APIRouter(tags=["contents"])
logger = logging.getLogger(__name__)


def _word_count(text: str) -> int:
    return len(text.split())


def _clean_content(raw: str, url: str = "") -> str:
    """Strip leading boilerplate: nav, ToC, language links, tools. Start from main body."""
    lines = raw.splitlines()
    out: list[str] = []
    past_boilerplate = False
    is_wikipedia = "wikipedia.org" in url

    for line in lines:
        s = line.strip()
        if not s:
            if out:
                out.append("")
            continue

        # Wikipedia: skip everything until "From Wikipedia, the free encyclopedia"
        if is_wikipedia:
            if "From Wikipedia, the free encyclopedia" in s:
                past_boilerplate = True
            if past_boilerplate:
                out.append(s)
            continue

        if not past_boilerplate:
            if s.startswith("["):
                continue
            if re.match(r"^##\s+Contents?\s*$", s) or (
                s.startswith("* [") and ("](#" in s or "](#)" in s)
            ):
                continue
            if s.startswith("* [") and "wikipedia.org" in s and "/wiki/" in s:
                continue
            if s in ("Tools", "Actions", "General", "Print/export", "In other projects", "Appearance"):
                continue
            if s.startswith("* [") and ("Edit" in s or "Read" in s or "Talk" in s):
                continue

        past_boilerplate = True
        out.append(s)

    return "\n".join(out).strip()


@router.get(
    "/contents",
    response_model=list[PageContent],
    response_class=PrettyJSONResponse,
    responses={
        400: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
def contents(
    urls: str = Query(..., description="Comma-separated list of URLs (max 10)"),
):
    if not urls or not urls.strip():
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "Missing required urls parameter", "code": "MISSING_URLS"},
        )

    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    if len(url_list) > 10:
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "Maximum 10 URLs allowed", "code": "TOO_MANY_URLS"},
        )
    if not url_list:
        return PrettyJSONResponse(
            status_code=400,
            content={"error": "At least one URL required", "code": "MISSING_URLS"},
        )

    for u in url_list:
        try:
            parsed = urlparse(u)
            if parsed.scheme not in ("http", "https"):
                return PrettyJSONResponse(
                    status_code=400,
                    content={"error": "URLs must use http or https", "code": "INVALID_URLS"},
                )
            if not parsed.netloc or not parsed.netloc.strip():
                return PrettyJSONResponse(
                    status_code=400,
                    content={"error": "Invalid URL: missing host", "code": "INVALID_URLS"},
                )
        except Exception:
            return PrettyJSONResponse(
                status_code=400,
                content={"error": "Invalid URL format", "code": "INVALID_URLS"},
            )

    if not config.TAVILY_API_KEY:
        return PrettyJSONResponse(
            status_code=502,
            content={"error": "Tavily API key not configured", "code": "TAVILY_ERROR"},
        )

    try:
        data = tavily_extract(config.TAVILY_API_KEY, url_list)
    except Exception as e:
        logger.warning("Tavily extract failed: %s", e)
        return PrettyJSONResponse(
            status_code=502,
            content={"error": redact_message(str(e)), "code": "TAVILY_ERROR"},
        )

    results = data.get("results") or []
    by_url = {r.get("url", ""): r for r in results}

    out: list[PageContent] = []
    for url in url_list:
        if url in by_url:
            r = by_url[url]
            raw = r.get("raw_content", "")
            cleaned = _clean_content(raw, url)
            out.append(
                PageContent(
                    url=url,
                    title=_extract_title(raw),
                    content=cleaned,
                    word_count=_word_count(cleaned),
                    success=True,
                )
            )
        else:
            out.append(
                PageContent(url=url, title="", content="", word_count=0, success=False)
            )

    return out


def _extract_title(content: str) -> str:
    """Extract title: prefer H1 (# ), then H2 (## ), then first substantial line."""
    if not content:
        return ""

    h2_fallback = ""
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # Prefer H1 (# ) only; skip ## Contents, use other H2s as fallback
        if line.startswith("# ") or line.startswith("#\t"):
            m = re.match(r"^#\s+(.+)$", line)
            if m:
                t = m.group(1).strip()
                if t and len(t) > 2:
                    return t[:200]
        if line.startswith("## ") and not re.match(r"^##\s+Contents?\s*$", line):
            m = re.match(r"^##\s+(.+)$", line)
            if m and not h2_fallback:
                h2_fallback = m.group(1).strip()[:200]
        # Skip boilerplate: [Jump...], ## Contents, ToC (* [1 History](#...)), link lines
        if re.match(r"^##\s+Contents?\s*$", line):
            continue
        if line.startswith("["):
            continue
        if line.startswith("* [") and ("](#" in line or "](http" in line):
            continue
        if len(line) < 4:
            continue
        # First substantial line
        return line[:200]

    return h2_fallback or content[:80].strip()
