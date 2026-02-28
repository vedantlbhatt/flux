# flux

Search with the [Tavily Search API](https://docs.tavily.com/).

## Setup

1. Get an API key from [Tavily](https://docs.tavily.com/).
2. Copy `.env.example` to `.env` and set `TAVILY_API_KEY`.
3. Install and run:

```bash
bun install
bun run search "your query"
```

## Optional: Reranking

If you set `COHERE_API_KEY` in `.env`, search results are reranked by relevance using [Cohere Rerank](https://docs.cohere.com/docs/rerank). Get a key at [dashboard.cohere.com](https://dashboard.cohere.com/). Without it, results use Tavily’s default order.

## API server (Tier A)

Run the FastAPI server:

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
bun run api
```

Then open:
- **Health**: `curl http://localhost:8000/health`
- **Search**: `curl "http://localhost:8000/search?q=hello+world"`
- **Docs**: http://localhost:8000/docs

## Stateful conversations

Multi-turn context-aware search. Each message builds on previous turns.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/conversations` | Create a new conversation |
| `GET` | `/conversations` | List conversations (paginated: `page`, `page_size`) |
| `GET` | `/conversations/{id}` | Get full conversation with messages |
| `POST` | `/conversations/{id}/messages` | Add a query; returns synthesized answer with citations |
| `DELETE` | `/conversations/{id}` | Delete conversation (204 No Content) |

**Example — 3-turn conversation:**

```bash
# Create conversation
CONV=$(curl -s -X POST http://localhost:8000/conversations | jq -r '.id')

# Turn 1
curl -s -X POST "http://localhost:8000/conversations/$CONV/messages" \
  -H "Content-Type: application/json" -d '{"query": "what is SVB"}'

# Turn 2 (context-aware: knows SVB from turn 1)
curl -s -X POST "http://localhost:8000/conversations/$CONV/messages" \
  -H "Content-Type: application/json" -d '{"query": "why did it collapse"}'

# Turn 3 (knows SVB collapse context)
curl -s -X POST "http://localhost:8000/conversations/$CONV/messages" \
  -H "Content-Type: application/json" -d '{"query": "what was the federal response"}'
```

## Scripts

- `bun run api` — Start FastAPI server (Tavily + Cohere rerank)
- `bun run search <query>` — CLI web search (with optional Cohere rerank)
- `bun run lint` — Lint with oxlint
- `bun run lint:fix` — Lint and auto-fix

## API client

Use the client in your own code:

```ts
import { getTavilyApiKey } from "./src/config";
import { tavilySearch } from "./src/tavily";

const apiKey = getTavilyApiKey();
const res = await tavilySearch(apiKey, { query: "hello world", max_results: 5 });
console.log(res.results);
```