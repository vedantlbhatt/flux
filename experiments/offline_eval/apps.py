"""Comparable RAG app implementations for offline evaluation."""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass

import httpx

import config
from services.gemini_service import MODEL, gemini_generate
from services.tavily import tavily_search


@dataclass
class Citation:
    title: str
    url: str
    score: float
    rank: int


@dataclass
class AppResult:
    system: str
    success: bool
    error: str | None
    answer: str
    citations: list[dict]
    retrieval_latency_ms: float
    synthesis_latency_ms: float
    total_latency_ms: float

    def to_dict(self) -> dict:
        return asdict(self)


def _build_prompt(query: str, sources: list[tuple[str, str]]) -> str:
    parts = [
        "Answer the following question using only the sources provided.",
        "Keep the answer concise and practical.",
        "Cite sources inline using [1], [2], etc.",
        "",
        f"Question: {query}",
        "",
        "Sources:",
    ]
    for i, (title, snippet) in enumerate(sources, start=1):
        parts.append(f"[{i}] {title}")
        parts.append(snippet)
        parts.append("")
    return "\n".join(parts).strip()


def _synthesize(query: str, sources: list[tuple[str, str]]) -> tuple[str, float]:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("Missing GEMINI_API_KEY for synthesis")
    prompt = _build_prompt(query, sources)
    attempts = 4
    start_total = time.perf_counter()
    backoff_seconds = 1.5

    for attempt in range(1, attempts + 1):
        try:
            answer = gemini_generate(config.GEMINI_API_KEY, prompt, max_tokens=512)
            elapsed_ms = (time.perf_counter() - start_total) * 1000
            return answer, elapsed_ms
        except httpx.HTTPStatusError as e:
            code = e.response.status_code if e.response is not None else 0
            if attempt < attempts and code in (429, 503):
                time.sleep(backoff_seconds)
                backoff_seconds *= 1.8
                continue
            raise


def _extractive_answer(sources: list[tuple[str, str]], max_sources: int = 3) -> str:
    """Fallback answer mode that avoids LLM synthesis rate limits."""
    selected = sources[:max_sources]
    chunks = []
    for i, (title, snippet) in enumerate(selected, start=1):
        clean = " ".join(snippet.split())
        chunks.append(f"[{i}] {title}: {clean[:220]}")
    return " ".join(chunks).strip()


def _safe_error_message(error: Exception) -> str:
    """Redact sensitive tokens from provider errors before writing artifacts."""
    text = str(error)
    text = re.sub(r"([?&]key=)[^&\\s'\"\\n]+", r"\1<redacted>", text)
    return text


class BaselineRAGApp:
    """Baseline app: Tavily retrieval in native order + shared synthesis."""

    name = "baseline"

    def __init__(self, use_synthesis: bool = True):
        self.use_synthesis = use_synthesis

    def answer(self, query: str) -> AppResult:
        total_start = time.perf_counter()
        if not config.TAVILY_API_KEY:
            return AppResult(self.name, False, "Missing TAVILY_API_KEY", "", [], 0.0, 0.0, 0.0)

        try:
            retrieval_start = time.perf_counter()
            data = tavily_search(config.TAVILY_API_KEY, query, max_results=10, topic="general")
            retrieval_ms = (time.perf_counter() - retrieval_start) * 1000
            results = data.get("results") or []
            top5 = results[:5]
            sources = [(r.get("title", ""), r.get("content", "")[:300]) for r in top5]
            citations = [
                Citation(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    score=float(r.get("score", 0.0) or 0.0),
                    rank=i + 1,
                )
                for i, r in enumerate(top5)
            ]
            if self.use_synthesis:
                answer_text, synthesis_ms = _synthesize(query, sources)
            else:
                answer_text = _extractive_answer(sources)
                synthesis_ms = 0.0
            total_ms = (time.perf_counter() - total_start) * 1000
            return AppResult(
                system=self.name,
                success=True,
                error=None,
                answer=answer_text,
                citations=[asdict(c) for c in citations],
                retrieval_latency_ms=retrieval_ms,
                synthesis_latency_ms=synthesis_ms,
                total_latency_ms=total_ms,
            )
        except Exception as e:
            total_ms = (time.perf_counter() - total_start) * 1000
            return AppResult(self.name, False, _safe_error_message(e), "", [], 0.0, 0.0, total_ms)


class FluxRAGApp:
    """Flux app: retrieval through Flux /search endpoint + shared synthesis."""

    name = "flux"

    def __init__(self, base_url: str = "http://127.0.0.1:8000", use_synthesis: bool = True):
        self.base_url = base_url.rstrip("/")
        self.use_synthesis = use_synthesis

    def answer(self, query: str) -> AppResult:
        total_start = time.perf_counter()
        try:
            retrieval_start = time.perf_counter()
            with httpx.Client(timeout=60.0) as client:
                resp = client.get(f"{self.base_url}/search", params={"q": query, "limit": 10})
            retrieval_ms = (time.perf_counter() - retrieval_start) * 1000
            if resp.status_code >= 400:
                return AppResult(self.name, False, f"/search failed: {resp.status_code}", "", [], retrieval_ms, 0.0, retrieval_ms)

            payload = resp.json()
            results = payload.get("results") or []
            top5 = results[:5]
            sources = [(r.get("title", ""), r.get("snippet", "")[:300]) for r in top5]
            citations = [
                Citation(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    score=float(r.get("score", 0.0) or 0.0),
                    rank=int(r.get("rank", i + 1)),
                )
                for i, r in enumerate(top5)
            ]

            if self.use_synthesis:
                answer_text, synthesis_ms = _synthesize(query, sources)
            else:
                answer_text = _extractive_answer(sources)
                synthesis_ms = 0.0
            total_ms = (time.perf_counter() - total_start) * 1000
            return AppResult(
                system=self.name,
                success=True,
                error=None,
                answer=answer_text,
                citations=[asdict(c) for c in citations],
                retrieval_latency_ms=retrieval_ms,
                synthesis_latency_ms=synthesis_ms,
                total_latency_ms=total_ms,
            )
        except Exception as e:
            total_ms = (time.perf_counter() - total_start) * 1000
            return AppResult(self.name, False, _safe_error_message(e), "", [], 0.0, 0.0, total_ms)


def synthesis_model_name() -> str:
    return MODEL
