/**
 * Flux API client. Same endpoints as the vanilla demo.
 */

const API_BASE_URL = "https://flux-production-9c9e.up.railway.app";

function getBaseUrl(): string {
  return API_BASE_URL;
}

export type HealthResponse = { status: string; tavily_ready: boolean; cohere_ready: boolean };

export type Conversation = {
  id: string;
  created_at: string;
  message_count: number;
  messages?: Message[];
};

export type Citation = { title: string; url: string; score: number; rank: number };

export type Message = {
  id: string;
  query: string;
  answer?: string;
  citations?: Citation[];
  results?: unknown[];
  created_at: string;
};

export type ConversationListResponse = {
  conversations: Conversation[];
  total: number;
  page: number;
  page_size: number;
};

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = getBaseUrl() + path;
  const res = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const text = await res.text();
  if (res.status === 204) return null as T;
  let data: unknown;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    throw new Error(res.ok ? text : `HTTP ${res.status}: ${text}`);
  }
  if (!res.ok) {
    const err = data as { error?: string; code?: string };
    throw new Error(err?.error || err?.code || `HTTP ${res.status}`);
  }
  return data as T;
}

export async function checkHealth(): Promise<HealthResponse> {
  return api<HealthResponse>("/health");
}

export async function listConversations(page = 1, pageSize = 50): Promise<ConversationListResponse> {
  return api<ConversationListResponse>(`/conversations?page=${page}&page_size=${pageSize}`);
}

export async function createConversation(): Promise<Conversation> {
  return api<Conversation>("/conversations", { method: "POST" });
}

export async function getConversation(id: string): Promise<Conversation> {
  return api<Conversation>(`/conversations/${id}`);
}

export async function deleteConversation(id: string): Promise<void> {
  await api(`/conversations/${id}`, { method: "DELETE" });
}

export async function sendMessage(conversationId: string, query: string): Promise<Message> {
  return api<Message>(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}
