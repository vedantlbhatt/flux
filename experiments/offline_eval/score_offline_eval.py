#!/usr/bin/env python3
"""Compute presentation-ready scorecard from offline evaluation run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(round((p / 100.0) * (len(ordered) - 1)))))
    return ordered[idx]


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_metrics(run: dict, system: str) -> dict:
    rows = [item["results"][system] for item in run["items"] if system in item["results"]]
    success_rows = [r for r in rows if r.get("success")]
    latencies = [float(r.get("total_latency_ms", 0.0)) for r in success_rows]
    recalls = [float(r["keyword_recall"]) for r in success_rows if r.get("keyword_recall") is not None]
    citations = [len(r.get("citations", [])) for r in success_rows]

    return {
        "system": system,
        "requests": len(rows),
        "success_rate": (len(success_rows) / len(rows)) if rows else 0.0,
        "error_rate": ((len(rows) - len(success_rows)) / len(rows)) if rows else 0.0,
        "avg_latency_ms": mean(latencies),
        "p95_latency_ms": percentile(latencies, 95),
        "avg_keyword_recall": mean(recalls),
        "avg_citations": mean(citations),
    }


def apply_score_formula(metrics: dict, best_latency_ms: float) -> dict:
    quality_score = (metrics["avg_keyword_recall"] * 70.0) + (min(metrics["avg_citations"] / 5.0, 1.0) * 30.0)
    reliability_score = metrics["success_rate"] * 100.0
    latency_score = (best_latency_ms / metrics["avg_latency_ms"] * 100.0) if metrics["avg_latency_ms"] > 0 else 0.0
    latency_score = min(latency_score, 100.0)
    final_score = (0.6 * quality_score) + (0.2 * reliability_score) + (0.2 * latency_score)

    out = dict(metrics)
    out["quality_score_100"] = quality_score
    out["reliability_score_100"] = reliability_score
    out["latency_score_100"] = latency_score
    out["final_score_100"] = final_score
    return out


def markdown_report(scored: list[dict], run_path: str) -> str:
    lines = [
        "# Offline Eval Scorecard",
        "",
        f"- Run file: `{run_path}`",
        "",
        "## Formula",
        "",
        "- `quality_score = 70% * avg_keyword_recall + 30% * citation_coverage`",
        "- `reliability_score = success_rate * 100`",
        "- `latency_score = (best_avg_latency / system_avg_latency) * 100`",
        "- `final_score = 60% quality + 20% reliability + 20% latency`",
        "",
        "## Results",
        "",
        "| System | Success | Avg Latency (ms) | P95 (ms) | Keyword Recall | Avg Citations | Final Score |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sorted(scored, key=lambda x: x["final_score_100"], reverse=True):
        lines.append(
            f"| {r['system']} | {r['success_rate']:.1%} | {r['avg_latency_ms']:.1f} | {r['p95_latency_ms']:.1f} | "
            f"{r['avg_keyword_recall']:.3f} | {r['avg_citations']:.2f} | {r['final_score_100']:.2f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate scorecard from offline eval run.")
    parser.add_argument("--run", default="experiments/offline_eval/outputs/run_latest.json", help="Run JSON path")
    parser.add_argument(
        "--output-json",
        default="experiments/offline_eval/outputs/scorecard_latest.json",
        help="Output scorecard JSON path",
    )
    parser.add_argument(
        "--output-md",
        default="experiments/offline_eval/outputs/scorecard_latest.md",
        help="Output scorecard markdown path",
    )
    args = parser.parse_args()

    run = json.loads(Path(args.run).read_text(encoding="utf-8"))
    systems = run["meta"]["systems"]
    metrics = [compute_metrics(run, system) for system in systems]
    best_latency = min((m["avg_latency_ms"] for m in metrics if m["avg_latency_ms"] > 0), default=1.0)
    scored = [apply_score_formula(m, best_latency) for m in metrics]

    out_json = {
        "meta": run["meta"],
        "formula": {
            "quality_weight": 0.6,
            "reliability_weight": 0.2,
            "latency_weight": 0.2,
            "quality_components": {
                "keyword_recall_weight": 0.7,
                "citation_coverage_weight": 0.3,
            },
        },
        "systems": scored,
    }
    Path(args.output_json).write_text(json.dumps(out_json, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(markdown_report(scored, args.run), encoding="utf-8")
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")


if __name__ == "__main__":
    main()
