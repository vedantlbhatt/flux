"""Retry HTTP calls on 429/503/500 with exponential backoff."""
import time

import httpx

RETRY_STATUSES = (429, 503, 500)
MAX_ATTEMPTS = 3


def retry_http(fn):
    """
    Call fn(). On httpx.HTTPStatusError with status in 429/503/500,
    retry up to MAX_ATTEMPTS with exponential backoff (1s, 2s, 4s).
    Re-raise after last attempt or on other statuses.
    """
    last = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            return fn()
        except httpx.HTTPStatusError as e:
            last = e
            if e.response.status_code in RETRY_STATUSES and attempt < MAX_ATTEMPTS - 1:
                time.sleep(2**attempt)
                continue
            raise
    if last is not None:
        raise last
    raise RuntimeError("retry_http unreachable")
