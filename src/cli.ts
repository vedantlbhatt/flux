#!/usr/bin/env bun
/**
 * CLI for Tavily Search (optional Cohere rerank).
 * Usage: bun run search [query]
 */

import { getTavilyApiKey, getCohereApiKey } from "./config";
import { tavilySearch, type TavilySearchResult } from "./tavily";
import { cohereRerank, rerankOrder, type CohereRerankResult } from "./reranker";

async function main(): Promise<void> {
  const query: string = process.argv.slice(2).join(" ").trim();
  if (!query) {
    console.error("Usage: bun run search <query>");
    console.error("Example: bun run search \"tavily search api\"");
    process.exit(1);
  }

  const tavilyKey = getTavilyApiKey();
  const res = await tavilySearch(tavilyKey, {
    query,
    max_results: 10,
    search_depth: "fast",
    include_answer: false,
    include_favicon: true,
  });

  let results: TavilySearchResult[] = res.results ?? [];
  if (results.length === 0) {
    console.log("No results.");
    return;
  }

  const cohereKey = getCohereApiKey();
  let rerankMeta: CohereRerankResult[] | null = null;
  if (cohereKey) {
    const documents = results.map((r) => `${r.title}\n${r.content}`);
    const reranked = await cohereRerank(cohereKey, query, documents, {
      topN: results.length,
    });
    results = rerankOrder(reranked.results, results);
    rerankMeta = reranked.results;
    console.log(`Query: ${res.query} (reranked with Cohere)\n`);
  } else {
    console.log(`Query: ${res.query}\n`);
  }

  for (let i = 0; i < results.length; i++) {
    const r: TavilySearchResult = results[i];
    const prefix =
      rerankMeta != null
        ? `[orig #${rerankMeta[i]?.index != null ? rerankMeta[i]!.index + 1 : "?"}, score ${
            rerankMeta[i]?.relevance_score != null
              ? rerankMeta[i]!.relevance_score.toFixed(3)
              : "?"
          }] `
        : "";
    console.log(`${i + 1}. ${prefix}${r.title}`);
    console.log(`   ${r.url}`);
    console.log(`   ${r.content}`);
    console.log("");
  }
}

main().catch((err: unknown) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
