"use client";
import { useState, useCallback } from "react";

export type AttachedFile = {
  id: string;
  name: string;
  size: number;
  type: string;
  content: string | null;   // text content for preview
  raw: File;                // original File object for upload
  preview?: string;         // for images
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const SUPPORTED_TYPES = [
  "text/plain",
  "text/markdown",
  "text/csv",
  "application/json",
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/gif",
  "image/webp",
];

const CODE_EXTENSIONS = [
  ".py", ".js", ".ts", ".tsx", ".jsx",
  ".java", ".cpp", ".c", ".go", ".rs",
  ".html", ".css", ".scss", ".sql",
  ".yaml", ".yml", ".toml", ".env",
  ".sh", ".bash", ".zsh",
];

function isSupported(file: File): boolean {
  if (SUPPORTED_TYPES.includes(file.type)) return true;
  const ext = "." + file.name.split(".").pop()?.toLowerCase();
  return CODE_EXTENSIONS.includes(ext);
}

function getFileIcon(file: AttachedFile): string {
  if (file.type.startsWith("image/")) return "🖼️";
  if (file.type === "application/pdf") return "📄";
  if (file.type === "application/json") return "📋";
  if (file.type === "text/csv") return "📊";
  const ext = "." + file.name.split(".").pop()?.toLowerCase();
  if ([".py"].includes(ext)) return "🐍";
  if ([".js", ".ts", ".tsx", ".jsx"].includes(ext)) return "⚡";
  if ([".java"].includes(ext)) return "☕";
  if ([".cpp", ".c"].includes(ext)) return "⚙️";
  if ([".go"].includes(ext)) return "🔵";
  if ([".rs"].includes(ext)) return "🦀";
  if ([".md"].includes(ext)) return "📝";
  return "📎";
}

export { getFileIcon };

export function useFileAttachment() {
  const [attachments, setAttachments] = useState<AttachedFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const addFiles = useCallback(async (files: FileList | File[]) => {
    setError(null);
    const fileArray = Array.from(files);

    for (const file of fileArray) {
      if (file.size > MAX_FILE_SIZE) {
        setError(`${file.name} is too large (max 10MB)`);
        continue;
      }

      if (!isSupported(file)) {
        setError(`${file.name} — unsupported file type`);
        continue;
      }

      const id = crypto.randomUUID();
      let content: string | null = null;
      let preview: string | undefined;

      if (file.type.startsWith("image/")) {
        preview = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target?.result as string);
          reader.readAsDataURL(file);
        });
      } else if (file.type !== "application/pdf") {
        content = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target?.result as string);
          reader.readAsText(file);
        });
      }

      setAttachments((prev) => [
        ...prev,
        { id, name: file.name, size: file.size, type: file.type, content, raw: file, preview }
      ]);
    }
  }, []);

  const removeAttachment = useCallback((id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const clearAttachments = useCallback(() => {
    setAttachments([]);
  }, []);

  return { attachments, error, addFiles, removeAttachment, clearAttachments };
}
