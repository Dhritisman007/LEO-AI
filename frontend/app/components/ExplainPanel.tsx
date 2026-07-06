"use client";
import { X, Loader2 } from "lucide-react";

type Props = {
  explanation: string;
  loading: boolean;
  onClose: () => void;
};

function renderExplanation(text: string) {
  // Simple markdown-like rendering for bold and code
  const lines = text.split("\n");
  return lines.map((line, i) => {
    // Bold headers like **What it does**
    if (line.startsWith("**") && line.includes("**", 2)) {
      const content = line.replace(/\*\*(.*?)\*\*/g, "$1");
      return (
        <p key={i} className="font-semibold text-white mt-4 mb-1">
          {content}
        </p>
      );
    }
    // Numbered points
    if (/^\d+\./.test(line)) {
      return (
        <p key={i} className="font-semibold text-white mt-4 mb-1">
          {line}
        </p>
      );
    }
    // Inline code
    if (line.includes("`")) {
      const parts = line.split("`");
      return (
        <p key={i} className="text-zinc-300 text-sm leading-relaxed">
          {parts.map((part, j) =>
            j % 2 === 1 ? (
              <code key={j} className="bg-zinc-800 text-emerald-400 px-1 py-0.5 rounded text-xs font-mono">
                {part}
              </code>
            ) : (
              part
            )
          )}
        </p>
      );
    }
    // Empty line
    if (!line.trim()) return <div key={i} className="h-1" />;
    // Normal line
    return (
      <p key={i} className="text-zinc-300 text-sm leading-relaxed">
        {line}
      </p>
    );
  });
}

export default function ExplainPanel({ explanation, loading, onClose }: Props) {
  return (
    <div className="mt-3 border border-blue-800 bg-blue-950/30 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-blue-800/50">
        <div className="flex items-center gap-2">
          <span className="text-sm">🧠</span>
          <span className="text-xs font-semibold text-blue-300 uppercase tracking-wide">
            Code Explanation
          </span>
          {loading && <Loader2 size={12} className="animate-spin text-blue-400" />}
        </div>
        <button onClick={onClose} className="text-blue-600 hover:text-blue-300">
          <X size={14} />
        </button>
      </div>
      <div className="px-4 py-3 max-h-96 overflow-y-auto">
        {loading && !explanation ? (
          <div className="flex items-center gap-2 text-blue-400 text-sm">
            <Loader2 size={14} className="animate-spin" />
            LEO is reading the code...
          </div>
        ) : (
          <div>{renderExplanation(explanation)}</div>
        )}
      </div>
    </div>
  );
}
