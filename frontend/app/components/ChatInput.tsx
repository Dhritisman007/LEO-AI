"use client";
import { Send, Mic, MicOff } from "lucide-react";
import { useVoiceInput } from "../hooks/useVoiceInput";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
  inputRef?: React.RefObject<HTMLTextAreaElement>;
};

export default function ChatInput({ value, onChange, onSend, disabled, inputRef }: Props) {
  const { listening, startListening, stopListening } = useVoiceInput((transcript) => {
    onChange(value ? value + " " + transcript : transcript);
  });

  return (
    <div className="border-t border-zinc-800 bg-zinc-950 p-3 md:p-4">
      <div className="flex gap-2 max-w-2xl mx-auto">
        <textarea
          ref={inputRef}
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 md:px-4 md:py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 text-sm resize-none h-10 md:h-12 leading-tight"
          placeholder={listening ? "Listening... speak now 🎤" : "Give LEO a task..."}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
        />

        {/* Mic button */}
        <button
          onClick={listening ? stopListening : startListening}
          className={`rounded-xl px-3 transition flex items-center justify-center ${
            listening
              ? "bg-red-500 hover:bg-red-400 text-white animate-pulse"
              : "bg-zinc-700 hover:bg-zinc-600 text-zinc-300"
          }`}
          title={listening ? "Stop listening" : "Voice input"}
        >
          {listening ? <MicOff size={16} /> : <Mic size={16} />}
        </button>

        {/* Send button */}
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="bg-white text-black rounded-xl px-4 disabled:opacity-30 hover:bg-zinc-200 transition flex items-center justify-center"
        >
          <Send size={18} />
        </button>
      </div>
      {listening && (
        <p className="text-center text-xs text-red-400 mt-2 animate-pulse">
          🔴 Recording — speak your task, then click stop
        </p>
      )}
      <p className="text-center text-[10px] text-zinc-700 mt-1">
        Cmd+K focus · Cmd+N new chat · Cmd+/ terminal · Esc close
      </p>
    </div>
  );
}
