"use client";
import { Send, Mic, MicOff, Loader2 } from "lucide-react";
import { useVoiceInput } from "../hooks/useVoiceInput";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
  inputRef?: React.RefObject<HTMLTextAreaElement | null>;
};

export default function ChatInput({ value, onChange, onSend, disabled, inputRef }: Props) {
  const { listening, startListening, stopListening } = useVoiceInput((t) =>
    onChange(value ? value + " " + t : t)
  );

  return (
    <div className="chat-input-wrap">
      <div className="chat-input-box">
        <textarea
          ref={inputRef}
          className="chat-input-field"
          placeholder={listening ? "Listening..." : "Ask LEO to build something..."}
          value={value}
          rows={1}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
        />
        <div className="chat-input-actions">
          <button
            onClick={listening ? stopListening : startListening}
            className={`chat-input-mic ${listening ? "chat-input-mic--active" : ""}`}
            title="Voice input"
          >
            {listening ? <MicOff size={15} /> : <Mic size={15} />}
          </button>
          <button
            onClick={onSend}
            disabled={disabled || !value.trim()}
            className="chat-input-send"
          >
            {disabled
              ? <Loader2 size={15} className="spin" />
              : <Send size={15} />
            }
          </button>
        </div>
      </div>
      <p className="chat-input-hint">
        ⌘K focus · ⌘N new · ⌘/ terminal · Enter send · Shift+Enter newline
      </p>
    </div>
  );
}
