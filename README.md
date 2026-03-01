# Flux

Live web search API with semantic reranking and multi-turn conversations. Query the open web, get reranked results or a synthesized answer with citations—all over HTTP.

**Tech stack:** Python 3.x, FastAPI, Tavily Search API, Cohere Rerank API, Google Gemini (answer synthesis). In-memory conversation store. No database required.

---

## Setup

1. Get an API key from [Tavily](https://docs.tavily.com/).
2. Copy `.env.example` to `.env` and set `TAVILY_API_KEY`.
3. For **answer** and **conversations** endpoints, set `GEMINI_API_KEY` in `.env` ([get one](https://aistudio.google.com/app/apikey)).
4. Optional: set `COHERE_API_KEY` for reranking ([dashboard.cohere.com](https://dashboard.cohere.com/)).

```bash
bun install
bun run search "your query"
```

## API server

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
bun run api
```

Server runs at **http://localhost:8000**. Interactive API docs (Swagger UI): **http://localhost:8000/docs**. Import **http://localhost:8000/openapi.json** into Postman or Insomnia for a ready-made request collection.

### Quick test (cURL)

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/search?q=hello+world&limit=5"
curl "http://localhost:8000/answer?q=What+is+FastAPI"
curl "http://localhost:8000/contents?urls=https://example.com"
```

**Test POST + state (create conversation, add one message):**

```bash
CONV=$(curl -s -X POST http://localhost:8000/conversations | jq -r '.id')
curl -s -X POST "http://localhost:8000/conversations/$CONV/messages" \
  -H "Content-Type: application/json" -d '{"query": "What is Python?"}'
```

## API reference

All endpoints return JSON. Errors use a consistent shape: `{"error": "<message>", "code": "<CODE>"}` with appropriate HTTP status (400, 404, 413, 502, etc.).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health; reports Tavily/Cohere readiness |
| `GET` | `/search` | Live web search. Query: `q`, optional `limit` (1–20), `topic` (news/general), `days` |
| `GET` | `/answer` | Synthesized answer from live search + citations. Query: `q`, optional `topic`, `days` |
| `GET` | `/contents` | Extracted text from URLs. Query: `urls` (comma-separated, max 10) |
| `POST` | `/conversations` | Create a conversation (returns `id`, use for messages) |
| `GET` | `/conversations` | List conversations; pagination: `page`, `page_size` (1–100) |
| `GET` | `/conversations/{id}` | Get one conversation with all messages (UUID required) |
| `POST` | `/conversations/{id}/messages` | Add a query; runs context-aware search + synthesis (body: `{"query": "..."}`) |
| `DELETE` | `/conversations/{id}` | Delete a conversation (204 No Content) |

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

---

## HackIllinois — Best Web API (criteria checklist)

- **Submission requirements**
  - ✅ API with multiple endpoints that perform valuable actions (live search, synthesized answers, URL extraction, stateful conversations).
  - ✅ Queryable over HTTP; testable with cURL/Postman. Operational on localhost.
  - ✅ Documentation in this README plus **hosted interactive docs** at `http://localhost:8000/docs` when the server is running (Swagger UI with try-it-out).

- **Functionality**
  - ✅ Endpoints return 200/2xx for valid inputs (e.g. `GET /search?q=...`, `GET /answer?q=...`, `POST /conversations`, `POST /conversations/{id}/messages`).
  - ✅ Error conditions use appropriate status codes (400 validation, 404 not found, 413 payload too large, 502 upstream failure) and a consistent `{ "error", "code" }` body so callers can handle failures predictably.

- **Usefulness & creativity**
  - ✅ Clear use case: developers building AI apps need live web data and conversation context without wiring Tavily, Cohere, and an LLM themselves. Flux exposes search, answer synthesis, content extraction, and multi-turn state in one API.

- **API design & attention to detail**
  - ✅ Consistent resource naming: `/conversations`, `/conversations/{id}`, `/conversations/{id}/messages`; `/search`, `/answer`, `/contents`.
  - ✅ Pagination on `GET /conversations` (`page`, `page_size`). Filtering on `/search` and `/answer` (`topic`, `days`).
  - ✅ POST to create; GET to retrieve and list; DELETE to remove. Corresponding GET for every created resource (get conversation by id, list conversations).

- **Documentation & developer experience**
  - ✅ README explains setup, tech stack, all endpoints, and curl examples. Interactive docs at `/docs` for exploration. Error format documented so users can interpret `code` and status.

---

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

## AI Tooling Disclosure

AI-assisted development tools were used during implementation. This project is not a wrapper, reskin, or minimal modification of an existing AI tool; the core product concept, architecture, API design, and evaluation approach were created as an original project.

### Tools used

- Cursor AI assistant (LLM-based coding assistant)
- ChatGPT-class LLM assistance through Cursor workflows

### What AI assisted with

- Implementation acceleration (code scaffolding, refactors, and documentation drafting)
- Debugging support and iteration on benchmark/evaluation scripts
- Editing help for API docs and README clarity

### What was created by the team

- Original product idea and scope (live retrieval + reranking + conversation-aware API)
- Endpoint design, data model choices, error contract, and system architecture
- Evaluation methodology and comparison framing

The project focus remained on building an original, production-oriented developer API over the weekend, with AI used strictly as an implementation aid.
