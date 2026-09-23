"use client";
import { useEffect, useState } from "react";
import { X, Download, Loader2 } from "lucide-react";
import Editor from "@monaco-editor/react";
import { motion } from "framer-motion";
import { API_URL, downloadWorkspaceFile } from "../lib/api";

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
  userId,
  onClose,
}: {
  filename: string | null;
  userId: string;
  onClose: () => void;
}) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    if (!filename) return;
    setDownloading(true);
    try {
      await downloadWorkspaceFile(filename, userId);
    } catch (e) {
      console.error("Download failed:", e);
    } finally {
      setDownloading(false);
    }
  }

  useEffect(() => {
    if (!filename) return;
    setLoading(true);
    setContent("");
    fetch(`${API_URL}/workspace/file/${filename}`)
      .then((res) => res.json())
      .then((data) => setContent(data.content || ""))
      .catch(() => setContent("// Could not load file"))
      .finally(() => setLoading(false));
  }, [filename]);

  if (!filename) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15 }}
      className="absolute inset-0 bg-zinc-950/98 z-10 flex flex-col"
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">
            {getLanguage(filename)}
          </span>
          <span className="text-sm font-mono text-zinc-300">{filename}</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleDownload}
            disabled={downloading}
            title="Download file"
            className="text-zinc-500 hover:text-zinc-300 disabled:opacity-50"
          >
            {downloading ? <Loader2 size={16} className="spin" /> : <Download size={16} />}
          </button>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
            <X size={16} />
          </button>
        </div>
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
    </motion.div>
  );
}
