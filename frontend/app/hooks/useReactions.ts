"use client";
import { useState, useEffect } from "react";

type Reactions = Record<string, string[]>; // messageId -> emoji[]

const STORAGE_KEY = "leo_reactions";

export function useReactions() {
  const [reactions, setReactions] = useState<Reactions>({});

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setReactions(JSON.parse(stored));
    } catch {}
  }, []);

  function toggleReaction(messageId: string, emoji: string) {
    setReactions((prev) => {
      const current = prev[messageId] || [];
      const next = current.includes(emoji)
        ? current.filter((e) => e !== emoji)
        : [...current, emoji];

      const updated = { ...prev, [messageId]: next };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch {}
      return updated;
    });
  }

  function getReactions(messageId: string): string[] {
    return reactions[messageId] || [];
  }

  return { toggleReaction, getReactions };
}
