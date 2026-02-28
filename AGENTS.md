# Flux

LLMs are frozen in time. GPT-4, Claude, Llama — every model has a training cutoff. Ask them about anything recent and they hallucinate or say "I don't know." The fix is live web access — but wiring that yourself means calling a search API, fetching pages, cleaning HTML, reranking by relevance, and formatting for an LLM context window. That's not your product. That's infrastructure. And every AI developer builds it from scratch, every time.

Flux collapses that into one API. Send a query, get back live semantically reranked web results — or a synthesized answer with citations — ready for your LLM to consume directly. For developers building chatbots, Flux also maintains conversation context across multiple turns, making each subsequent search smarter than the last.

The pipeline is the source of truth: `query → Tavily retrieval → Cohere rerank → return`.

---

## The problem Flux solves

Building AI apps that know about current events requires wiring together multiple services:

```
1. Call a search API          → get candidate pages
2. Fetch each page            → raw HTML
3. Clean and parse HTML       → extract readable text
4. Embed query + pages        → vectors
5. Rank by relevance          → reorder results
6. Format for LLM             → build prompt
7. Call OpenAI                → get answer
8. Extract citations          → format response
```

That is 8 steps, 4 different services, and 200+ lines of plumbing before a developer has started building their actual product. Flux collapses this into 1–3 API calls depending on how much the developer wants handled for them.

**Flux's differentiation vs existing tools:**
- Perplexity API — black box, no visibility into why results are ranked the way they are, stateless
- Tavily — returns results but does not expose reranking scores or rank deltas, no conversation context
- Exa — powerful but expensive, complex surface, not beginner-friendly

Flux is context-aware: conversation endpoints bias reranking using the full history of what was asked before, not just the latest query.

---

## Goals (hackathon scope)

- Live web search via Tavily API — real, current results, never a static corpus.
- Professional reranking via Cohere Rerank API — not cosine similarity on sentence transformers, a dedicated reranking model that scores query-document relevance directly.
- Stateful conversations — multi-turn context-aware search where each query builds on the previous ones.
- Four endpoints covering the full spectrum from raw results to deep synthesized answers.
- A developer can clone, configure, and make their first successful API call in under 5 minutes.
- All endpoints return typed JSON. All errors return `{ error, code }` with correct HTTP status.

---

## Non-goals (do not build in 36–48 hours)

- A web crawler or custom search index.
- Training or fine-tuning any model.
- User authentication or API key management.
- Rate limiting infrastructure.
- Streaming responses.
- A frontend or dashboard.

---

## Architecture

- **FastAPI** (Python) — HTTP layer; auto-generates OpenAPI spec at `/docs`.
- **Tavily Search API** — live web retrieval; returns up to 20 results per query as structured JSON with clean extracted content. Free tier available.
- **Cohere Rerank API** (`rerank-english-v3.0`) — professional reranking model; scores each document against the query directly, more accurate than cosine similarity on embeddings. Free tier: 1,000 calls/month.
- **OpenAI `gpt-4o-mini`** — used exclusively in `GET /answer` and `POST /conversations/:id/messages` for answer synthesis.
- **In-memory store** (`dict`) — stores conversation objects keyed by `conversation_id`. Resets on server restart. No database.

Rule: Tavily retrieves. Cohere reranks. OpenAI synthesizes. These are three separate, replaceable services. No service does another's job.

---

## Why Cohere instead of Sentence Transformers

Sentence Transformers embed query and documents separately, then compute cosine similarity. This works but is indirect — you're comparing vectors, not directly scoring relevance.

Cohere Rerank takes the query and each document together and scores them jointly — "how relevant is this specific document to this specific query?" This is called a cross-encoder and it is significantly more accurate than bi-encoder cosine similarity for reranking tasks.

Cohere's reranker is the same model used in production by companies like Notion, HubSpot, and Oracle. Using it instead of Sentence Transformers is the correct engineering decision and judges will recognize it.

---

