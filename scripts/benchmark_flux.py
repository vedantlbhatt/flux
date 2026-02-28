#!/usr/bin/env python3
"""Benchmark Flux API endpoints and summarize efficiency metrics."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import httpx


DEFAULT_QUERIES = [
    "latest US inflation rate 2026",
    "best open source LLM frameworks 2025",
    "what is retrieval augmented generation",
    "major AI model releases this month",
    "what happened at SVB collapse",
    "top Python web frameworks 2026",
    "latest NVIDIA earnings summary",
    "Fed interest rate decision this week",
    "what is MCP in AI tooling",
    "state of open-source agents 2026",
]


@dataclass
class EndpointRun:
    endpoint: str
    status_code: int
    elapsed_ms: float
    ok: bool
    error_code: str | None
    reranked: bool | None = None
    rank_changed_ratio: float | None = None
    citation_count: int | None = None


@dataclass
class Summary:
    endpoint: str
    requests: int
    success_rate: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    error_rate: float
    reranked_false_rate: float | None = None
    avg_rank_changed_ratio: float | None = None
    avg_citations: float | None = None


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(round((p / 100.0) * (len(ordered) - 1)))))
    return ordered[idx]


def load_queries(path: str | None) -> list[str]:
    if not path:
        return DEFAULT_QUERIES
    source = Path(path)
    raw = source.read_text(encoding="utf-8")
    queries = [line.strip() for line in raw.splitlines() if line.strip() and not line.strip().startswith("#")]
    return queries or DEFAULT_QUERIES


def _rank_changed_ratio(results: list[dict[str, Any]]) -> float:
    if not results:
        return 0.0
    changed = 0
    for r in results:
        if r.get("rank_original") != r.get("rank_flux"):
            changed += 1
    return changed / len(results)


def call_json(client: httpx.Client, method: str, url: str, **kwargs: Any) -> tuple[int, float, dict[str, Any]]:
    started = time.perf_counter()
    resp = client.request(method, url, **kwargs)
    elapsed_ms = (time.perf_counter() - started) * 1000
    try:
        data = resp.json()
    except Exception:
        data = {"error": resp.text, "code": None}
    return resp.status_code, elapsed_ms, data


def benchmark_search(client: httpx.Client, base_url: str, queries: list[str], loops: int) -> list[EndpointRun]:
    runs: list[EndpointRun] = []
    for _ in range(loops):
        for q in queries:
            status, elapsed, data = call_json(client, "GET", f"{base_url}/search", params={"q": q, "limit": 10})
            error_code = data.get("code") if isinstance(data, dict) else None
            results = data.get("results", []) if isinstance(data, dict) else []
            runs.append(
                EndpointRun(
                    endpoint="/search",
                    status_code=status,
                    elapsed_ms=elapsed,
                    ok=200 <= status < 300,
                    error_code=error_code,
                    reranked=data.get("reranked") if isinstance(data, dict) else None,
                    rank_changed_ratio=_rank_changed_ratio(results) if isinstance(results, list) else None,
                )
            )
    return runs


def benchmark_answer(client: httpx.Client, base_url: str, queries: list[str], loops: int) -> list[EndpointRun]:
    runs: list[EndpointRun] = []
    for _ in range(loops):
        for q in queries:
            status, elapsed, data = call_json(client, "GET", f"{base_url}/answer", params={"q": q})
            error_code = data.get("code") if isinstance(data, dict) else None
            citations = data.get("citations", []) if isinstance(data, dict) else []
            runs.append(
                EndpointRun(
                    endpoint="/answer",
                    status_code=status,
                    elapsed_ms=elapsed,
                    ok=200 <= status < 300,
                    error_code=error_code,
                    citation_count=len(citations) if isinstance(citations, list) else 0,
                )
            )
    return runs


def benchmark_conversation_messages(
    client: httpx.Client, base_url: str, queries: list[str], loops: int
) -> list[EndpointRun]:
    runs: list[EndpointRun] = []
    for _ in range(loops):
        status, _, data = call_json(client, "POST", f"{base_url}/conversations")
        if not (200 <= status < 300) or not isinstance(data, dict) or "id" not in data:
            runs.append(
                EndpointRun(
                    endpoint="/conversations/{id}/messages",
                    status_code=status,
                    elapsed_ms=0.0,
                    ok=False,
                    error_code=(data or {}).get("code") if isinstance(data, dict) else "UNKNOWN",
                )
            )
            continue
        conv_id = data["id"]
        for q in queries[: min(3, len(queries))]:
            status2, elapsed2, data2 = call_json(
                client,
                "POST",
                f"{base_url}/conversations/{conv_id}/messages",
                json={"query": q},
            )
            error_code = data2.get("code") if isinstance(data2, dict) else None
            citations = data2.get("citations", []) if isinstance(data2, dict) else []
            runs.append(
                EndpointRun(
                    endpoint="/conversations/{id}/messages",
                    status_code=status2,
                    elapsed_ms=elapsed2,
                    ok=200 <= status2 < 300,
                    error_code=error_code,
                    citation_count=len(citations) if isinstance(citations, list) else 0,
                )
            )
        client.delete(f"{base_url}/conversations/{conv_id}")
    return runs


def summarize(endpoint: str, runs: list[EndpointRun]) -> Summary:
    times = [r.elapsed_ms for r in runs]
    success = [r for r in runs if r.ok]
    errors = [r for r in runs if not r.ok]
    rerank_values = [r.reranked for r in runs if r.reranked is not None]
    rank_changed = [r.rank_changed_ratio for r in runs if r.rank_changed_ratio is not None]
    citations = [r.citation_count for r in runs if r.citation_count is not None]

    reranked_false_rate = None
    if rerank_values:
        reranked_false_rate = sum(1 for x in rerank_values if x is False) / len(rerank_values)

    return Summary(
        endpoint=endpoint,
        requests=len(runs),
        success_rate=(len(success) / len(runs)) if runs else 0.0,
        p50_ms=percentile(times, 50),
        p95_ms=percentile(times, 95),
        p99_ms=percentile(times, 99),
        avg_ms=(statistics.fmean(times) if times else 0.0),
        error_rate=(len(errors) / len(runs)) if runs else 0.0,
        reranked_false_rate=reranked_false_rate,
        avg_rank_changed_ratio=(statistics.fmean(rank_changed) if rank_changed else None),
        avg_citations=(statistics.fmean(citations) if citations else None),
    )


def write_json_report(path: Path, summaries: list[Summary], runs: list[EndpointRun], meta: dict[str, Any]) -> None:
    payload = {
        "meta": meta,
        "summaries": [asdict(s) for s in summaries],
        "runs": [asdict(r) for r in runs],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Flux API efficiency metrics.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Flux API base URL")
    parser.add_argument("--queries-file", default=None, help="Optional newline-delimited queries file")
    parser.add_argument("--loops", type=int, default=2, help="How many passes over query set")
    parser.add_argument("--output", default="reports/flux_benchmark.json", help="Output JSON path")
    parser.add_argument(
        "--skip-answer", action="store_true", help="Skip /answer and /conversations/{id}/messages benchmarks"
    )
    args = parser.parse_args()

    queries = load_queries(args.queries_file)
    all_runs: list[EndpointRun] = []

    with httpx.Client(timeout=60.0) as client:
        health_status, _, health = call_json(client, "GET", f"{args.base_url}/health")
        if not (200 <= health_status < 300):
            raise RuntimeError(f"Health check failed: {health_status} {health}")

        search_runs = benchmark_search(client, args.base_url, queries, loops=args.loops)
        all_runs.extend(search_runs)

        if not args.skip_answer:
            answer_runs = benchmark_answer(client, args.base_url, queries[: min(5, len(queries))], loops=args.loops)
            conv_runs = benchmark_conversation_messages(
                client, args.base_url, queries[: min(5, len(queries))], loops=max(1, args.loops // 2)
            )
            all_runs.extend(answer_runs)
            all_runs.extend(conv_runs)

    grouped: dict[str, list[EndpointRun]] = {}
    for run in all_runs:
        grouped.setdefault(run.endpoint, []).append(run)

    summaries = [summarize(endpoint, runs) for endpoint, runs in sorted(grouped.items())]
    meta = {"base_url": args.base_url, "queries_count": len(queries), "loops": args.loops}
    output_path = Path(args.output)
    write_json_report(output_path, summaries, all_runs, meta)

    print(f"Benchmark complete. Report written to {output_path}")
    for summary in summaries:
        print(
            f"{summary.endpoint}: p50={summary.p50_ms:.1f}ms p95={summary.p95_ms:.1f}ms "
            f"success={summary.success_rate:.2%} error={summary.error_rate:.2%}"
        )


if __name__ == "__main__":
    main()
