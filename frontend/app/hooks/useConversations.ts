"use client";
import { useState, useEffect } from "react";
import { Conversation, Message } from "../types";

const STORAGE_KEY = "leo_conversations";
const MAX_CONVERSATIONS = 30;

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed: Conversation[] = JSON.parse(stored);
        setConversations(parsed);
        // Resume the most recent conversation
        if (parsed.length > 0) {
          setActiveConversationId(parsed[0].id);
        }
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    } finally {
      setLoaded(true);
    }
  }, []);

  // Persist whenever conversations change
  useEffect(() => {
    if (!loaded) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.slice(0, MAX_CONVERSATIONS)));
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [conversations, loaded]);

  function createConversation(): Conversation {
    const convo: Conversation = {
      id: crypto.randomUUID(),
      title: "New conversation",
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    setConversations((prev) => [convo, ...prev]);
    setActiveConversationId(convo.id);
    return convo;
  }

  function updateConversation(id: string, messages: Message[]) {
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== id) return c;
        // Title = first user message, truncated to 40 chars
        const firstUser = messages.find((m) => m.role === "user");
        const title = firstUser
          ? firstUser.content.slice(0, 40) + (firstUser.content.length > 40 ? "..." : "")
          : "New conversation";
        return { ...c, title, messages, updatedAt: Date.now() };
      })
    );
  }

  function updateMessage(convoId: string, messageId: string, updater: (m: Message) => Message) {
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== convoId) return c;
        const newMessages = c.messages.map((m) => (m.id === messageId ? updater(m) : m));
        return { ...c, messages: newMessages, updatedAt: Date.now() };
      })
    );
  }

  function deleteConversation(id: string) {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeConversationId === id) {
      setActiveConversationId(null);
    }
  }

  function getActiveConversation(): Conversation | null {
    return conversations.find((c) => c.id === activeConversationId) || null;
  }

  function switchConversation(id: string) {
    setActiveConversationId(id);
  }

  function renameConversation(id: string, newTitle: string) {
    setConversations((prev) =>
      prev.map((c) =>
        c.id === id ? { ...c, title: newTitle, updatedAt: Date.now() } : c
      )
    );
  }

  return {
    conversations,
    activeConversationId,
    loaded,
    createConversation,
    updateConversation,
    updateMessage,
    deleteConversation,
    getActiveConversation,
    switchConversation,
    renameConversation,
  };
}