## Data models (minimum viable)

### SearchResult
```
id               str     — stable hash of url
url              str     — page URL
title            str     — page title from Tavily
snippet          str     — clean extracted text excerpt, 150–300 chars
score            float   — Cohere relevance score, 0.0–1.0
rank              int     — position in results (1-indexed)
```

### SearchResponse
```
query            str     — original query string
results          list[SearchResult]
total            int     — number of results returned
reranked         bool    — always true; false only if Cohere call failed
```

### AnswerResponse
```
query            str     — original query string
answer           str     — synthesized natural language answer
citations        list[Citation]
model            str     — always "gpt-4o-mini"
```

### Citation
```
title            str
url              str
score            float
rank             int
```

### Conversation
```
id               str              — uuid, assigned on creation
created_at       str              — ISO 8601 timestamp
message_count    int              — number of messages in this conversation
messages         list[Message]
```

### Message
```
id               str              — uuid
query            str              — what the user asked
answer           str              — synthesized answer for this turn
citations        list[Citation]
results          list[SearchResult]
created_at       str              — ISO 8601 timestamp
```

### ConversationListResponse
```
conversations    list[Conversation]   — paginated list, messages field omitted for brevity
total            int                  — total conversations in store
page             int                  — current page
page_size        int                  — page size used
```

### ErrorResponse
```
error            str     — human-readable message
code             str     — machine-readable code (see error codes)
```

Rules:
- Every route handler returns a typed Pydantic model. No raw `dict` at any boundary. No `Any`.
- `GET /conversations` omits the `messages` field from each Conversation for performance. Use `GET /conversations/:id` to get full messages.
- `POST /conversations/:id/messages` is idempotent in shape — same query always returns the same response structure, even if web content differs.

---

## Endpoints

### Stateless core

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/search` | Live web search, Cohere reranked. Returns `SearchResponse`. |
| `GET` | `/answer` | Synthesized answer from live web sources with citations. Returns `AnswerResponse`. |
| `GET` | `/contents` | Clean extracted text from specific URLs. Returns list of page content objects. |

### Stateful conversations

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/conversations` | Create a new conversation. Returns `Conversation`. |
| `POST` | `/conversations/:id/messages` | Add a query. Runs context-aware search + synthesis. Returns `Message`. |
| `GET` | `/conversations` | List all conversations. Supports pagination. Returns `ConversationListResponse`. |
| `GET` | `/conversations/:id` | Retrieve full conversation with all messages and results. Returns `Conversation`. |
| `DELETE` | `/conversations/:id` | Delete conversation and all associated data. Returns `204 No Content`. |

### Utility

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns `{ status: "ok", cohere_ready: bool, tavily_ready: bool }`. |
| `GET` | `/docs` | Auto-generated OpenAPI / Swagger UI. |

---

## Query parameters

### `GET /search`
```
q              str   required     natural language query; max 500 chars
limit          int   default 10   results to return; min 1, max 20
```

### `GET /answer`
```
q              str   required     natural language query; max 500 chars
```

### `GET /contents`
```
urls           str   required     comma-separated list of URLs; max 10
```

### `GET /search` — filtering
```
q              str   required     natural language query; max 500 chars
limit          int   default 10   results to return; min 1, max 20
topic          str   optional     filter by topic: "news" | "general" — passed to Tavily
days           int   optional     filter results to last N days (e.g. days=7, days=730); min 1, no max; default none
```

### `GET /conversations` — pagination
```
page           int   default 1    page number; min 1
page_size      int   default 20   conversations per page; min 1, max 100
```

### `POST /conversations/:id/messages` (request body)
```
query          str   required     natural language query; max 500 chars
```

Rules:
- `q` and `query` are always processed server-side. Clients never send vectors or embeddings.
- Missing required params → `400` with correct error code immediately, before any external API call.
- `topic` and `days` are passed directly to Tavily — they do not affect reranking, only retrieval.

---

## Pipeline — exact steps

