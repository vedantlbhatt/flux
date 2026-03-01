#!/usr/bin/env bash
# Flux API demo — run with server at http://localhost:8000
# Usage: ./demo.sh   or   bash demo.sh

set -e
BASE="${BASE_URL:-http://localhost:8000}"

echo "=============================================="
echo "  Flux API Demo (BASE=$BASE)"
echo "=============================================="
echo ""

echo "--- 1. Health ---"
curl -s "$BASE/health" | python3 -c "import sys,json; d=json.load(sys.stdin); print('  status:', d.get('status')); print('  tavily:', d.get('tavily_ready')); print('  cohere:', d.get('cohere_ready'))"
echo ""

echo "--- 2. Search (live web + rerank) ---"
curl -s "$BASE/search?q=HackIllinois+2026&limit=2" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('  query:', d.get('query'))
for r in d.get('results', [])[:2]:
    print('  -', r.get('title', '')[:55] + ('...' if len(r.get('title','')) > 55 else ''))
"
echo ""

echo "--- 3. Answer (synthesized + citations) ---"
curl -s "$BASE/answer?q=What+is+HackIllinois" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ans = (d.get('answer') or '')[:200]
print('  answer:', ans + ('...' if len(d.get('answer','')) > 200 else ''))
print('  citations:', len(d.get('citations', [])), 'sources')
"
echo ""

echo "--- 4. Stateful conversation (context-aware) ---"
CONV=$(curl -s -X POST "$BASE/conversations" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "  created conversation: $CONV"

echo "  Turn 1: \"What is HackIllinois?\""
curl -s -X POST "$BASE/conversations/$CONV/messages" -H "Content-Type: application/json" -d '{"query": "What is HackIllinois?"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
ans = (d.get('answer') or '')[:180]
print('  ->', ans + ('...' if len(d.get('answer','')) > 180 else ''))
"

echo "  Turn 2: \"When is it this year?\" (uses context)"
curl -s -X POST "$BASE/conversations/$CONV/messages" -H "Content-Type: application/json" -d '{"query": "When is it this year?"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
ans = (d.get('answer') or '')[:180]
print('  ->', ans + ('...' if len(d.get('answer','')) > 180 else ''))
"
echo ""

echo "--- 5. Error handling (invalid conversation ID) ---"
HTTP=$(curl -s -o /tmp/demo_err.json -w "%{http_code}" "$BASE/conversations/not-a-uuid")
BODY=$(python3 -c "import json; d=json.load(open('/tmp/demo_err.json')); print(d.get('code',''), d.get('error','')[:50])" 2>/dev/null || echo "400 INVALID_CONVERSATION_ID")
echo "  GET /conversations/not-a-uuid -> $HTTP ($BODY)"
echo ""

echo "=============================================="
echo "  Demo complete. Try the full API at $BASE/docs"
echo "=============================================="
