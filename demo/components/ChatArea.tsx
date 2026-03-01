"use client";

import * as React from "react";
import {
  MoreHorizontal,
  MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { MessageBubble } from "@/components/MessageBubble";
import { Composer } from "@/components/Composer";
import type { Conversation, Message } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ChatAreaProps {
  conversation: Conversation | null;
  loading: boolean;
  sending: boolean;
  pendingQuery: string | null;
  error: string | null;
  onSendMessage: (query: string) => Promise<void>;
  onDeleteConversation: () => void;
}

export function ChatArea({
  conversation,
  loading,
  sending,
  pendingQuery,
  error,
  onSendMessage,
  onDeleteConversation,
}: ChatAreaProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages?.length, sending]);

  const messages = conversation?.messages ?? [];
  const isEmpty = messages.length === 0 && !sending;
  const title = conversation
    ? messages[0]?.query
      ? (messages[0].query.length > 40 ? messages[0].query.slice(0, 40) + "…" : messages[0].query)
      : "New chat"
    : null;

  return (
    <div className="flex h-full flex-col">
      {conversation && (
        <>
          <header className="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-border px-4">
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-sm font-medium text-foreground">
                {title}
              </h1>
              <p className="truncate text-xs text-muted-foreground">
                {conversation.message_count} message{conversation.message_count !== 1 ? "s" : ""}
              </p>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Conversation menu">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={onDeleteConversation}
                  className="text-muted-foreground focus:text-foreground"
                >
                  Delete conversation
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </header>
          <Separator className="shrink-0" />
        </>
      )}

      <ScrollArea className="flex-1">
        <div className="mx-auto max-w-2xl px-4 py-6">
          {!conversation && !loading && (
            <EmptyState />
          )}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center gap-2 text-muted-foreground">
                <div className="h-6 w-6 animate-pulse rounded-full border-2 border-border border-t-foreground" />
                <span className="text-sm">Loading…</span>
              </div>
            </div>
          )}
          {conversation && !loading && (
            <>
              <div className="space-y-4">
                {messages.map((msg) => (
                  <React.Fragment key={msg.id}>
                    <MessageBubble message={msg} role="user" />
                    <MessageBubble
                      message={{
                        id: msg.id,
                        query: msg.query,
                        answer: msg.answer,
                        citations: msg.citations,
                        created_at: msg.created_at,
                        error: (msg as Message & { error?: string }).error,
                      }}
                      role="assistant"
                    />
                  </React.Fragment>
                ))}
                {sending && pendingQuery && (
                  <>
                    <MessageBubble
                      message={{ id: "sending", query: pendingQuery, created_at: "" }}
                      role="user"
                    />
                    <MessageBubble
                      message={{ id: "sending", query: "", answer: "", created_at: "" }}
                      role="assistant"
                      isStreaming
                    />
                  </>
                )}
              </div>
              {error && (
                <div className="mt-4 rounded-md border border-border bg-muted/80 px-3 py-2 text-sm text-muted-foreground">
                  {error}
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </ScrollArea>

      {conversation && (
        <div className="shrink-0 border-t border-border pt-3">
          <Composer
            onSubmit={onSendMessage}
            disabled={sending}
            emptyState={isEmpty}
          />
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <MessageSquare className="h-12 w-12 text-muted-foreground/60" />
      <p className="mt-4 text-sm font-medium text-foreground">
        Select a conversation or start a new one
      </p>
      <p className="mt-1 max-w-sm text-xs text-muted-foreground">
        Messages use <strong>POST /conversations/:id/messages</strong> (context-aware search + answer).
      </p>
    </div>
  );
}
