# Flux

**One line:** Flux is a REST API that gives your app **live web search**, **AI answers with citations**, and **stateful conversations**—without wiring search, reranking, or LLMs yourself.

| Use it for | One call |
|------------|----------|
| **Search** the web and get reranked results | `GET /search?q=...` |
| **Answer** a question with cited sources | `GET /answer?q=...` |
| **Conversation** — multi-turn chat with context | `POST /conversations` → `POST /conversations/{id}/messages` |
| **Extract** clean text from URLs | `GET /contents?urls=...` |

All over HTTP. JSON in, JSON out. Test with cURL or Postman; optional demo UI at `/demo`.

**Tech stack:** FastAPI, Tavily (search), Cohere (rerank), Google Gemini (synthesis). In-memory store—no database required.

---

## Quick start (3 steps)

1. **Clone and env**
   ```bash
   cp .env.example .env
   ```
   Set `TAVILY_API_KEY` (required). For answers and conversations add `GEMINI_API_KEY`. Optional: `COHERE_API_KEY` for better ranking.

2. **Run the API**
   ```bash
   python -m venv .venv && .venv/bin/pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   Server: **http://localhost:8000**. Docs: **http://localhost:8000/docs**.

3. **Try it**
   ```bash
   curl http://localhost:8000/health
   curl "http://localhost:8000/search?q=FastAPI&limit=3"
   curl "http://localhost:8000/answer?q=What+is+FastAPI"
   ```

---

## Setup (detailed)

1. Get an API key from [Tavily](https://docs.tavily.com/).
2. Copy `.env.example` to `.env` and set `TAVILY_API_KEY`.
3. For **answer** and **conversations** endpoints, set `GEMINI_API_KEY` in `.env` ([get one](https://aistudio.google.com/app/apikey)).
   - Key must be from **Google AI Studio** (aistudio.google.com), not only Google Cloud.
   - If you get 400 from Gemini: run the command below from the project directory to test the key in `.env` and see Google’s exact error.
   ```bash
   # From repo root: uses GEMINI_API_KEY from .env
   curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$(grep '^GEMINI_API_KEY=' .env | cut -d= -f2-)" \
     -H "Content-Type: application/json" \
     -d '{"contents":[{"role":"user","parts":[{"text":"Say hi"}]}]}'
   ```
   If it works you’ll see JSON with `"candidates"`. If not, the response body is the exact reason (e.g. `"API key not valid"`, `"not available in your region"`).
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

### Deploy on Railway

One deployment serves both the API and the demo UI.

1. **Connect the repo** to [Railway](https://railway.app) (New Project → Deploy from GitHub repo).
2. **Set environment variables** in the Railway dashboard (Variables):
   - `TAVILY_API_KEY` (required)
   - `GEMINI_API_KEY` (required for /answer and conversations)
   - `COHERE_API_KEY` (optional, for reranking)
   - `CORS_ORIGINS=*` (recommended if the demo is on Vercel or you run it locally—allows the API to be called from any origin)
3. Railway uses the **Procfile** to run `uvicorn main:app --host 0.0.0.0 --port $PORT`. No extra config needed.
4. After deploy you get a URL like `https://your-app.up.railway.app`:
   - **API:** `https://your-app.up.railway.app/health`, `/search`, `/answer`, `/conversations`, etc.
   - **Docs:** `https://your-app.up.railway.app/docs`
   - **Demo UI:** `https://your-app.up.railway.app/demo` (the demo’s “API base URL” defaults to the same origin)

### Deploy demo on Vercel (optional)

Host the demo as a separate static site so you get a Vercel URL (e.g. `https://flux-demo.vercel.app`) that talks to your Railway API.

