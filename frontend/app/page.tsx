"use client";
import { useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [code, setCode] = useState("");
  const [output, setOutput] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);

  async function sendMessage() {
    if (!message.trim()) return;
    setLoading(true);
    setReply("");
    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      setReply(data.reply);
    } catch {
      setReply("Error connecting to LEO backend.");
    } finally {
      setLoading(false);
    }
  }

  async function runCode() {
    if (!code.trim()) return;
    setRunning(true);
    setOutput(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language: "python" }),
      });
      const data = await res.json();
      setOutput(data);
    } catch {
      setOutput({ stderr: "Error connecting to sandbox.", success: false });
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center bg-zinc-950 text-white px-4 py-12">
      <div className="w-full max-w-2xl">
        <h1 className="text-5xl font-bold tracking-tight text-center mb-2">LEO 🐐</h1>
        <p className="text-zinc-400 text-center mb-10">Your AI coding agent</p>

        {/* Chat */}
        <div className="mb-10">
          <p className="text-zinc-500 text-sm mb-2 uppercase tracking-widest">Chat</p>
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
            <div className="mt-4 bg-zinc-800 border border-zinc-700 rounded-lg p-4 text-zinc-200 leading-relaxed whitespace-pre-wrap">
              {reply}
            </div>
          )}
        </div>

        {/* Code Runner */}
        <div>
          <p className="text-zinc-500 text-sm mb-2 uppercase tracking-widest">Run Code in Sandbox</p>
          <textarea
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 font-mono text-sm h-40 resize-none"
            placeholder={"# Write Python here...\nprint('Hello from LEO sandbox 🐐')"}
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
          <button
            onClick={runCode}
            disabled={running}
            className="mt-2 bg-emerald-500 text-black font-semibold px-5 py-3 rounded-lg hover:bg-emerald-400 disabled:opacity-50 transition"
          >
            {running ? "Running..." : "▶ Run"}
          </button>

          {output && (
            <div className={`mt-4 rounded-lg p-4 font-mono text-sm border ${output.success ? "bg-zinc-800 border-zinc-700 text-emerald-400" : "bg-red-950 border-red-800 text-red-300"}`}>
              {output.stdout && <pre>{output.stdout}</pre>}
              {output.stderr && <pre className="text-red-400">{output.stderr}</pre>}
              <p className="text-xs mt-2 opacity-50">exit code: {output.exit_code}</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}