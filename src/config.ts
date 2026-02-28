/**
 * Load Tavily API key from environment.
 * Use TAVILY_API_KEY.
 */
export function getTavilyApiKey(): string {
  const key = process.env.TAVILY_API_KEY;
  if (!key?.trim()) {
    throw new Error("Missing Tavily API key. Set TAVILY_API_KEY in your environment or .env file.");
  }
  return key.trim();
}
