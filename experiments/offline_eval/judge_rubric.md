# Offline Judge Rubric (Blind A/B)

Use this rubric when scoring `answer_a` vs `answer_b` from `judge_packet.jsonl`.

## Rules

- Evaluate blind. Do not use mapping until judging is complete.
- Score both answers independently, then pick winner (`A`, `B`, or `Tie`).
- If both are factually poor, still choose the less harmful answer.

## Dimensions (1-5 each)

- **Relevance**
  - 5: Directly answers the question with high precision.
  - 3: Partially answers; some useful content.
  - 1: Mostly off-topic.

- **Groundedness**
  - 5: Claims are clearly supported by sources/citations.
  - 3: Some supported claims, some unsupported leaps.
  - 1: Mostly unsupported or speculative.

- **Clarity**
  - 5: Crisp, well-structured, easy to act on.
  - 3: Understandable but verbose/confusing in places.
  - 1: Hard to follow.

## Winner Decision

- Prefer the answer with higher combined score.
- If scores are close, prefer better groundedness over style.
- Mark `Tie` only when genuinely indistinguishable.

## Aggregation

- Human winner rate = `% queries won`.
- Human quality score (optional):
  - `0.4 * relevance + 0.4 * groundedness + 0.2 * clarity`.

Use `judge_scores_template.csv` to record final judgments.
