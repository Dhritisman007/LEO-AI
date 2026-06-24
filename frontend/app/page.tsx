"use client";
import { useState, useRef, useEffect } from "react";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import { Message } from "./types";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || sending) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
      status: "done",
      timestamp: Date.now(),
    };

    const leoMsgId = crypto.randomUUID();
    const leoMsg: Message = {
      id: leoMsgId,
      role: "leo",
      content: "",
      steps: [],
      status: "pending",
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg, leoMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await fetch("http://127.0.0.1:8001/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: userMsg.content, max_steps: 10 }),
      });
      const data = await res.json();

      setMessages((prev) =>
        prev.map((m) =>
          m.id === leoMsgId
            ? {
                ...m,
                content: data.final_answer || "No response.",
                steps: data.steps || [],
                plan: data.plan || [],
                status: data.final_answer?.startsWith("ERROR") ? "error" : "done",
              }
            : m
        )
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === leoMsgId
            ? { ...m, content: "Couldn't reach LEO backend. Is it running on port 8001?", status: "error" }
            : m
        )
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="flex flex-col h-screen bg-zinc-950 text-white">
      {/* Header */}
      <div className="border-b border-zinc-800 px-6 py-4 flex items-center gap-2">
        <span className="text-2xl">🐐</span>
        <span className="font-bold text-lg">LEO</span>
        <span className="text-zinc-500 text-sm ml-1">— autonomous coding agent</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl mx-auto">
          {messages.length === 0 && (
            <div className="text-center text-zinc-500 mt-20">
              <p className="text-lg">Give LEO a task to get started 🐐</p>
              <p className="text-sm mt-2 text-zinc-600">
                Try: "Write a Python script that sorts a list and run it"
              </p>
            </div>
          )}
          {messages.map((m) => (
            <ChatMessage key={m.id} message={m} />
          ))}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={handleSend}
        disabled={sending}
      />
    </main>
  );
}