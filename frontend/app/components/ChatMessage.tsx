"use client";
import { useState } from "react";
import { Wrench, CheckCircle2, XCircle, Brain, Loader2, BookOpen, Copy, Check, Bot } from "lucide-react";
import { Message } from "../types";
import PlanTracker from "./PlanTracker";
import ExplainPanel from "./ExplainPanel";

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

function extractCodeFromMessage(message: Message): { code: string; filename: string } | null {
  // Look through tool call steps for write_file calls
  const writeSteps = message.steps?.filter(
    (s) => s.type === "tool_call" && s.tool === "write_file" && s.params?.content
  );
  if (writeSteps && writeSteps.length > 0) {
    const lastWrite = writeSteps[writeSteps.length - 1];
    return {
      code: lastWrite.params.content,
      filename: lastWrite.params.filename || "unknown",
    };
  }
  // Fallback — check if final answer contains a code block
  if (message.content.includes("```")) {
    const match = message.content.match(/```[\w]*\n([\s\S]*?)```/);
    if (match) {
      return { code: match[1], filename: "snippet" };
    }
  }
  return null;
}

function getUserTask(message: Message, allMessages: Message[]): string {
  // Find the user message that preceded this LEO message
  const idx = allMessages.findIndex((m) => m.id === message.id);
  if (idx > 0) {
    const prev = allMessages[idx - 1];
    if (prev.role === "user") return prev.content;
  }
  return "";
}

type Props = {
  message: Message;
  allMessages: Message[];
  userId: string;
};

export default function ChatMessage({ message, allMessages, userId }: Props) {
  const [showExplain, setShowExplain] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState("");
  const [copied, setCopied] = useState(false);

  const codeInfo = message.role === "leo" ? extractCodeFromMessage(message) : null;
  const hasCode = codeInfo !== null;

  async function handleExplain() {
    if (!codeInfo) return;
    setShowExplain(true);
    setExplaining(true);
    setExplanation("");

    const task = getUserTask(message, allMessages);

    try {
      const res = await fetch("http://localhost:8000/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: codeInfo.code,
          filename: codeInfo.filename,
          task,
          user_id: userId,
        }),
      });

      if (!res.body) throw new Error("No response body");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setExplanation((prev) => prev + chunk);
      }
    } catch {
      setExplanation("Could not generate explanation.");
    } finally {
      setExplaining(false);
    }
  }

  function handleCopy() {
    if (!codeInfo) return;
    navigator.clipboard.writeText(codeInfo.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

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
          <Bot size={18} className="text-zinc-300" />
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">LEO</span>
          {message.status === "pending" && (
            <Loader2 size={12} className="animate-spin text-zinc-500" />
          )}
        </div>

        {/* Plan tracker */}
        {message.plan && <PlanTracker plan={message.plan} />}

        {/* Memory hint */}
        {message.recalled_memories && message.recalled_memories.length > 0 && (
          <div className="text-[11px] text-zinc-500 mb-3 italic">
            🧠 Recalled {message.recalled_memories.length} similar past task
            {message.recalled_memories.length > 1 ? "s" : ""}
          </div>
        )}

        {/* Step trace */}
        {message.steps && message.steps.length > 0 && (
          <div className="flex flex-col gap-2 mb-3">
            {message.steps.map((s, index) => (
              <div
                key={index}
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

        {/* Action buttons — only show when LEO is done and has code */}
        {message.status === "done" && hasCode && (
          <div className="flex items-center gap-2 mt-2">
            <button
              onClick={handleExplain}
              disabled={explaining}
              className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-blue-400 border border-zinc-700 hover:border-blue-700 rounded-lg px-3 py-1.5 transition"
            >
              {explaining ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <BookOpen size={12} />
              )}
              {showExplain ? "Re-explain" : "Explain this code"}
            </button>

            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 border border-zinc-700 hover:border-zinc-500 rounded-lg px-3 py-1.5 transition"
            >
              {copied ? (
                <><Check size={12} className="text-emerald-400" /> Copied!</>
              ) : (
                <><Copy size={12} /> Copy code</>
              )}
            </button>
          </div>
        )}

        {/* Explanation panel */}
        {showExplain && (
          <ExplainPanel
            explanation={explanation}
            loading={explaining}
            onClose={() => {
              setShowExplain(false);
              setExplanation("");
            }}
          />
        )}
      </div>
    </div>
  );
}
