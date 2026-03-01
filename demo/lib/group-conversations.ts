import type { Conversation } from "./api";

export type ConversationGroup = "today" | "last7" | "older";

export function getConversationGroup(createdAt: string): ConversationGroup {
  const date = new Date(createdAt);
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfSevenDaysAgo = new Date(startOfToday);
  startOfSevenDaysAgo.setDate(startOfSevenDaysAgo.getDate() - 7);

  if (date >= startOfToday) return "today";
  if (date >= startOfSevenDaysAgo) return "last7";
  return "older";
}

export function groupConversations(conversations: Conversation[]): {
  today: Conversation[];
  last7: Conversation[];
  older: Conversation[];
} {
  const groups = { today: [] as Conversation[], last7: [] as Conversation[], older: [] as Conversation[] };
  for (const c of conversations) {
    const group = getConversationGroup(c.created_at);
    groups[group].push(c);
  }
  return groups;
}

export const GROUP_LABELS: Record<ConversationGroup, string> = {
  today: "Today",
  last7: "Last 7 days",
  older: "Older",
};
