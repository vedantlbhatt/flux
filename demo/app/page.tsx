"use client";

import * as React from "react";
import { AppShell } from "@/components/AppShell";
import { ConversationList } from "@/components/ConversationList";
import { ChatArea } from "@/components/ChatArea";
import { Badge } from "@/components/ui/badge";
import {
  checkHealth,
  listConversations,
  createConversation,
  getConversation,
  deleteConversation,
  sendMessage,
  type Conversation,
} from "@/lib/api";

export default function DemoPage() {
  const [conversations, setConversations] = React.useState<Conversation[]>([]);
  const [currentId, setCurrentId] = React.useState<string | null>(null);
  const [conversation, setConversation] = React.useState<Conversation | null>(null);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [sending, setSending] = React.useState(false);
  const [pendingQuery, setPendingQuery] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [health, setHealth] = React.useState<{ tavily: boolean; cohere: boolean } | null>(null);
  const [offline, setOffline] = React.useState(false);

  const loadList = React.useCallback(async () => {
    try {
      const data = await listConversations(1, 50);
      setConversations(data.conversations);
    } catch (e) {
      console.error(e);
      setConversations([]);
    }
  }, []);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const h = await checkHealth();
        if (!cancelled) setHealth({ tavily: h.tavily_ready, cohere: h.cohere_ready });
      } catch {
        if (!cancelled) setHealth({ tavily: false, cohere: false });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  React.useEffect(() => {
    setOffline(typeof navigator !== "undefined" && !navigator.onLine);
    const onOffline = () => setOffline(true);
    const onOnline = () => setOffline(false);
    window.addEventListener("offline", onOffline);
    window.addEventListener("online", onOnline);
    return () => {
      window.removeEventListener("offline", onOffline);
      window.removeEventListener("online", onOnline);
    };
  }, []);

  React.useEffect(() => {
    setLoading(true);
    loadList().finally(() => setLoading(false));
  }, [loadList]);

  React.useEffect(() => {
    if (!currentId) {
      setConversation(null);
      return;
    }
    setLoading(true);
    getConversation(currentId)
      .then(setConversation)
      .catch((e) => {
        setError(e.message);
        setConversation(null);
      })
      .finally(() => setLoading(false));
  }, [currentId]);

  const handleSelect = React.useCallback((id: string) => {
    setCurrentId(id);
    setError(null);
  }, []);

  const handleNewChat = React.useCallback(async () => {
    setError(null);
    try {
      const c = await createConversation();
      setConversations((prev) => [
        { id: c.id, created_at: c.created_at, message_count: 0 },
        ...prev,
      ]);
      setCurrentId(c.id);
      setConversation({ ...c, messages: [] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create conversation");
    }
  }, []);

  const handleDelete = React.useCallback(
    async (id: string, e: React.MouseEvent) => {
      e.stopPropagation();
      try {
        await deleteConversation(id);
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (currentId === id) {
          setCurrentId(null);
          setConversation(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete");
      }
    },
    [currentId]
  );

  const handleSendMessage = React.useCallback(
    async (query: string) => {
      if (!currentId) return;
      setError(null);
      setSending(true);
      setPendingQuery(query);
      try {
        const msg = await sendMessage(currentId, query);
        const conv = await getConversation(currentId);
        setConversation(conv);
        setConversations((prev) =>
          prev.map((c) =>
            c.id === currentId ? { ...c, message_count: conv.message_count } : c
          )
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : "Request failed");
      } finally {
        setSending(false);
        setPendingQuery(null);
      }
    },
    [currentId]
  );

  const handleDeleteCurrent = React.useCallback(() => {
    if (currentId) handleDelete(currentId, {} as React.MouseEvent);
  }, [currentId, handleDelete]);

  const currentConversation = currentId ? conversation : null;

  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between gap-2 border-b border-border p-3">
        <span className="text-sm font-semibold text-foreground">Flux</span>
        {health != null && (
          <Badge variant="success" className="text-[10px]">
            {health.tavily && health.cohere ? "API ok" : "API degraded"}
          </Badge>
        )}
      </div>
      <ConversationList
        conversations={conversations}
        currentId={currentId}
        loading={loading && !conversations.length}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSelect={handleSelect}
        onNewChat={handleNewChat}
        onDelete={handleDelete}
      />
    </div>
  );

  return (
    <AppShell sidebar={sidebar}>
      {offline && (
        <div className="shrink-0 border-b border-border bg-muted/80 px-4 py-2 text-center text-sm text-muted-foreground">
          You are offline. Check your connection.
        </div>
      )}
      <ChatArea
        conversation={currentConversation}
        loading={loading && currentId != null && !conversation}
        sending={sending}
        pendingQuery={pendingQuery}
        error={error}
        onSendMessage={handleSendMessage}
        onDeleteConversation={handleDeleteCurrent}
      />
    </AppShell>
  );
}
