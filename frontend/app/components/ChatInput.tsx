"use client";
import { useEffect, useRef } from "react";
import { Send, Mic, MicOff, Loader2, Users } from "lucide-react";
import { useVoiceInput } from "../hooks/useVoiceInput";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
  inputRef?: React.RefObject<HTMLTextAreaElement | null>;
  isMultiAgent: boolean;
  onToggleMultiAgent: () => void;
};

const MAX_CHARS = 500;

export default function ChatInput({ value, onChange, onSend, disabled, inputRef, isMultiAgent, onToggleMultiAgent }: Props) {
  const internalRef = useRef<HTMLTextAreaElement>(null);
  const ref = inputRef || internalRef;
  const charCount = value.length;
  const nearLimit = charCount > MAX_CHARS * 0.8;
  const atLimit = charCount >= MAX_CHARS;

  const { listening, startListening, stopListening } = useVoiceInput((t) =>
    onChange(value ? value + " " + t : t)
  );

  // Auto-resize logic
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    const newHeight = Math.min(el.scrollHeight, 160); // max ~6 lines
    el.style.height = `${newHeight}px`;
  }, [value]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Cmd+Enter or Ctrl+Enter to send
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      onSend();
      return;
    }
    // Shift+Enter = newline (default textarea behavior)
    // Plain Enter = also send for single-line messages
    if (e.key === "Enter" && !e.shiftKey && !e.metaKey) {
      if (!value.includes("\n")) {
        e.preventDefault();
        onSend();
      }
    }
  }

  return (
    <div className="chat-input-wrap">
      <div className={`chat-input-box ${atLimit ? "chat-input-box--limit" : ""}`}>
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
          {/* Character counter — only show when approaching limit */}
          {nearLimit && (
            <span className={`chat-input-counter ${atLimit ? "chat-input-counter--limit" : ""}`}>
              {charCount}/{MAX_CHARS}
            </span>
          )}

          <button
            onClick={listening ? stopListening : startListening}
            className={`chat-input-mic ${listening ? "chat-input-mic--active" : ""}`}
            title="Voice input"
          >
            {listening ? <MicOff size={15} /> : <Mic size={15} />}
          </button>

          <button
            onClick={onToggleMultiAgent}
            className={`chat-input-mic ${isMultiAgent ? "chat-input-mic--active" : "text-gray-400"}`}
            title="Toggle Multi-Agent Mode"
          >
            <Users size={15} />
          </button>

          <button
            onClick={onSend}
            disabled={disabled || !value.trim() || atLimit}
            className="chat-input-send"
            title="Send (⌘↵)"
          >
            {disabled
              ? <Loader2 size={15} className="spin" />
              : <Send size={15} />
            }
          </button>
        </div>
      </div>

      <div className="chat-input-footer">
        <span className="chat-input-hint">
          ⌘K focus · ⌘N new · ⌘/ terminal · ⌘↵ send · Shift↵ newline
        </span>
        {listening && (
          <span className="chat-input-listening">
            🔴 Listening...
          </span>
        )}
      </div>
    </div>
  );
}
