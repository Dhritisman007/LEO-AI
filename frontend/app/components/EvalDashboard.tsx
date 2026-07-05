"use client";
import { useState } from "react";
import { X, Play, CheckCircle2, XCircle, Loader2 } from "lucide-react";

type EvalResult = {
  id: string;
  category: string;
  passed: boolean;
  score: number;
  reason: string;
  steps_taken: number;
  max_steps: number;
  elapsed_seconds: number;
};

type EvalSummary = {
  total_cases: number;
  passed: number;
  failed: number;
  pass_rate: number;
  avg_score: number;
  avg_steps: number;
  avg_time_seconds: number;
  by_category: Record<string, { total: number; passed: number }>;
  results: EvalResult[];
};

export default function EvalDashboard({ onClose }: { onClose: () => void }) {
  const [running, setRunning] = useState(false);
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = ["basic", "functions", "file_ops", "error_handling", "reasoning"];

  async function runEvals() {
    setRunning(true);
    setSummary(null);
    try {
      const res = await fetch("http://localhost:8000/evals/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          categories: selectedCategory ? [selectedCategory] : null,
          user_id: "eval_user"
        }),
      });
      const data = await res.json();
      setSummary(data);
    } catch {
      alert("Eval run failed — check the backend");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="absolute inset-0 bg-zinc-950/98 z-20 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <span className="text-sm font-semibold text-zinc-300">🧪 LEO Eval Dashboard</span>
        <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
          <X size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Controls */}
        <div className="flex flex-wrap gap-2 mb-6 items-center">
          <select
            className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2 focus:outline-none"
            value={selectedCategory || ""}
            onChange={(e) => setSelectedCategory(e.target.value || null)}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          <button
            onClick={runEvals}
            disabled={running}
            className="flex items-center gap-2 bg-white text-black font-semibold text-sm px-4 py-2 rounded-lg hover:bg-zinc-200 disabled:opacity-40 transition"
          >
            {running
              ? <><Loader2 size={14} className="animate-spin" /> Running evals...</>
              : <><Play size={14} /> Run Evals</>
            }
          </button>

          {running && (
            <span className="text-xs text-zinc-500 italic">
              This takes a few minutes — LEO is completing each task...
            </span>
          )}
        </div>

        {/* Summary cards */}
        {summary && (
          <>
            <div className="grid grid-cols-2 gap-3 mb-6 sm:grid-cols-4">
              {[
                { label: "Pass rate", value: `${summary.pass_rate}%`, color: summary.pass_rate >= 70 ? "text-emerald-400" : "text-red-400" },
                { label: "Passed", value: `${summary.passed}/${summary.total_cases}`, color: "text-white" },
                { label: "Avg steps", value: summary.avg_steps, color: "text-white" },
                { label: "Avg time", value: `${summary.avg_time_seconds}s`, color: "text-white" },
              ].map((card) => (
                <div key={card.label} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 text-center">
                  <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
                  <div className="text-xs text-zinc-500 mt-1">{card.label}</div>
                </div>
              ))}
            </div>

            {/* Category breakdown */}
            <div className="mb-6">
              <p className="text-xs text-zinc-500 uppercase tracking-wide mb-3">By category</p>
              <div className="flex flex-col gap-2">
                {Object.entries(summary.by_category).map(([cat, stats]) => {
                  const rate = stats.passed / stats.total;
                  return (
                    <div key={cat} className="flex items-center gap-3">
                      <span className="text-xs text-zinc-400 w-28">{cat}</span>
                      <div className="flex-1 bg-zinc-800 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${rate === 1 ? "bg-emerald-500" : rate >= 0.5 ? "bg-yellow-500" : "bg-red-500"}`}
                          style={{ width: `${rate * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-zinc-400 w-12 text-right">
                        {stats.passed}/{stats.total}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Individual results */}
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wide mb-3">
                Individual results
              </p>
              <div className="flex flex-col gap-2">
                {summary.results.map((r) => (
                  <div
                    key={r.id}
                    className={`border rounded-lg p-3 ${r.passed ? "border-zinc-700 bg-zinc-900/50" : "border-red-900 bg-red-950/30"}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {r.passed
                        ? <CheckCircle2 size={14} className="text-emerald-400 flex-shrink-0" />
                        : <XCircle size={14} className="text-red-400 flex-shrink-0" />
                      }
                      <span className="text-sm font-medium text-zinc-200">{r.id}</span>
                      <span className="text-xs text-zinc-600 ml-auto">{r.category}</span>
                    </div>
                    <p className="text-xs text-zinc-500 ml-5">{r.reason}</p>
                    <div className="flex gap-3 ml-5 mt-1 text-[11px] text-zinc-600">
                      <span>steps: {r.steps_taken}/{r.max_steps}</span>
                      <span>time: {r.elapsed_seconds}s</span>
                      <span>score: {r.score.toFixed(1)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
