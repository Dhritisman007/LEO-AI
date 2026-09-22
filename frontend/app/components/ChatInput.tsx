"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { Send, Mic, MicOff, Loader2, Paperclip } from "lucide-react";
import { useVoiceInput } from "../hooks/useVoiceInput";
import { AttachedFile } from "../hooks/useFileAttachment";
import AttachmentStrip from "./AttachmentStrip";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
  inputRef?: React.RefObject<HTMLTextAreaElement | null>;
  attachments: AttachedFile[];
  onAttach: (files: FileList | File[]) => void;
  onRemoveAttachment: (id: string) => void;
  attachError: string | null;
  isMultiAgent?: boolean;
  onToggleMultiAgent?: () => void;
};

const MAX_CHARS = 500;

export default function ChatInput({
  value, onChange, onSend, disabled,
  inputRef, attachments, onAttach,
  onRemoveAttachment, attachError,
  isMultiAgent, onToggleMultiAgent
}: Props) {
  const internalRef = useRef<HTMLTextAreaElement>(null);
  const ref = inputRef || internalRef;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const charCount = value.length;
  const nearLimit = charCount > MAX_CHARS * 0.8;
  const atLimit = charCount >= MAX_CHARS;

  const { listening, startListening, stopListening } = useVoiceInput((t) =>
    onChange(value ? value + " " + t : t)
  );

  // Auto-resize
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length > 0) {
      onAttach(e.dataTransfer.files);
    }
  }, [onAttach]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      onSend();
      return;
    }
    if (e.key === "Enter" && !e.shiftKey && !e.metaKey && !value.includes("\n")) {
      e.preventDefault();
      onSend();
    }
  }

  return (
    <div className="chat-input-wrap">
      {/* Attachment strip above input */}
      {attachments.length > 0 && (
        <AttachmentStrip
          attachments={attachments}
          onRemove={onRemoveAttachment}
        />
      )}

      {/* Error message */}
      {attachError && (
        <div className="attachment-error">{attachError}</div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="sr-only"
        accept=".py,.js,.ts,.tsx,.jsx,.java,.cpp,.c,.go,.rs,.html,.css,.scss,.sql,.yaml,.yml,.toml,.sh,.txt,.md,.json,.csv,.pdf,.png,.jpg,.jpeg,.gif,.webp"
        onChange={(e) => e.target.files && onAttach(e.target.files)}
      />

      {/* Main input box */}
      <div
        className={`chat-input-box ${atLimit ? "chat-input-box--limit" : ""} ${dragging ? "chat-input-box--dragging" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {dragging ? (
          <div className="chat-input-drop-zone">
            <span className="chat-input-drop-icon">📎</span>
            <span className="chat-input-drop-text">Drop files here</span>
          </div>
        ) : (
          <>
            <textarea
              ref={ref}
              className="chat-input-field"
              placeholder="Ask LEO to build something... (⌘↵ to send)"
              value={value}
              rows={1}
              maxLength={MAX_CHARS}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={handleKeyDown}
            />

            <div className="chat-input-actions">
              {nearLimit && (
                <span className={`chat-input-counter ${atLimit ? "chat-input-counter--limit" : ""}`}>
                  {charCount}/{MAX_CHARS}
                </span>
              )}

              {/* Attach button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="chat-input-attach"
                title="Attach file"
                disabled={disabled}
              >
                <Paperclip size={15} />
                {attachments.length > 0 && (
                  <span className="chat-input-attach-badge">
                    {attachments.length}
                  </span>
                )}
              </button>

              {/* Mic button */}
              <button
                onClick={listening ? stopListening : startListening}
                className={`chat-input-mic ${listening ? "chat-input-mic--active" : ""}`}
                title="Voice input"
              >
                {listening ? <MicOff size={15} /> : <Mic size={15} />}
              </button>

              {/* Send button */}
              <button
                onClick={onSend}
                disabled={disabled || (!value.trim() && attachments.length === 0) || atLimit}
                className="chat-input-send"
                title="Send (⌘↵)"
              >
                {disabled
                  ? <Loader2 size={15} className="spin" />
                  : <Send size={15} />
                }
              </button>
            </div>
          </>
        )}
      </div>

      <div className="chat-input-footer flex justify-between items-center w-full px-1">
        <span className="chat-input-hint">
          ⌘K focus · ⌘N new · ⌘/ terminal · ⌘↵ send · Drag files to attach
        </span>
        <div className="flex items-center gap-2">
          {onToggleMultiAgent && (
            <label className="flex items-center gap-1.5 text-[10px] text-gray-500 cursor-pointer hover:text-gray-300">
              <input 
                type="checkbox" 
                checked={isMultiAgent} 
                onChange={onToggleMultiAgent}
                className="accent-indigo-500 cursor-pointer"
              />
              Multi-Agent Mode
            </label>
          )}
          {listening && (
            <span className="chat-input-listening">🔴 Listening...</span>
          )}
        </div>
      </div>
    </div>
  );
}
