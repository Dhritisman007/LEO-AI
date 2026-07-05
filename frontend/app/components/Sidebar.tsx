"use client";
import { useState } from "react";
import { Files, MessageSquare, Plus, Trash2 } from "lucide-react";
import FileTree from "./FileTree";
import { Conversation } from "../types";

type Props = {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onFileSelect: (filename: string) => void;
  refreshTrigger: number;
  userId: string;
};

function timeAgo(timestamp: number): string {
  const diff = Date.now() - timestamp;
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

export default function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onFileSelect,
  refreshTrigger,
  userId,
}: Props) {
  const [activeTab, setActiveTab] = useState<"chats" | "files">("chats");

  return (
    <div className="h-full flex flex-col border-r border-zinc-800">
      {/* Tab switcher */}
      <div className="flex border-b border-zinc-800">
        <button
          onClick={() => setActiveTab("chats")}
          className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium transition ${
            activeTab === "chats"
              ? "text-white border-b-2 border-white"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          <MessageSquare size={13} />
          Chats
        </button>
        <button
          onClick={() => setActiveTab("files")}
          className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium transition ${
            activeTab === "files"
              ? "text-white border-b-2 border-white"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          <Files size={13} />
          Files
        </button>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "chats" ? (
          <div className="flex flex-col h-full">
            {/* New chat button */}
            <button
              onClick={onNewConversation}
              className="flex items-center gap-2 mx-3 my-2 px-3 py-2 text-xs text-zinc-400 hover:text-white border border-zinc-700 hover:border-zinc-500 rounded-lg transition"
            >
              <Plus size={13} />
              New chat
            </button>

            {/* Conversation list */}
            {conversations.length === 0 ? (
              <p className="text-zinc-600 text-xs px-4 py-3">No conversations yet</p>
            ) : (
              <div className="flex flex-col gap-0.5 px-2">
                {conversations.map((convo) => (
                  <div
                    key={convo.id}
                    className={`group flex items-start justify-between gap-1 px-2 py-2 rounded-lg cursor-pointer transition ${
                      convo.id === activeConversationId
                        ? "bg-zinc-700 text-white"
                        : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                    }`}
                    onClick={() => onSelectConversation(convo.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-xs truncate font-medium leading-tight">
                        {convo.title}
                      </p>
                      <p className="text-[10px] text-zinc-600 mt-0.5">
                        {timeAgo(convo.updatedAt)} · {convo.messages.length} msgs
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(convo.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition flex-shrink-0 mt-0.5"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <FileTree
            onFileSelect={onFileSelect}
            refreshTrigger={refreshTrigger}
            userId={userId}
          />
        )}
      </div>
    </div>
  );
}
