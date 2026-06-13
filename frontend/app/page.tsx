"use client";
import { useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    if (!message.trim()) return;
    setLoading(true);
    setReply("");
    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      setReply(data.reply);
    } catch (e) {
      setReply("Error connecting to LEO backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 text-white px-4">
      <div className="w-full max-w-xl">
        <h1 className="text-5xl font-bold tracking-tight text-center mb-2">LEO 🐐</h1>
        <p className="text-zinc-400 text-center mb-8">Your AI coding agent</p>

        <div className="flex gap-2">
          <input
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500"
            placeholder="Ask LEO anything..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            className="bg-white text-black font-semibold px-5 py-3 rounded-lg hover:bg-zinc-200 disabled:opacity-50 transition"
          >
            {loading ? "..." : "Send"}
          </button>
        </div>

        {reply && (
          <div className="mt-6 bg-zinc-800 border border-zinc-700 rounded-lg p-4 text-zinc-200 leading-relaxed whitespace-pre-wrap">
            {reply}
          </div>
        )}
      </div>
    </main>
  );
}