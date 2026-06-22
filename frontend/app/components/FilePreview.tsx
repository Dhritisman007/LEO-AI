"use client";
import { useEffect, useState } from "react";
import { X } from "lucide-react";

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
    fetch(`http://127.0.0.1:8001/workspace/file/${filename}`)
      .then((res) => res.json())
      .then((data) => setContent(data.content || ""))
      .catch(() => setContent("Couldn't load file."))
      .finally(() => setLoading(false));
  }, [filename]);

  if (!filename) return null;

  return (
    <div className="absolute inset-0 bg-zinc-950/95 z-10 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <span className="text-sm font-mono text-zinc-300">{filename}</span>
        <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
          <X size={16} />
        </button>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {loading ? (
          <p className="text-zinc-500 text-sm">Loading...</p>
        ) : (
          <pre className="text-xs text-zinc-300 font-mono whitespace-pre-wrap">{content}</pre>
        )}
      </div>
    </div>
  );
}
