#!/usr/bin/env python3
"""Run offline A/B evaluation for baseline vs Flux RAG apps."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.offline_eval.apps import BaselineRAGApp, FluxRAGApp, synthesis_model_name


def load_dataset(path: Path) -> list[dict]:
    items: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        items.append(json.loads(line))
    return items


def keyword_recall(answer: str, expected_keywords: list[str]) -> float | None:
    if not expected_keywords:
        return None
    haystack = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in haystack)
    return hits / len(expected_keywords)


def build_blind_judging_files(run: dict, output_dir: Path) -> None:
    rnd = random.Random(42)
    packet_rows: list[dict] = []
    mapping_rows: list[dict] = []

    for item in run["items"]:
        query_id = item["id"]
        baseline = item["results"].get("baseline")
        flux = item["results"].get("flux")
        if not baseline or not flux:
            continue

        if rnd.random() < 0.5:
            a_label, b_label = "baseline", "flux"
            a_result, b_result = baseline, flux
        else:
            a_label, b_label = "flux", "baseline"
            a_result, b_result = flux, baseline

        packet_rows.append(
            {
                "query_id": query_id,
                "query": item["query"],
                "expected_keywords": ", ".join(item["expected_keywords"]),
                "answer_a": a_result["answer"],
                "answer_b": b_result["answer"],
            }
        )
        mapping_rows.append({"query_id": query_id, "A": a_label, "B": b_label})

    packet_path = output_dir / "judge_packet.jsonl"
    mapping_path = output_dir / "judge_packet_mapping_private.json"
    csv_path = output_dir / "judge_scores_template.csv"

    with packet_path.open("w", encoding="utf-8") as f:
        for row in packet_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    mapping_path.write_text(json.dumps(mapping_rows, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query_id",
                "evaluator",
                "winner",
                "answer_a_relevance_1_5",
                "answer_b_relevance_1_5",
                "answer_a_groundedness_1_5",
                "answer_b_groundedness_1_5",
                "answer_a_clarity_1_5",
                "answer_b_clarity_1_5",
                "notes",
            ],
        )
        writer.writeheader()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run offline baseline vs Flux evaluation.")
    parser.add_argument(
        "--dataset",
        default="experiments/offline_eval/dataset/questions.jsonl",
        help="Path to JSONL dataset",
    )
    parser.add_argument(
        "--systems",
        default="baseline,flux",
        help="Comma-separated systems to run (baseline,flux)",
    )
    parser.add_argument(
        "--flux-base-url",
        default="http://127.0.0.1:8000",
        help="Flux API base URL for flux system",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="Optional cap for dataset items (0 = all)",
    )
    parser.add_argument(
        "--output",
        default="experiments/offline_eval/outputs/run_latest.json",
        help="Output run JSON file",
    )
    parser.add_argument(
        "--sleep-between",
        type=float,
        default=0.5,
        help="Seconds to sleep between individual app calls (reduce provider rate limits)",
    )
    parser.add_argument(
        "--skip-synthesis",
        action="store_true",
        help="Disable LLM synthesis and use extractive answer mode for stable offline eval",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    items = load_dataset(dataset_path)
    if args.max_items > 0:
        items = items[: args.max_items]

    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    runners = {}
    if "baseline" in systems:
        runners["baseline"] = BaselineRAGApp(use_synthesis=not args.skip_synthesis)
    if "flux" in systems:
        runners["flux"] = FluxRAGApp(base_url=args.flux_base_url, use_synthesis=not args.skip_synthesis)

    run = {
        "meta": {
            "run_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset_path": str(dataset_path),
            "systems": list(runners.keys()),
            "flux_base_url": args.flux_base_url,
            "synthesis_model": ("extractive-only" if args.skip_synthesis else synthesis_model_name()),
            "skip_synthesis": args.skip_synthesis,
        },
        "items": [],
    }

    for item in items:
        row = {
            "id": item["id"],
            "query": item["query"],
            "category": item.get("category", "unknown"),
            "expected_keywords": item.get("expected_keywords", []),
            "results": {},
        }
        for name, app in runners.items():
            result = app.answer(item["query"]).to_dict()
            result["keyword_recall"] = keyword_recall(result["answer"], row["expected_keywords"]) if result["success"] else None
            row["results"][name] = result
            print(f"[{name}] {item['id']} success={result['success']} latency={result['total_latency_ms']:.1f}ms")
            if args.sleep_between > 0:
                time.sleep(args.sleep_between)
        run["items"].append(row)

    output_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    build_blind_judging_files(run, output_path.parent)
    print(f"\nRun complete: {output_path}")
    print(f"Blind judging packet: {output_path.parent / 'judge_packet.jsonl'}")
    print(f"Scoring template: {output_path.parent / 'judge_scores_template.csv'}")


if __name__ == "__main__":
    main()