### `GET /search`
```
1.  Validate params → 400 on any violation
2.  Call Tavily search API with q → up to 20 results with pre-extracted content
3.  If Tavily fails → 502 TAVILY_ERROR
4.  If Tavily returns 0 results → 404 NO_RESULTS
5.  Call Cohere Rerank API: query + list of result snippets → relevance scores
6.  If Cohere fails → return Tavily results unranked, reranked=false, log warning
7.  Assign rank (position) to each result
8.  Sort by rank ascending
9.  Truncate to limit
10. Return SearchResponse
```

### `GET /answer`
```
1–9. Identical to /search with limit=10
10.  Take top 5 by rank
11.  Build prompt:
     "Answer the following question using only the sources provided.
      Be concise. Cite sources by number [1], [2], etc.
      Question: {query}
      Sources: {top 5 snippets with index}"
12.  Call gpt-4o-mini, max_tokens=512
13.  If OpenAI fails → 502 ANSWER_FAILED
14.  Return AnswerResponse with answer + citations built from top 5 results
```

### `GET /contents`
```
1.  Validate urls param → 400 if missing or > 10 URLs
2.  Call Tavily extract API with url list
3.  If Tavily fails → 502 TAVILY_ERROR
4.  For each URL: return { url, title, content, word_count, success: bool }
5.  Never fail the whole request if one URL fails — mark that URL success=false
6.  Return list of page content objects
```

### `GET /conversations`
```
1.  Validate page and page_size params → 400 on violation
2.  Retrieve all conversations from store as list
3.  Sort by created_at descending (most recent first)
4.  Slice to page/page_size
5.  Return ConversationListResponse with messages field omitted per conversation
```

### `POST /conversations`
```
1.  Generate uuid for conversation_id
2.  Create Conversation object with empty messages list
3.  Store in memory dict keyed by conversation_id
4.  Return Conversation
```

### `POST /conversations/:id/messages`
```
1.  Validate conversation exists → 404 CONVERSATION_NOT_FOUND if missing
2.  Validate query param → 400 on violation
3.  Build context-aware query:
    - Take last 3 message queries from conversation history
    - Append current query
    - Pass full context string to Tavily so results are relevant to the conversation, not just the latest query
4.  Call Tavily search API with context-aware query
5.  Call Cohere Rerank API — rerank using current query only, not full context
6.  Assign rank to each result
7.  Take top 5, build prompt with conversation history context
8.  Call gpt-4o-mini with full conversation history + new sources
9.  Build Message object with query, answer, citations, results
10. Append Message to conversation.messages
11. Update conversation.message_count
12. Return Message
```

### `GET /conversations/:id`
```
1.  Look up conversation_id in memory store → 404 if not found
2.  Return full Conversation with all messages
```

### `DELETE /conversations/:id`
```
1.  Look up conversation_id → 404 if not found
2.  Remove from memory store
3.  Return 204 No Content
```

---

## Why conversation state is meaningful

Each `POST /conversations/:id/messages` call is smarter than a standalone `/answer` call because:

- The Tavily query includes context from previous turns — if the user asked "what is SVB" and then asks "why did it collapse", Flux searches for "SVB collapse" not just "why did it collapse"
- The OpenAI synthesis call includes the full conversation history — the answer is coherent and references what was said before
- The stored conversation has ongoing value — developers can retrieve it, display it to users, or use it to debug their chatbot

This is not state for the sake of state. A developer building a multi-turn chatbot cannot replicate this with stateless `/answer` calls — they would have to manage conversation context themselves, which is exactly the plumbing Flux is supposed to eliminate.

---

## Error codes