1. **Railway:** In your Railway service → **Variables**, set `CORS_ORIGINS=*` so the API accepts requests from Vercel (and from anywhere). Redeploy if needed.
2. **Vercel:** Go to [vercel.com](https://vercel.com) → **Add New** → **Project** → Import your GitHub repo (the Flux repo).
3. **Configure the project:**
   - **Root Directory:** Click “Edit” and set to **`demo`** (so Vercel only deploys the demo folder).
   - **Build Command:** Leave empty (static site, no build).
   - **Output Directory:** Leave default.
   - **Install Command:** Leave empty.
4. **Deploy.** Vercel will build and give you a URL like `https://flux-xxx.vercel.app`.
5. The demo’s “API base URL” is already set to your Railway URL in `demo/index.html`. If your Railway URL is different, change the `value` in that input in `demo/index.html` and redeploy on Vercel (or change it in the UI after loading).

You don’t need to set any env vars on Vercel for the demo; the API URL is in the HTML. The API stays on Railway and is callable from anywhere as long as `CORS_ORIGINS=*` is set there.

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

### Demo (60-second walkthrough)

With the server running, run the script to hit every capability: health → search → answer → stateful conversation (2 turns) → error handling.

```bash
chmod +x demo.sh
./demo.sh
```

Uses `BASE_URL=http://localhost:8000` by default; set `BASE_URL` if your server is elsewhere (e.g. a deployed URL for a live demo).

**Demo website (chatbot UI using all endpoints):** A small static app in `demo/` provides a multi-conversation chatbot plus panels for Search, Quick answer, and Extract URLs. With the API running, serve the demo and open in a browser:

```bash
npx serve demo
```

Then open the URL shown (e.g. http://localhost:3000). See `demo/README.md` for which endpoint each part of the UI calls.

## All endpoints

| Method | Path | Purpose |
|--------|------|--------|
| `GET` | `/health` | Check service; reports Tavily/Cohere readiness |
| `GET` | `/search` | Live web search, reranked. Params: `q` (required), `limit` (1–20), `topic` (news \| general), `days` |
| `GET` | `/answer` | One-shot: question → cited answer. Params: `q`, optional `topic`, `days` |
| `GET` | `/contents` | Extract clean text from up to 10 URLs. Param: `urls` (comma-separated) |
| `POST` | `/conversations` | Create conversation; returns `id` for messages |
| `GET` | `/conversations` | List conversations (paginated: `page`, `page_size` 1–100) |
| `GET` | `/conversations/{id}` | Get one conversation with all messages |
| `POST` | `/conversations/{id}/messages` | Add a message; body `{"query": "..."}` → context-aware search + answer |
| `DELETE` | `/conversations/{id}` | Delete conversation (204 No Content) |

Responses are JSON. Errors use a single shape: `{"error": "<message>", "code": "<CODE>"}` with the right HTTP status so clients can handle them predictably.

### When something goes wrong

| Code | HTTP | When |
|------|------|------|
| `MISSING_QUERY` | 400 | `q` or `query` missing |
| `QUERY_TOO_LONG` | 400 | Query &gt; 500 chars |
| `INVALID_LIMIT` | 400 | `limit` not 1–20 |
| `MISSING_URLS` / `TOO_MANY_URLS` | 400 | `urls` missing or &gt; 10 |
| `INVALID_TOPIC` | 400 | `topic` not `news` or `general` |
| `INVALID_DAYS` | 400 | `days` &lt; 1 |
| `INVALID_BODY` | 400 | Malformed or missing body |
| `CONVERSATION_NOT_FOUND` | 404 | No conversation for that `id` |
| `NO_RESULTS` | 404 | Search returned nothing |
| `TAVILY_ERROR` | 502 | Tavily API failure |
| `ANSWER_FAILED` | 502 | Gemini API failure |
| `PAYLOAD_TOO_LARGE` | 413 | Request body &gt; 1MB |
| `INTERNAL` | 500 | Unhandled server error |

### API design (in brief)

- **Resource naming:** `/conversations`, `/conversations/{id}`, `/conversations/{id}/messages`; stateless `/search`, `/answer`, `/contents`.
- **Pagination:** `GET /conversations?page=1&page_size=20`. **Filtering:** `/search` and `/answer` support `topic` and `days`.
- **Full CRUD for conversations:** POST to create, GET to list and get one, DELETE to remove. Every created conversation is retrievable by `id`.
- **Predictable errors:** Same `{ error, code }` shape and appropriate status codes so callers can branch on `code` or status.

---

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

## HackIllinois — Best Web API

**How Flux fits the track:** One API, four clear capabilities (search, answer, contents, conversations). Developers get live web data and cited answers in a few REST calls instead of gluing multiple services. We focused on a **simple surface** (one-line pitch, one table of endpoints, one error shape), **predictable behavior** (correct status codes, pagination, full CRUD), and **documentation that gets you running fast** (quick start, full endpoint table, error reference, hosted `/docs`).

| Rubric | How Flux addresses it |
|--------|------------------------|
| **Functionality** | All endpoints return 2xx for valid input. Errors use 400/404/413/502/500 with a consistent `{ "error", "code" }` body (see [When something goes wrong](#when-something-goes-wrong)). |
| **Usefulness & creativity** | Solves a real need: AI apps that need *current* web info and multi-turn context without building search + rerank + LLM pipelines. Stateful conversations use context across turns (e.g. “what is SVB” → “why did it collapse”). |
| **API design & attention to detail** | RESTful naming; pagination on list (`/conversations`); filtering on search (`topic`, `days`); POST/GET/DELETE for conversations with a GET for every created resource. See [API design (in brief)](#api-design-in-brief). |
| **Documentation & DX** | Quick start (3 steps), [all endpoints](#all-endpoints) in one table, [error codes](#when-something-goes-wrong) for debugging. **Hosted docs:** run the server → **http://localhost:8000/docs** (Swagger UI, try-it-out). Optional: public deploy for bonus. |

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
