# Offline Eval Scorecard

- Run file: `experiments/offline_eval/outputs/run_latest.json`

## Formula

- `quality_score = 70% * avg_keyword_recall + 30% * citation_coverage`
- `reliability_score = success_rate * 100`
- `latency_score = (best_avg_latency / system_avg_latency) * 100`
- `final_score = 60% quality + 20% reliability + 20% latency`

## Results

| System | Success | Avg Latency (ms) | P95 (ms) | Keyword Recall | Avg Citations | Final Score |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 100.0% | 908.7 | 1494.2 | 0.800 | 5.00 | 91.60 |
| flux | 100.0% | 2009.1 | 2985.2 | 0.733 | 5.00 | 77.85 |
