# Flux — Full Project Overview

## Purpose

**Flux is a REST API that gives apps live web search, AI answers with citations, and stateful multi-turn conversations** without building search, reranking, or LLM pipelines yourself.

- **Problem it solves:** Building “AI that knows about the world” usually means: call search API → fetch pages → clean HTML → embed → rerank → prompt LLM → extract citations. That’s many steps and services. Flux does that pipeline once and exposes it as a few HTTP endpoints.
- **Differentiation:** Live search (Tavily), professional reranking (Cohere), context-aware conversations (history used for retrieval; Gemini for synthesis). Stateless endpoints plus stateful conversations.

---

## Architecture (one sentence each)

| Layer | Role |
|-------|------|
| **FastAPI** (`main.py`) | HTTP app: routes, CORS, body-size limit, request ID, global error handlers, mounts `/demo`. |
| **Config** (`config.py`) | Loads env: Tavily, Cohere, Gemini keys; CORS origins; store limits; log level. |
| **Store** (`store.py`) | In-memory dict of conversations (id → { id, created_at, message_count, messages }). Only this module touches the store. Resets on restart. |
| **Routers** | Validate input, call services, return Pydantic models. No business logic. |
| **Services** | Tavily (search + extract), Cohere (rerank), Gemini (synthesis), search_flow (orchestrates search+rerank), context (conversation → query string), reranker (merge Tavily + Cohere → SearchResult list). |
| **Models** | Pydantic: SearchResult, SearchResponse; AnswerResponse, Citation; PageContent; Conversation, Message, ConversationListItem, AddMessageRequest; ErrorResponse. |
| **Utils** | Pretty JSON response, retry (429/503/500), safe_errors (redact keys, generic 500 message). |

**Pipeline rule:** Tavily retrieves. Cohere reranks. Gemini synthesizes. Each service has one job.

---

## Endpoints

| Method | Path | Purpose |
|--------|------|--------|
| GET | `/` | Links to docs, demo, health. |
| GET | `/health` | `{ status, tavily_ready, cohere_ready }` — keys present, no live call. |
| GET | `/search` | `q`, `limit`, optional `topic`, `days` → Tavily → Cohere rerank → SearchResponse. |
| GET | `/answer` | `q`, optional `topic`, `days` → same search → top 5 → Gemini → AnswerResponse with citations. |
| GET | `/contents` | `urls` (comma, max 10) → Tavily extract → list of PageContent (per-URL success/failure). |
| POST | `/conversations` | Create conversation → Conversation (empty messages). |
| GET | `/conversations` | List with pagination → ConversationListResponse (messages omitted). |
| GET | `/conversations/:id` | Full conversation with messages. |
| POST | `/conversations/:id/messages` | Body `{ query }` → context-aware search (last 3 queries + current) → rerank by current only → Gemini with history → append Message, return it. |
| DELETE | `/conversations/:id` | Remove conversation → 204. |
| GET | `/demo`, `/demo/` | Static demo UI (or Next.js app when built from `demo/`). |
| GET | `/docs` | OpenAPI/Swagger UI. |

---

## Data flow (high level)

1. **Search:** `GET /search` → router validates → `search_flow.run_search(query, limit, topic, days)` → Tavily search → Cohere rerank (or Tavily-only on failure) → merge_and_rank / tavily_only_results → SearchResponse.
2. **Answer:** `GET /answer` → same search with limit=10 → top 5 → build prompt → `gemini_generate()` → AnswerResponse + citations.
3. **Conversation message:** `POST /conversations/:id/messages` → load conversation → `build_context_query(current, last 3 queries)` → Tavily with that context → Cohere rerank with current query only → top 5 → prompt with full history → Gemini → store new message → return Message.
4. **Contents:** `GET /contents` → Tavily extract for URLs → optional cleanup (e.g. Wikipedia) → list of PageContent.

---

## Key files (by concern)

- **Entry / HTTP:** `main.py`, `config.py`
- **Conversation state:** `store.py`, `routers/conversations.py`, `services/context.py`
- **Search pipeline:** `services/search_flow.py`, `services/tavily.py`, `services/cohere_service.py`, `services/reranker.py`
- **Synthesis:** `services/gemini_service.py` (used by `routers/answer.py` and `routers/conversations.py`)
- **Extract:** `services/tavily_extract.py`, `routers/contents.py`
- **Shapes:** `models/*.py`
- **Resilience / safety:** `utils/retry.py`, `utils/safe_errors.py`, `utils/responses.py`
- **Demo:** `demo/` — Next.js app (conversation list, chat, composer) talking to the API; also legacy static `index.html` / `app.js` / `styles.css` in same folder.
- **Deploy:** `Procfile` (uvicorn), `requirements.txt`
- **Extras:** `experiments/offline_eval/` (offline A/B eval), `scripts/benchmark_flux.py` (endpoint benchmarks)

---

## Bug fix applied during review

- **`store.py`:** Was using `config.MAX_CONVERSATIONS` and `config.MAX_MESSAGES_PER_CONVERSATION` without `import config` → 500 on POST /conversations. Fixed by adding `import config`.
- **`main.py`:** Lifespan used `await asyncio.sleep(3)` without `import asyncio`. Fixed by adding `import asyncio`.

---

## Summary

Flux is a single API that bundles **live web search (Tavily)**, **reranking (Cohere)**, and **answer synthesis (Gemini)** behind a small set of REST endpoints. It adds **stateful conversations** so multi-turn chats use prior queries for retrieval and full history for the LLM. The demo is a Next.js chat UI that uses those endpoints; the API can be deployed (e.g. Railway) and the demo separately (e.g. Vercel).
