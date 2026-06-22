"use client";
import { useEffect, useState } from "react";
import { File, Folder, FolderOpen, RefreshCw } from "lucide-react";

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
}: {
  node: TreeNode;
  depth: number;
  onSelect: (name: string) => void;
  selected: string | null;
}) {
  const [open, setOpen] = useState(true);

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
            />
          ))}
      </div>
    );
  }

  const isSelected = selected === node.name;

  return (
    <button
      onClick={() => onSelect(node.name)}
      className={`flex items-center gap-1.5 w-full text-left px-2 py-1 rounded text-xs transition ${
        isSelected ? "bg-zinc-700 text-white" : "text-zinc-300 hover:bg-zinc-800"
      }`}
      style={{ paddingLeft: `${depth * 12 + 8}px` }}
    >
      <File size={13} />
      <span className="truncate">{node.name}</span>
    </button>
  );
}

export default function FileTree({
  onFileSelect,
  refreshTrigger,
}: {
  onFileSelect: (filename: string) => void;
  refreshTrigger: number;
}) {
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function fetchTree() {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8001/workspace/tree");
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
  }, [refreshTrigger]);

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
          <FileTreeNode node={tree} depth={0} onSelect={handleSelect} selected={selected} />
        )}
      </div>
    </div>
  );
}
