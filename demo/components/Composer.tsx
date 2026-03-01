"use client";

import * as React from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "What is SVB?",
  "Why did it collapse?",
  "What was the federal response?",
];

interface ComposerProps {
  onSubmit: (query: string) => void;
  disabled?: boolean;
  placeholder?: string;
  emptyState?: boolean;
}

export function Composer({
  onSubmit,
  disabled,
  placeholder = "Ask anything…",
  emptyState = false,
}: ComposerProps) {
  const [value, setValue] = React.useState("");
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const handleSubmit = React.useCallback(() => {
    const q = value.trim();
    if (!q || disabled) return;
    setValue("");
    onSubmit(q);
  }, [value, disabled, onSubmit]);

  const handleKeyDown = React.useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <div className="w-full max-w-2xl mx-auto px-4 pb-4">
      {emptyState && (
        <div className="mb-4 flex flex-wrap justify-center gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              type="button"
              key={s}
              onClick={() => onSubmit(s)}
              className={cn(
                "rounded-md border border-border bg-muted px-3 py-1.5 text-sm text-muted-foreground transition-colors duration-150",
                "hover:bg-border hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-500 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              )}
            >
              {s}
            </button>
          ))}
        </div>
      )}
      <div className="flex gap-2 rounded-lg border border-border bg-card p-2">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="min-h-[44px] max-h-[120px] resize-none border-0 bg-transparent focus-visible:ring-0"
          aria-label="Message"
        />
        <Button
          type="button"
          size="icon"
          className="h-10 w-10 shrink-0"
          onClick={handleSubmit}
          disabled={!value.trim() || disabled}
          aria-label="Send"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
