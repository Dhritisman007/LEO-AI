"use client";
import { useEffect, useState } from "react";
import { File, Folder, FolderOpen, RefreshCw, Download, Loader2 } from "lucide-react";
import { API_URL, downloadWorkspaceFile } from "../lib/api";

type TreeNode = {
  name: string;
  type: "file" | "folder";
  size?: number;
  children?: TreeNode[];
};

function FileTreeNode({
  node,
  depth,
  onSelect,
  selected,
  userId,
}: {
  node: TreeNode;
  depth: number;
  onSelect: (name: string) => void;
  selected: string | null;
  userId: string;
}) {
  const [open, setOpen] = useState(true);
  const [downloading, setDownloading] = useState(false);

  if (node.type === "folder") {
    return (
      <div>
        {node.name !== "workspace" && (
          <button
            onClick={() => setOpen(!open)}
            className="flex items-center gap-1.5 w-full text-left px-2 py-1 rounded hover:bg-zinc-800 text-zinc-400 text-xs"
            style={{ paddingLeft: `${depth * 12 + 8}px` }}
          >
            {open ? <FolderOpen size={13} /> : <Folder size={13} />}
            {node.name}
          </button>
        )}
        {open &&
          node.children?.map((child, i) => (
            <FileTreeNode
              key={i}
              node={child}
              depth={node.name === "workspace" ? depth : depth + 1}
              onSelect={onSelect}
              selected={selected}
              userId={userId}
            />
          ))}
      </div>
    );
  }

  const isSelected = selected === node.name;

  async function handleDownload(e: React.MouseEvent) {
    e.stopPropagation();
    setDownloading(true);
    try {
      await downloadWorkspaceFile(node.name, userId);
    } catch (err) {
      console.error("Download failed:", err);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div
      onClick={() => onSelect(node.name)}
      className={`group flex items-center gap-1.5 w-full text-left px-2 py-1 rounded text-xs transition cursor-pointer ${
        isSelected ? "bg-zinc-700 text-white" : "text-zinc-300 hover:bg-zinc-800"
      }`}
      style={{ paddingLeft: `${depth * 12 + 8}px` }}
    >
      <File size={13} className="flex-shrink-0" />
      <span className="truncate flex-1">{node.name}</span>
      <button
        onClick={handleDownload}
        disabled={downloading}
        title="Download file"
        className="opacity-0 group-hover:opacity-100 flex-shrink-0 text-zinc-500 hover:text-zinc-200 disabled:opacity-50 transition-opacity"
      >
        {downloading ? <Loader2 size={12} className="spin" /> : <Download size={12} />}
      </button>
    </div>
  );
}

export default function FileTree({
  onFileSelect,
  refreshTrigger,
  userId,
}: {
  onFileSelect: (filename: string) => void;
  refreshTrigger: number;
  userId: string;
}) {
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function fetchTree() {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/workspace/tree?user_id=${encodeURIComponent(userId)}`);
      const data = await res.json();
      if (data.success) setTree(data.tree);
    } catch {
      // silent fail — sidebar just stays empty
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchTree();
  }, [refreshTrigger, userId]);

  function handleSelect(filename: string) {
    setSelected(filename);
    onFileSelect(filename);
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-3 py-3 border-b border-zinc-800">
        <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">
          Workspace
        </span>
        <button onClick={fetchTree} className="text-zinc-500 hover:text-zinc-300">
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        {!tree || tree.children?.length === 0 ? (
          <p className="text-zinc-600 text-xs px-3 py-2">No files yet</p>
        ) : (
          <FileTreeNode node={tree} depth={0} onSelect={handleSelect} selected={selected} userId={userId} />
        )}
      </div>
    </div>
  );
}
