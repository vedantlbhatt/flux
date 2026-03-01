"use client";

import * as React from "react";
import { Copy, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Citation, Message } from "@/lib/api";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: Pick<Message, "query" | "answer" | "citations" | "id" | "created_at"> & { error?: string };
  role: "user" | "assistant";
  isStreaming?: boolean;
}

export function MessageBubble({ message, role, isStreaming }: MessageBubbleProps) {
  const text = role === "user" ? message.query : ((message.error || message.answer) ?? "");
  const citations = role === "assistant" ? message.citations : undefined;

  const handleCopy = React.useCallback(() => {
    if (!text) return;
    void navigator.clipboard.writeText(text);
  }, [text]);

  return (
    <div
      className={cn(
        "group flex flex-col gap-1 rounded-lg px-4 py-3 transition-colors duration-150",
        role === "user"
          ? "bg-muted/80"
          : "bg-card border border-border"
      )}
      data-role={role}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-medium text-muted-foreground">
          {role === "user" ? "You" : "Flux"}
        </span>
        {text && (
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
                  onClick={handleCopy}
                  aria-label="Copy"
                >
                  <Copy className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Copy</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      <div className="min-w-0 text-sm leading-relaxed text-foreground whitespace-pre-wrap break-words">
        {isStreaming && !text ? (
          <ThinkingIndicator />
        ) : (
          text
        )}
      </div>
      {citations && citations.length > 0 && (
        <CitationsBlock citations={citations} />
      )}
    </div>
  );
}

function ThinkingIndicator() {
  return (
    <span className="inline-flex items-center gap-1 text-muted-foreground">
      <span className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground" />
      <span className="text-xs">Searching and synthesizing…</span>
    </span>
  );
}

function CitationsBlock({ citations }: { citations: Citation[] }) {
  return (
    <div className="mt-2 rounded-md border border-border bg-muted/50 px-3 py-2">
      <p className="mb-1.5 text-xs font-medium text-muted-foreground">Sources</p>
      <ul className="space-y-1">
        {citations.map((c, i) => (
          <li key={i}>
            <a
              href={c.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-foreground underline decoration-border underline-offset-2 hover:decoration-foreground"
            >
              {c.title || c.url}
              <ExternalLink className="h-3 w-3 shrink-0" />
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
