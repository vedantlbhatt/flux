/**
 * Load Tavily API key from environment.
 */
export function getTavilyApiKey(): string {
  const key = process.env.TAVILY_API_KEY;
  if (!key?.trim()) {
    throw new Error("Missing Tavily API key. Set TAVILY_API_KEY in your environment or .env file.");
  }
  return key.trim();
}

/**
 * Load Cohere API key from environment (optional, for reranking).
 * Get one at https://dashboard.cohere.com/
 */
export function getCohereApiKey(): string | null {
  const key = process.env.COHERE_API_KEY;
  return key?.trim() ?? null;
}
