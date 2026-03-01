"""Retry HTTP calls on 429/503/500 with backoff."""
import time

import httpx

RETRY_STATUSES = (429, 503, 500)
MAX_ATTEMPTS_429 = 2  # 429 = rate limit: only 1 retry so we don't send 4 requests per message
MAX_ATTEMPTS_OTHER = 3  # 503/500: retry twice (1s, 2s) for transient errors
BACKOFF_429_SEC = 20


def retry_http(fn):
    """
    Call fn(). On httpx.HTTPStatusError:
    - 429: retry at most once after BACKOFF_429_SEC (2 attempts total).
    - 503/500: retry up to MAX_ATTEMPTS_OTHER with 1s, 2s backoff.
    Re-raise after last attempt or on other statuses.
    """
    last = None
    attempt = 0
    while True:
        try:
            return fn()
        except httpx.HTTPStatusError as e:
            last = e
            code = e.response.status_code
            if code not in RETRY_STATUSES:
                raise
            if code == 429:
                max_attempts = MAX_ATTEMPTS_429
            else:
                max_attempts = MAX_ATTEMPTS_OTHER
            if attempt >= max_attempts - 1:
                raise
            if code == 429:
                time.sleep(BACKOFF_429_SEC)
            else:
                time.sleep(2**attempt)
            attempt += 1
