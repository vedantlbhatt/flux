# Flux API Demo

A minimal web UI that uses **every Flux endpoint** in a natural way: multi-conversation chatbot plus optional “try other endpoints” panels.

## What it uses (all 9 endpoints)

| Endpoint | Where in the demo |
|---------|-------------------|
| `GET /health` | Sidebar: “Check health” and on load |
| `GET /conversations` | Sidebar: list of conversations (paginated) |
| `POST /conversations` | “+ New conversation” |
| `GET /conversations/:id` | Selecting a conversation loads messages |
| `POST /conversations/:id/messages` | Sending a message in the chat (context-aware answer) |
| `DELETE /conversations/:id` | Trash icon on each conversation |
| `GET /search` | Sidebar: “Search (GET /search)” → modal with query + limit |
| `GET /answer` | Sidebar: “Quick answer (GET /answer)” → modal with question |
| `GET /contents` | Sidebar: “Extract URLs (GET /contents)” → modal with comma-separated URLs |

## Run it

1. Start the Flux API (from repo root):

   ```bash
   bun run api
   ```

2. If the demo is served from a different origin (e.g. `npx serve demo` → http://localhost:3000), set CORS in your API `.env` so the browser can call the API:

   ```
   CORS_ORIGINS=http://localhost:3000
   ```
   Or use `CORS_ORIGINS=*` to allow any origin.

3. Serve the demo (from repo root):

   ```bash
   npx serve demo
   ```

4. Open the URL shown (e.g. http://localhost:3000). Set **API base URL** in the sidebar if your API is not at `http://localhost:8000` (e.g. a deployed URL).

## Flow

- **Chat:** Create a conversation, send messages. Each message calls `POST /conversations/:id/messages` and shows the synthesized answer and citations.
- **Multiple conversations:** Create several; switch between them; delete from the list.
- **Other endpoints:** Use the sidebar buttons to open Search, Quick answer, or Extract URLs and see the raw API responses.

No build step: plain HTML, CSS, and JavaScript.
