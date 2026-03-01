# Offline A/B Evaluation: Baseline vs Flux

This folder creates two comparable RAG applications:

- `baseline`: Tavily retrieval in native order + shared synthesis
- `flux`: Flux `/search` retrieval + shared synthesis

Both use the same synthesis model and prompt style so retrieval quality is the main changing variable.

## Files

- `dataset/questions.jsonl` — offline query set with expected keywords
- `run.schema.json` — JSON schema for run artifacts
- `run_offline_eval.py` — executes both systems and writes a run file
- `score_offline_eval.py` — computes scorecard JSON + Markdown
- `judge_rubric.md` — human blind judging rubric

## Run

1. Start Flux API:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

2. Execute offline eval:

```bash
python experiments/offline_eval/run_offline_eval.py --output experiments/offline_eval/outputs/run_latest.json
```

If you hit provider rate limits, run stable retrieval-focused mode:

```bash
python experiments/offline_eval/run_offline_eval.py --skip-synthesis --sleep-between 0.2 --output experiments/offline_eval/outputs/run_latest.json
```

3. Build scorecard:

```bash
python experiments/offline_eval/score_offline_eval.py --run experiments/offline_eval/outputs/run_latest.json
```

## Outputs

- `outputs/run_latest.json` — full run artifact (matches `run.schema.json`)
- `outputs/judge_packet.jsonl` — blind A/B packet for human judges
- `outputs/judge_packet_mapping_private.json` — private mapping, reveal only after judging
- `outputs/judge_scores_template.csv` — manual scoring sheet
- `outputs/scorecard_latest.json` — metric + weighted score payload
- `outputs/scorecard_latest.md` — presentation-ready summary
