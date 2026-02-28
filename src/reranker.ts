/**
 * Cohere Rerank API v2.
 * Reranks documents by relevance to the query.
 * @see https://docs.cohere.com/reference/rerank
 */

const COHERE_RERANK_URL = "https://api.cohere.com/v2/rerank";

export interface CohereRerankResult {
  index: number;
  relevance_score: number;
}

export interface CohereRerankResponse {
  results: CohereRerankResult[];
  id?: string;
  meta?: { api_version?: unknown; billed_units?: { search_units: number } };
}

/**
 * Rerank documents by relevance to the query.
 * Pass the raw document strings in order; returns indices + scores in reranked order.
 */
export async function cohereRerank(
  apiKey: string,
  query: string,
  documents: string[],
  options?: { model?: string; topN?: number }
): Promise<CohereRerankResponse> {
  if (documents.length === 0) {
    return { results: [] };
  }

  const model = options?.model ?? "rerank-v3.5";
  const top_n = options?.topN ?? Math.min(documents.length, 10);

  const res = await fetch(COHERE_RERANK_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      model,
      query,
      documents,
      top_n,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Cohere Rerank API error ${res.status}: ${text}`);
  }

  return (await res.json()) as CohereRerankResponse;
}

/**
 * Rerank an array of items by using a getter for the text to rank.
 * Returns the items in reranked order (top first).
 */
export function rerankOrder<T>(
  results: CohereRerankResult[],
  items: T[]
): T[] {
  return results.map((r) => items[r.index]).filter((x): x is T => x != null);
}
