"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare, Files, Plus, Trash2,
  Search, X, PenLine, Zap, Clock
} from "lucide-react";
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
  if (days < 7) return `${days}d ago`;
  return new Date(timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function groupConversations(conversations: Conversation[]) {
  const now = Date.now();
  const today: Conversation[] = [];
  const week: Conversation[] = [];
  const older: Conversation[] = [];

  conversations.forEach((c) => {
    const diff = now - c.updatedAt;
    if (diff < 86400000) today.push(c);
    else if (diff < 604800000) week.push(c);
    else older.push(c);
  });

  return { today, week, older };
}

function ConversationItem({
  convo,
  isActive,
  onSelect,
  onDelete,
  onRename,
}: {
  convo: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: (title: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editVal, setEditVal] = useState(convo.title);
  const [hovered, setHovered] = useState(false);

  function commitRename() {
    if (editVal.trim()) onRename(editVal.trim());
    setEditing(false);
  }

  return (
    <div
      className={`sidebar-convo ${isActive ? "sidebar-convo--active" : ""}`}
      onClick={onSelect}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="sidebar-convo__icon">
        <MessageSquare size={13} />
      </div>

      <div className="sidebar-convo__body">
        {editing ? (
          <input
            autoFocus
            className="sidebar-convo__rename"
            value={editVal}
            onChange={(e) => setEditVal(e.target.value)}
            onBlur={commitRename}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitRename();
              if (e.key === "Escape") setEditing(false);
            }}
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <p className="sidebar-convo__title">{convo.title}</p>
        )}
        <div className="sidebar-convo__meta">
          <Clock size={9} />
          <span>{timeAgo(convo.updatedAt)}</span>
          {convo.messages.length > 0 && (
            <span className="sidebar-convo__count">
              {convo.messages.length} msg{convo.messages.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      {(hovered || isActive) && !editing && (
        <div className="sidebar-convo__actions" onClick={(e) => e.stopPropagation()}>
          <button
            className="sidebar-convo__action-btn"
            onClick={() => { setEditing(true); setEditVal(convo.title); }}
            title="Rename"
          >
            <PenLine size={11} />
          </button>
          <button
            className="sidebar-convo__action-btn sidebar-convo__action-btn--danger"
            onClick={onDelete}
            title="Delete"
          >
            <Trash2 size={11} />
          </button>
        </div>
      )}
    </div>
  );
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div className="sidebar-section-label">
      {label}
    </div>
  );
}

export default function Sidebar({
  conversations, activeConversationId,
  onSelectConversation, onNewConversation, onDeleteConversation,
  onRenameConversation, onFileSelect, refreshTrigger, userId,
}: Props) {
  const [activeTab, setActiveTab] = useState<"chats" | "files">("chats");
  const [search, setSearch] = useState("");

  const filtered = search.trim()
    ? conversations.filter((c) =>
        c.title.toLowerCase().includes(search.toLowerCase()) ||
        c.messages.some((m) => m.content.toLowerCase().includes(search.toLowerCase()))
      )
    : conversations;

  const { today, week, older } = groupConversations(filtered);

  return (
    <div className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand__logo">
          <span className="sidebar-brand__icon"><Zap size={22} className="text-indigo-400" fill="currentColor" /></span>
          <div>
            <span className="sidebar-brand__name">LEO</span>
            <span className="sidebar-brand__sub">AI Engineer</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="sidebar-tabs">
        <button
          className={`sidebar-tab ${activeTab === "chats" ? "sidebar-tab--active" : ""}`}
          onClick={() => setActiveTab("chats")}
        >
          <MessageSquare size={13} />
          Chats
        </button>
        <button
          className={`sidebar-tab ${activeTab === "files" ? "sidebar-tab--active" : ""}`}
          onClick={() => setActiveTab("files")}
        >
          <Files size={13} />
          Files
        </button>
      </div>

      {activeTab === "chats" ? (
        <div className="sidebar-chats">
          {/* New chat */}
          <button className="sidebar-new-btn" onClick={onNewConversation}>
            <Plus size={14} />
            New conversation
          </button>

          {/* Search */}
          <div className="sidebar-search">
            <Search size={12} className="sidebar-search__icon" />
            <input
              className="sidebar-search__input"
              placeholder="Search conversations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button className="sidebar-search__clear" onClick={() => setSearch("")}>
                <X size={11} />
              </button>
            )}
          </div>

          {/* Conversation list */}
          <div className="sidebar-list">
            {filtered.length === 0 ? (
              <div className="sidebar-empty">
                <Zap size={20} className="sidebar-empty__icon" />
                <p>No conversations yet</p>
                <span>Start by asking LEO to build something</span>
              </div>
            ) : (
              <AnimatePresence>
                {today.length > 0 && <SectionLabel key="label-today" label="Today" />}
                {today.map((c) => (
                  <motion.div
                    key={c.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -8 }}
                    transition={{ duration: 0.15 }}
                  >
                    <ConversationItem
                      convo={c}
                      isActive={c.id === activeConversationId}
                      onSelect={() => onSelectConversation(c.id)}
                      onDelete={() => onDeleteConversation(c.id)}
                      onRename={(t) => onRenameConversation(c.id, t)}
                    />
                  </motion.div>
                ))}
                {week.length > 0 && <SectionLabel key="label-week" label="This week" />}
                {week.map((c) => (
                  <motion.div
                    key={c.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -8 }}
                    transition={{ duration: 0.15 }}
                  >
                    <ConversationItem
                      convo={c}
                      isActive={c.id === activeConversationId}
                      onSelect={() => onSelectConversation(c.id)}
                      onDelete={() => onDeleteConversation(c.id)}
                      onRename={(t) => onRenameConversation(c.id, t)}
                    />
                  </motion.div>
                ))}
                {older.length > 0 && <SectionLabel key="label-older" label="Older" />}
                {older.map((c) => (
                  <motion.div
                    key={c.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -8 }}
                    transition={{ duration: 0.15 }}
                  >
                    <ConversationItem
                      convo={c}
                      isActive={c.id === activeConversationId}
                      onSelect={() => onSelectConversation(c.id)}
                      onDelete={() => onDeleteConversation(c.id)}
                      onRename={(t) => onRenameConversation(c.id, t)}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
          </div>
        </div>
      ) : (
        <div className="sidebar-files">
          <FileTree
            onFileSelect={onFileSelect}
            refreshTrigger={refreshTrigger}
            userId={userId}
          />
        </div>
      )}
    </div>
  );
}
