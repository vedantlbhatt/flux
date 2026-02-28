/**
 * Tavily Search API client.
 * @see https://docs.tavily.com/documentation/api-reference/endpoint/search
 */

const TAVILY_SEARCH_URL = "https://api.tavily.com/search";

export type TavilySearchDepth = "advanced" | "basic" | "fast" | "ultra-fast";
export type TavilySearchTopic = "general" | "news" | "finance";
export type TavilyTimeRange = "day" | "week" | "month" | "year" | "d" | "w" | "m" | "y";

export interface TavilySearchParams {
  query: string;
  search_depth?: TavilySearchDepth;
  max_results?: number;
  topic?: TavilySearchTopic;
  time_range?: TavilyTimeRange | null;
  start_date?: string | null; // YYYY-MM-DD
  end_date?: string | null; // YYYY-MM-DD
  include_answer?: boolean | "basic" | "advanced";
  include_raw_content?: boolean | "markdown" | "text";
  include_images?: boolean;
  include_image_descriptions?: boolean;
  include_favicon?: boolean;
  include_domains?: string[];
  exclude_domains?: string[];
  include_usage?: boolean;
}

export interface TavilySearchResult {
  title: string;
  url: string;
  content: string;
  score: number;
  raw_content?: string | null;
  favicon?: string;
}

export interface TavilySearchResponse {
  query: string;
  answer?: string;
  images: Array<{ url: string; description?: string }>;
  results: TavilySearchResult[];
  auto_parameters?: Record<string, unknown>;
  response_time: number;
  usage?: { credits: number };
  request_id?: string;
}

export async function tavilySearch(
  apiKey: string,
  params: TavilySearchParams
): Promise<TavilySearchResponse> {
  const res = await fetch(TAVILY_SEARCH_URL, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      api_key: apiKey,
      ...params,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Tavily API error ${res.status}: ${text}`);
  }

  return (await res.json()) as TavilySearchResponse;
}

