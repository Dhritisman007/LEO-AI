"use client";
import { Wrench, CheckCircle2, XCircle, Brain, Loader2 } from "lucide-react";
import { Message } from "../types";

function stepIcon(type: string) {
  if (type === "tool_call") return <Wrench size={14} />;
  if (type === "done") return <CheckCircle2 size={14} />;
  if (type === "error") return <XCircle size={14} />;
  return <Brain size={14} />;
}

function stepColor(type: string) {
  if (type === "tool_call") return "border-blue-700 bg-blue-950/50 text-blue-300";
  if (type === "done") return "border-emerald-700 bg-emerald-950/50 text-emerald-300";
  if (type === "error") return "border-red-700 bg-red-950/50 text-red-300";
  return "border-zinc-700 bg-zinc-800/50 text-zinc-300";
}

export default function ChatMessage({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div className="bg-white text-black rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[80%] text-sm">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[85%] w-full">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg">🐐</span>
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">LEO</span>
          {message.status === "pending" && (
            <Loader2 size={12} className="animate-spin text-zinc-500" />
          )}
        </div>

        {/* Agent steps trace */}
        {message.steps && message.steps.length > 0 && (
          <div className="flex flex-col gap-2 mb-3">
            {message.steps.map((s) => (
              <div
                key={s.step}
                className={`border rounded-lg px-3 py-2 text-xs ${stepColor(s.type)}`}
              >
                <div className="flex items-center gap-2 font-medium">
                  {stepIcon(s.type)}
                  <span>
                    {s.type === "tool_call"
                      ? `Using ${s.tool}`
                      : s.type === "done"
                      ? "Task complete"
                      : s.type === "error"
                      ? "Stopped"
                      : "Thinking"}
                  </span>
                </div>
                {s.type === "tool_call" && s.params && (
                  <pre className="mt-1 text-[11px] opacity-60 overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(s.params, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Final reply bubble */}
        {message.content && (
          <div
            className={`rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm whitespace-pre-wrap ${
              message.status === "error"
                ? "bg-red-950/50 border border-red-800 text-red-200"
                : "bg-zinc-800 text-zinc-100"
            }`}
          >
            {message.content}
          </div>
        )}
      </div>
    </div>
  );
}
