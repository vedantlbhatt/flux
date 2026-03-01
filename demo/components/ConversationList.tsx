"use client";

import * as React from "react";
import { Search, MessageSquarePlus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { groupConversations, GROUP_LABELS, type ConversationGroup } from "@/lib/group-conversations";
import type { Conversation } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ConversationListProps {
  conversations: Conversation[];
  currentId: string | null;
  loading?: boolean;
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
}

function conversationTitle(conv: Conversation): string {
  const firstMessage = conv.messages?.[0];
  if (firstMessage?.query) {
    const q = firstMessage.query.trim();
    return q.length > 36 ? q.slice(0, 36) + "…" : q;
  }
  return `Chat ${conv.id.slice(0, 8)}…`;
}

function filterConversations(conversations: Conversation[], query: string): Conversation[] {
  const q = query.trim().toLowerCase();
  if (!q) return conversations;
  return conversations.filter((c) => {
    const title = conversationTitle(c).toLowerCase();
    const id = c.id.toLowerCase();
    return title.includes(q) || id.includes(q);
  });
}

export function ConversationList({
  conversations,
  currentId,
  loading,
  searchQuery,
  onSearchChange,
  onSelect,
  onNewChat,
  onDelete,
}: ConversationListProps) {
  const filtered = filterConversations(conversations, searchQuery);
  const groups = groupConversations(filtered);

  const renderGroup = (groupKey: ConversationGroup) => {
    const list = groups[groupKey];
    if (!list.length) return null;
    return (
      <div key={groupKey} className="mb-4">
        <p className="mb-1.5 px-2 text-xs font-medium text-muted-foreground">
          {GROUP_LABELS[groupKey]}
        </p>
        <ul className="space-y-0.5">
          {list.map((conv) => (
            <li key={conv.id}>
              <ConversationItem
                conversation={conv}
                isActive={conv.id === currentId}
                onSelect={() => onSelect(conv.id)}
                onDelete={(e) => onDelete(conv.id, e)}
              />
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="flex h-full flex-col p-3">
      <div className="mb-3 flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search conversations"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="h-8 pl-8"
            aria-label="Search conversations"
          />
        </div>
      </div>
      <Button
        variant="secondary"
        size="sm"
        className="w-full gap-2"
        onClick={onNewChat}
        aria-label="New conversation"
      >
        <MessageSquarePlus className="h-4 w-4" />
        New chat
      </Button>
      <Separator className="my-3" />
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-9 w-full rounded-md" />
          ))}
        </div>
      ) : (
        <ScrollArea className="flex-1 pr-1">
          {renderGroup("today")}
          {renderGroup("last7")}
          {renderGroup("older")}
          {filtered.length === 0 && (
            <p className="px-2 py-4 text-center text-sm text-muted-foreground">
              {searchQuery.trim() ? "No matches." : "No conversations yet."}
            </p>
          )}
        </ScrollArea>
      )}
    </div>
  );
}

function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
}: {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
}) {
  const title = conversationTitle(conversation);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
      className={cn(
        "group flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors duration-150",
        isActive
          ? "bg-muted text-foreground"
          : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
      )}
      aria-current={isActive ? "true" : undefined}
    >
      <span className="min-w-0 flex-1 truncate">{title}</span>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onDelete(e);
        }}
        className="shrink-0 rounded p-1 opacity-0 transition-opacity hover:bg-border focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-neutral-500 group-hover:opacity-100"
        aria-label="Delete conversation"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
