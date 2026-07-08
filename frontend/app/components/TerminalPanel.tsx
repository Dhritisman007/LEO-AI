"use client";
import { useState, useRef, useEffect } from "react";
import { Terminal, Play, X } from "lucide-react";
import { motion } from "framer-motion";

type TerminalLine = {
  type: "stdout" | "stderr" | "error" | "exit" | "system";
  content: string;
};

const LANGUAGES = [
  "python", "javascript", "java", "cpp", "c", "go", "rust", "bash"
];

export default function TerminalPanel({ onClose }: { onClose: () => void }) {
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [lines, setLines] = useState<TerminalLine[]>([]);
  const [running, setRunning] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  function runCode() {
    if (!code.trim() || running) return;

    setLines([{ type: "system", content: "$ running..." }]);
    setRunning(true);

    const ws = new WebSocket("ws://localhost:8000/ws/execute");
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ code, language }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "exit") {
        setLines((prev) => [
          ...prev,
          {
            type: "system",
            content: `process exited with code ${data.exit_code}`,
          },
        ]);
        setRunning(false);
        ws.close();
        return;
      }

      if (data.type === "error") {
        setLines((prev) => [...prev, { type: "error", content: data.content }]);
        setRunning(false);
        return;
      }

      setLines((prev) => [...prev, { type: data.type, content: data.content }]);
    };

    ws.onerror = () => {
      setLines((prev) => [...prev, { type: "error", content: "WebSocket connection failed" }]);
      setRunning(false);
    };

    ws.onclose = () => {
      setRunning(false);
    };
  }

  function lineColor(type: string) {
    if (type === "stderr") return "text-red-400";
    if (type === "error") return "text-red-400";
    if (type === "system") return "text-zinc-500 italic";
    return "text-emerald-400";
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15 }}
      className="absolute inset-0 bg-zinc-950/98 z-20 flex flex-col"
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-zinc-400" />
          <span className="text-sm font-semibold text-zinc-300">Live Terminal</span>
        </div>
        <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
          <X size={16} />
        </button>
      </div>

      <textarea
        className="bg-zinc-900 border-b border-zinc-800 px-4 py-3 text-sm font-mono text-zinc-200 placeholder-zinc-600 focus:outline-none h-28 resize-none"
        placeholder={`Write ${language} code to run live...`}
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />

      <div className="px-4 py-2 border-b border-zinc-800 flex items-center justify-between">
        <select
          className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs rounded-lg px-2 py-1.5 focus:outline-none"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          {LANGUAGES.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        <button
          onClick={runCode}
          disabled={running}
          className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-semibold px-3 py-1.5 rounded"
        >
          <Play size={12} />
          {running ? "Running..." : "Run"}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 font-mono text-xs bg-black/40">
        {lines.length === 0 && (
          <p className="text-zinc-600">Output will stream here in real time...</p>
        )}
        {lines.map((l, i) => (
          <div key={i} className={lineColor(l.type)}>
            {l.type === "stdout" || l.type === "stderr" ? "> " : ""}
            {l.content}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </motion.div>
  );
}
