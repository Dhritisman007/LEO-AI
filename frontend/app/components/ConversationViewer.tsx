"use client";
import { X, RotateCcw } from "lucide-react";
import { Conversation } from "../types";
import ChatMessage from "./ChatMessage";

type Props = {
  conversation: Conversation;
  userId: string;
  onClose: () => void;
  onResume: (conversation: Conversation) => void;
};

export default function ConversationViewer({ conversation, userId, onClose, onResume }: Props) {
  return (
    <div className="absolute inset-0 bg-zinc-950/98 z-10 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex-1 min-w-0 mr-4">
          <p className="text-sm font-medium text-zinc-200 truncate">{conversation.title}</p>
          <p className="text-xs text-zinc-600 mt-0.5">
            {conversation.messages.length} messages ·{" "}
            {new Date(conversation.createdAt).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onResume(conversation)}
            className="flex items-center gap-1.5 text-xs bg-white text-black font-semibold px-3 py-1.5 rounded-lg hover:bg-zinc-200 transition"
          >
            <RotateCcw size={12} />
            Resume
          </button>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Read-only messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-2xl mx-auto">
          <div className="mb-4 text-center">
            <span className="text-xs text-zinc-600 bg-zinc-800 px-3 py-1 rounded-full">
              Read-only view
            </span>
          </div>
          {conversation.messages.map((m) => (
            <ChatMessage 
              key={m.id} 
              message={m} 
              allMessages={conversation.messages} 
              userId={userId} 
            />
          ))}
        </div>
      </div>
    </div>
  );
}
