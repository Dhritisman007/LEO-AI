"use client";
import { useState } from "react";

type Step = {
  step: number;
  type: "tool_call" | "thought" | "done" | "error";
  tool?: string;
  params?: any;
  result?: any;
  content?: string;
  thought?: string;
};

export default function Home() {
  const [task, setTask] = useState("");
  const [steps, setSteps] = useState<Step[]>([]);
  const [finalAnswer, setFinalAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  async function runAgent() {
    if (!task.trim()) return;
    setLoading(true);
    setSteps([]);
    setFinalAnswer("");

    try {
      const res = await fetch("http://127.0.0.1:8000/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, max_steps: 10 }),
      });
      const data = await res.json();
      setSteps(data.steps || []);
      setFinalAnswer(data.final_answer || "");
    } catch {
      setFinalAnswer("Error connecting to LEO.");
    } finally {
      setLoading(false);
    }
  }

  function stepColor(type: string) {
    if (type === "tool_call") return "border-blue-600 bg-blue-950";
    if (type === "done") return "border-emerald-600 bg-emerald-950";
    if (type === "error") return "border-red-600 bg-red-950";
    return "border-zinc-600 bg-zinc-800";
  }

  function stepIcon(type: string) {
    if (type === "tool_call") return "🔧";
    if (type === "done") return "✅";
    if (type === "error") return "❌";
    return "💭";
  }

  return (
    <main className="flex min-h-screen flex-col items-center bg-zinc-950 text-white px-4 py-12">
      <div className="w-full max-w-2xl">
        <h1 className="text-5xl font-bold tracking-tight text-center mb-2">LEO 🐐</h1>
        <p className="text-zinc-400 text-center mb-10">Autonomous AI coding agent</p>

        {/* Task input */}
        <div className="mb-8">
          <p className="text-zinc-500 text-sm mb-2 uppercase tracking-widest">Give LEO a task</p>
          <textarea
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 text-sm h-28 resize-none"
            placeholder="Write a Python script that sorts a list of numbers and run it..."
            value={task}
            onChange={(e) => setTask(e.target.value)}
          />
          <button
            onClick={runAgent}
            disabled={loading}
            className="mt-2 w-full bg-white text-black font-bold py-3 rounded-lg hover:bg-zinc-200 disabled:opacity-50 transition text-sm"
          >
            {loading ? "LEO is working... 🐐" : "▶ Run Agent"}
          </button>
        </div>

        {/* Steps */}
        {steps.length > 0 && (
          <div className="mb-8">
            <p className="text-zinc-500 text-sm mb-3 uppercase tracking-widest">Agent steps</p>
            <div className="flex flex-col gap-3">
              {steps.map((s) => (
                <div
                  key={s.step}
                  className={`border rounded-lg p-4 text-sm ${stepColor(s.type)}`}
                >
                  <div className="flex items-center gap-2 mb-1 font-semibold">
                    <span>{stepIcon(s.type)}</span>
                    <span>Step {s.step} — {s.type === "tool_call" ? `Tool: ${s.tool}` : s.type}</span>
                  </div>

                  {s.type === "tool_call" && (
                    <>
                      {s.params && (
                        <pre className="text-xs text-zinc-400 mt-1 overflow-x-auto">
                          params: {JSON.stringify(s.params, null, 2)}
                        </pre>
                      )}
                      {s.result && (
                        <pre className="text-xs text-zinc-300 mt-2 overflow-x-auto">
                          result: {JSON.stringify(s.result, null, 2)}
                        </pre>
                      )}
                    </>
                  )}

                  {(s.type === "thought" || s.type === "done" || s.type === "error") && (
                    <p className="text-zinc-300 mt-1 whitespace-pre-wrap">{s.content}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Final answer */}
        {finalAnswer && (
          <div className="bg-emerald-950 border border-emerald-700 rounded-lg p-4">
            <p className="text-emerald-400 font-semibold mb-1">✅ LEO's final answer</p>
            <p className="text-zinc-200 text-sm whitespace-pre-wrap">{finalAnswer}</p>
          </div>
        )}
      </div>
    </main>
  );
}