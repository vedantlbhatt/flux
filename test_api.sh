#!/bin/bash
# Test all Flux API endpoints. Run with: ./test_api.sh
# Ensure the API is running first: bun run api

set -e
API="http://localhost:8000"

echo "=== 1. Health ==="
curl -s "$API/health" || { echo "FAIL: Is the server running? Try: bun run api"; exit 1; }
echo -e "\n"

echo "=== 2. Create conversation ==="
RESP=$(curl -s -X POST "$API/conversations")
echo "$RESP"

# Extract ID without jq (works on any system)
CONV=$(echo "$RESP" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$CONV" ]; then
  echo "FAIL: Could not parse conversation ID. Response above."
  exit 1
fi
echo "Created ID: $CONV"
echo ""

echo "=== 3. List conversations ==="
curl -s "$API/conversations?page=1&page_size=10"
echo -e "\n"

echo "=== 4. Get conversation ==="
curl -s "$API/conversations/$CONV"
echo -e "\n"

echo "=== 5. Add message ==="
curl -s -X POST "$API/conversations/$CONV/messages" \
  -H "Content-Type: application/json" \
  -d '{"query": "what is SVB"}'
echo -e "\n"

echo "=== 6. Get conversation (with messages) ==="
curl -s "$API/conversations/$CONV"
echo -e "\n"

echo "=== 7. Delete conversation ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$API/conversations/$CONV")
echo "Status: $STATUS (expect 204)"
echo ""

echo "Done."
