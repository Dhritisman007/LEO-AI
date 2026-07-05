"use client";
import { useState, useEffect } from "react";
import { Message } from "../types";

const STORAGE_KEY = "leo_messages";
const MAX_STORED = 50; // keep last 50 messages

export function usePersistedMessages() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loaded, setLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed: Message[] = JSON.parse(stored);
        // Mark any "pending" messages as error — they never finished
        const cleaned = parsed.map((m) =>
          m.status === "pending" ? { ...m, status: "error" as const, content: "Session interrupted." } : m
        );
        setMessages(cleaned);
      }
    } catch {
      // corrupt storage — start fresh
      localStorage.removeItem(STORAGE_KEY);
    } finally {
      setLoaded(true);
    }
  }, []);

  // Save to localStorage whenever messages change
  useEffect(() => {
    if (!loaded) return;
    try {
      const toStore = messages.slice(-MAX_STORED);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
    } catch {
      // storage full — clear and retry
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [messages, loaded]);

  function clearMessages() {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  }

  return { messages, setMessages, clearMessages, loaded };
}