| Code | HTTP | Condition |
|------|------|-----------|
| `MISSING_QUERY` | 400 | `q` or `query` param absent |
| `QUERY_TOO_LONG` | 400 | Query exceeds 500 characters |
| `INVALID_LIMIT` | 400 | `limit` < 1 or > 20 |
| `MISSING_URLS` | 400 | `urls` param absent on `/contents` |
| `TOO_MANY_URLS` | 400 | More than 10 URLs provided to `/contents` |
| `INVALID_BODY` | 400 | Request body missing or malformed |
| `CONVERSATION_NOT_FOUND` | 404 | `conversation_id` not in memory store |
| `INVALID_PAGE` | 400 | `page` < 1 or `page_size` out of range |
| `INVALID_TOPIC` | 400 | `topic` is not "news" or "general" |
| `INVALID_DAYS` | 400 | `days` < 1 or not a positive integer |
| `NO_RESULTS` | 404 | Tavily returned zero results |
| `TAVILY_ERROR` | 502 | Tavily API call failed or returned non-200 |
| `ANSWER_FAILED` | 502 | OpenAI call failed |
| `INTERNAL` | 500 | Unhandled exception |

Rules:
- Cohere failure is NOT a fatal error — degrade to returning Tavily order with `reranked=false`.
- Never swallow exceptions and return 200.
- Never return a bare 500 with no body.
- Every unhandled exception → `500` with `{ error, code: "INTERNAL" }`.

---

## Performance rules

- Tavily returns pre-extracted content — no separate page fetching step needed.
- Cohere Rerank is a single API call for all documents — never call it per-document.
- `/search` target latency: <2s — Tavily + Cohere in sequence, both fast.
- `/answer` allowed up to 8s — OpenAI call adds latency.
- `/conversations/:id/messages` allowed up to 10s — context building + OpenAI.
- `/contents` target latency: <3s — Tavily extract handles fetching.
- Never block the response on a non-critical failure — degrade gracefully.

---

## Tier A — implement first

These must work before anything else is touched:

- `GET /health` — confirms Tavily and Cohere are reachable
- `GET /search` — Tavily retrieval + Cohere reranking, rank on every result
- All error codes returning correct shapes and HTTP statuses
- Cohere failure degrades gracefully to `reranked=false`

## Tier B — implement after Tier A is solid

- `GET /answer` — OpenAI synthesis on top of reranked results
- `GET /contents` — Tavily extract endpoint
- `POST /conversations` + `GET /conversations` (paginated list) + `POST /conversations/:id/messages` + `GET /conversations/:id` + `DELETE /conversations/:id`
- OpenAPI `/docs` descriptions and examples for all endpoints
- Postman collection export

---

## Build order (36–48 hours)

1. FastAPI scaffold + `/health` + global error handler middleware + all Pydantic models defined upfront.
2. Tavily service — `GET /search` returns raw Tavily results, no reranking. Verify with curl.
3. Cohere service — takes list of strings + query → returns relevance scores. Unit test independently.
4. Wire reranking into `GET /search` — assign rank to each result.
5. `GET /answer` — build prompt + OpenAI call + citation assembly. Handle `ANSWER_FAILED`.
6. `GET /contents` — Tavily extract call. Handle partial failures per URL.
7. Conversation store — in-memory dict, CRUD operations, all four conversation endpoints.
8. Context-aware query building in `POST /conversations/:id/messages` — verify follow-up queries use history.
9. Error handling pass — trigger every error code manually. Confirm shape and status.
10. README + Postman collection. Quickstart verified clean on fresh clone.
11. Deploy to Railway or Render — get a public URL. Verify all endpoints work at public URL, not just localhost.
12. Demo prep — prepare a 3-turn conversation demo showing context awareness.

---

## Project structure

