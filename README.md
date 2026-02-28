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

## Scripts

- `bun run search <query>` — Run a web search from the CLI
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