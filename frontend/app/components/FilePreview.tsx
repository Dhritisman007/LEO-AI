"use client";
import { useEffect, useState } from "react";
import { X } from "lucide-react";
import Editor from "@monaco-editor/react";

function getLanguage(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase();
  const map: Record<string, string> = {
    py: "python",
    js: "javascript",
    ts: "typescript",
    tsx: "typescript",
    jsx: "javascript",
    json: "json",
    md: "markdown",
    txt: "plaintext",
    html: "html",
    css: "css",
    sh: "shell",
    yaml: "yaml",
    yml: "yaml",
    toml: "ini",
  };
  return map[ext || ""] || "plaintext";
}

export default function FilePreview({
  filename,
  onClose,
}: {
  filename: string | null;
  onClose: () => void;
}) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!filename) return;
    setLoading(true);
    setContent("");
    fetch(`http://localhost:8000/workspace/file/${filename}`)
      .then((res) => res.json())
      .then((data) => setContent(data.content || ""))
      .catch(() => setContent("// Could not load file"))
      .finally(() => setLoading(false));
  }, [filename]);

  if (!filename) return null;

  return (
    <div className="absolute inset-0 bg-zinc-950/98 z-10 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">
            {getLanguage(filename)}
          </span>
          <span className="text-sm font-mono text-zinc-300">{filename}</span>
        </div>
        <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
          <X size={16} />
        </button>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-zinc-600 text-sm">
          Loading...
        </div>
      ) : (
        <div className="flex-1">
          <Editor
            height="100%"
            language={getLanguage(filename)}
            value={content}
            theme="vs-dark"
            options={{
              readOnly: true,
              fontSize: 13,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: "on",
              folding: true,
              wordWrap: "on",
              padding: { top: 16 },
            }}
          />
        </div>
      )}
    </div>
  );
}
