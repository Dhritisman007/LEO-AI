"use client";
import { X, FileText, Image } from "lucide-react";
import { AttachedFile, getFileIcon } from "../hooks/useFileAttachment";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

export default function AttachmentStrip({
  attachments,
  onRemove,
}: {
  attachments: AttachedFile[];
  onRemove: (id: string) => void;
}) {
  if (attachments.length === 0) return null;

  return (
    <div className="attachment-strip">
      {attachments.map((file) => (
        <div key={file.id} className="attachment-chip">
          {file.preview ? (
            <img
              src={file.preview}
              alt={file.name}
              className="attachment-chip__thumb"
            />
          ) : (
            <span className="attachment-chip__icon">
              {getFileIcon(file)}
            </span>
          )}
          <div className="attachment-chip__info">
            <span className="attachment-chip__name">{file.name}</span>
            <span className="attachment-chip__size">{formatSize(file.size)}</span>
          </div>
          <button
            className="attachment-chip__remove"
            onClick={() => onRemove(file.id)}
            title="Remove"
          >
            <X size={11} />
          </button>
        </div>
      ))}
    </div>
  );
}
