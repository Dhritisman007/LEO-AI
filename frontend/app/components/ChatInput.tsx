"use client";
import { Send } from "lucide-react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
};

export default function ChatInput({ value, onChange, onSend, disabled }: Props) {
  return (
    <div className="border-t border-zinc-800 bg-zinc-950 p-4">
      <div className="max-w-2xl mx-auto flex gap-2">
        <textarea
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-500 text-sm resize-none h-12 leading-tight"
          placeholder="Give LEO a task..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
        />
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="bg-white text-black rounded-xl px-4 disabled:opacity-30 hover:bg-zinc-200 transition flex items-center justify-center"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
