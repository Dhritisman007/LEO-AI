"use client";
import { useState } from "react";
import { Files, MessageSquare, Plus, Trash2, Search, X as XIcon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import FileTree from "./FileTree";
import { Conversation } from "../types";

type Props = {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, title: string) => void;
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
  onRenameConversation,
  onFileSelect,
  refreshTrigger,
  userId,
}: Props) {
  const [activeTab, setActiveTab] = useState<"chats" | "files">("chats");
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const filteredConversations = search.trim()
    ? conversations.filter((c) =>
        c.title.toLowerCase().includes(search.toLowerCase()) ||
        c.messages.some((m) =>
          m.content.toLowerCase().includes(search.toLowerCase())
        )
      )
    : conversations;

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
              className="flex-shrink-0 flex items-center justify-between mx-3 mt-3 mb-2 px-3 py-2.5 text-sm font-medium text-zinc-200 transition"
              style={{ backgroundColor: "#27272a", borderRadius: "8px", padding: "12px 16px", marginBottom: "12px" }}
            >
              <div className="flex items-center gap-3">
                <Plus size={16} />
                <span style={{ fontSize: "14px" }}>New chat</span>
              </div>
            </button>

            {/* Search box */}
            <div className="flex-shrink-0 relative mx-3 mb-2" style={{ marginBottom: "12px" }}>
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" style={{ left: "12px" }} />
              <input
                className="w-full bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition"
                style={{ borderRadius: "8px", padding: "12px 16px 12px 36px", fontSize: "14px" }}
                placeholder="Search chats..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-zinc-400"
                >
                  <XIcon size={12} />
                </button>
              )}
            </div>

            {/* Show result count when searching */}
            {search && (
              <p className="text-[10px] text-zinc-600 px-4 mb-1">
                {filteredConversations.length} result{filteredConversations.length !== 1 ? "s" : ""}
              </p>
            )}

            {/* Conversation list */}
            {filteredConversations.length === 0 ? (
              <p className="text-zinc-600 text-xs px-4 py-3">No conversations found</p>
            ) : (
              <div className="flex flex-col gap-0.5 px-2">
                <AnimatePresence>
                  {filteredConversations.map((convo, idx) => (
                    <motion.div
                      key={convo.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      transition={{ duration: 0.15, delay: idx * 0.03 }}
                      className={`group flex items-start justify-between gap-1 px-2 py-2 rounded-lg cursor-pointer transition ${
                      convo.id === activeConversationId
                        ? "bg-zinc-700 text-white"
                        : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                    }`}
                    onClick={() => onSelectConversation(convo.id)}
                  >
                    <div className="flex-1 min-w-0">
                      {editingId === convo.id ? (
                        <input
                          autoFocus
                          className="bg-zinc-700 text-white text-xs px-1 py-0.5 rounded w-full outline-none"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onBlur={() => {
                            if (editTitle.trim()) {
                              onRenameConversation(convo.id, editTitle.trim());
                            }
                            setEditingId(null);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              if (editTitle.trim()) {
                                onRenameConversation(convo.id, editTitle.trim());
                              }
                              setEditingId(null);
                            }
                            if (e.key === "Escape") setEditingId(null);
                          }}
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <p
                          className="text-xs truncate font-medium leading-tight"
                          onDoubleClick={(e) => {
                            e.stopPropagation();
                            setEditingId(convo.id);
                            setEditTitle(convo.title);
                          }}
                          title="Double-click to rename"
                        >
                          {convo.title}
                        </p>
                      )}
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
                    </motion.div>
                  ))}
                </AnimatePresence>
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