```
flux/
  main.py                        ← FastAPI app, router registration, startup checks
  config.py                      ← TAVILY_API_KEY, COHERE_API_KEY, OPENAI_API_KEY from env
  store.py                       ← in-memory conversation store, get/set/delete operations
  models/
    search.py                    ← SearchResult, SearchResponse
    answer.py                    ← AnswerResponse, Citation
    contents.py                  ← PageContent, ContentsResponse
    conversation.py              ← Conversation, Message
    error.py                     ← ErrorResponse
    __init__.py                  ← barrel export
  services/
    tavily.py                    ← Tavily search + extract client; raises on non-200
    cohere.py                    ← Cohere rerank client; returns scores list
    reranker.py                  ← merges Tavily results + Cohere scores → ranked SearchResult list
    answerer.py                  ← prompt build + OpenAI call + citation assembly
    context.py                   ← builds context-aware query string from conversation history
    __init__.py                  ← barrel export
  routers/
    search.py                    ← GET /search
    answer.py                    ← GET /answer
    contents.py                  ← GET /contents
    conversations.py             ← POST, GET, DELETE /conversations + POST /conversations/:id/messages
    health.py                    ← GET /health
  tests/
    test_search.py
    test_answer.py
    test_contents.py
    test_conversations.py
    test_reranker.py
    test_context.py
.env.example
docker-compose.yml
README.md
postman_collection.json
```

---

## Coding conventions

- Keep business logic out of routers. Routers validate input, call services, return models. Nothing else.
- Keep each file under 300 LOC. Split when necessary.
- Always type boundaries: route params, service function signatures, return types.
- Avoid `Any`. Use `Optional[X]` when a value may be absent.
- Run `mypy --strict` before finalizing any file. Treat all warnings as errors.
- Do not use relative imports across service boundaries. Use absolute imports from project root.
- Prefer explicit naming: `tavilyService`, `cohereService`, `reranker`, `answerer`, `contextBuilder`.
- `store.py` is the only file that touches the in-memory conversation dict. No other file imports or mutates it directly.

---

## Project state + duplication avoidance

- One Tavily client. One Cohere client. One OpenAI client. No parallel implementations.
- `reranker.py` owns the merging of Tavily results + Cohere scores. No other file does this.
- `context.py` owns conversation history → query string logic. No other file does this.
- `store.py` owns all reads and writes to the in-memory conversation store.
- Config values come only from `config.py`. No hardcoded API keys or URLs anywhere else.

---

## Definition of done for each endpoint

- Returns correct HTTP 2xx for all valid inputs with correct response shape.
- Every error condition returns `{ error: str, code: str }` with correct HTTP status.
- All fields covered by a Pydantic model — zero untyped returns.
- Appears in `/docs` with description, all params documented, at least one example response.
- Has a working `curl` example in the README.
- `mypy --strict` passes with zero errors on all touched files.
- No duplicate code introduced.

---

## README requirements (judged directly by Stripe)

1. **One-line pitch** — Flux gives your AI app live web knowledge. From a single search to a full multi-turn conversation — without building the infrastructure yourself.
2. **The problem** — 8-step pipeline every AI developer builds from scratch. Flux collapses it to one API call.
3. **Tech stack** — FastAPI, Tavily Search API, Cohere Rerank API, OpenAI `gpt-4o-mini`, Docker.
4. **Quickstart** — exactly 3 steps: clone → fill `.env` → `docker compose up`. First curl call shown inline.
5. **Endpoint reference** — table: method, path, params, response shape, example for every endpoint.
6. **curl examples** — copy-pasteable, runnable examples for all endpoints including multi-turn conversation.
7. **Conversation demo** — 3-turn example showing context awareness:
   ```
   Turn 1: "what is SVB"          → explains SVB
   Turn 2: "why did it collapse"  → knows this means SVB, not generic collapse question
   Turn 3: "what was the federal response" → knows this refers to SVB collapse
   ```
9. **Error reference** — full table of all error codes, HTTP status, and when each fires.
10. **Why Flux** — keyword search matches words. Cohere reranks by meaning. Conversations remember context. Built for AI apps that need live, grounded, context-aware answers.
11. **Hosted docs** — `/docs` OpenAPI UI publicly accessible at deployment URL. Link in README header. (Bonus consideration per Stripe rubric.)
12. **Public deployment** — API deployed to Railway or Render; base URL in README so judges can call it without running locally. (Bonus consideration per Stripe rubric.)