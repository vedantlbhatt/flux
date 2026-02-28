#!/usr/bin/env bun
/**
 * CLI for Tavily Search.
 * Usage: bun run search [query]
 * Or:    bun run src/cli.ts "your search query"
 */

import { getTavilyApiKey } from "./config";
import { tavilySearch, type TavilySearchResult } from "./tavily";

async function main(): Promise<void> {
  const query: string = process.argv.slice(2).join(" ").trim();
  if (!query) {
    console.error("Usage: bun run search <query>");
    console.error("Example: bun run search \"tavily search api\"");
    process.exit(1);
  }

  const apiKey = getTavilyApiKey();
  const res = await tavilySearch(apiKey, {
    query,
    max_results: 10,
    search_depth: "basic",
    include_answer: false,
    include_favicon: true,
  });

  console.log(`Query: ${res.query}\n`);

  const results = res.results ?? [];
  if (results.length === 0) {
    console.log("No results.");
    return;
  }

  for (let i = 0; i < results.length; i++) {
    const r: TavilySearchResult = results[i];
    console.log(`${i + 1}. ${r.title}`);
    console.log(`   ${r.url}`);
    console.log(`   ${r.content}`);
    console.log("");
  }
}

main().catch((err: unknown) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
