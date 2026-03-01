# Flux API Demo

A chat-style web UI for the Flux API: Next.js, React, Tailwind, and shadcn-style components. Monochrome, docs-inspired layout with conversation list (grouped by Today / Last 7 days / Older), message bubbles with citations, and composer with suggestion chips.

## Stack

- **Next.js 14** (App Router)
- **React 18**
- **Tailwind CSS** (design tokens: grayscale theme)
- **shadcn-style UI** (Radix primitives + CVA)
- **lucide-react** icons

## Run locally

1. From this directory (`demo/`):

   ```bash
   npm install
   npm run dev
   ```

2. Open [http://localhost:3000](http://localhost:3000).

3. Ensure the Flux API is running and CORS allows this origin (e.g. `CORS_ORIGINS=http://localhost:3000` or `CORS_ORIGINS=*`). The app uses the same API URL logic as the original demo (localhost when on localhost, else the default Railway URL).

## Deploy (Vercel)

- Set your Vercel project **Root Directory** to `demo` so the build runs from this folder.
- Build command: `npm run build` (default for Next.js).
- No env vars required on Vercel; the API URL is resolved in the client as in the original demo.

## Endpoints used

| Endpoint | Usage |
|----------|--------|
| `GET /health` | Sidebar status badge |
| `GET /conversations` | Conversation list (paginated) |
| `POST /conversations` | New chat |
| `GET /conversations/:id` | Load conversation and messages |
| `POST /conversations/:id/messages` | Send message (context-aware answer) |
| `DELETE /conversations/:id` | Delete from list or header menu |

Search, Quick answer, and Extract URLs are not in this UI; add them as needed.
