"use client";
import { useState, useRef, useEffect } from "react";
import { useSession } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TerminalSquare, FlaskConical, Sun, Moon,
  Menu, X, Plus, Zap
} from "lucide-react";

import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import Sidebar from "./components/Sidebar";
import FilePreview from "./components/FilePreview";
import TerminalPanel from "./components/TerminalPanel";
import EvalDashboard from "./components/EvalDashboard";
import TaskTemplates from "./components/TaskTemplates";
import ConversationViewer from "./components/ConversationViewer";
import LoginGate from "./components/LoginGate";
import TypingIndicator from "./components/TypingIndicator";
import { useConversations } from "./hooks/useConversations";
import { useTheme } from "./hooks/useTheme";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { Message, Conversation } from "./types";

export default function Home() {
  const { data: session } = useSession();
  const userId = (session?.user as any)?.id || "anonymous";
  const { theme, toggleTheme } = useTheme();
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const {
    conversations, activeConversationId, loaded,
    createConversation, updateConversation, deleteConversation,
    getActiveConversation, switchConversation, renameConversation,
  } = useConversations();

  const [input, setInput] = useState("");
  const [isMultiAgent, setIsMultiAgent] = useState(false);
  const [sending, setSending] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showTerminal, setShowTerminal] = useState(false);
  const [showEvals, setShowEvals] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [viewingConversation, setViewingConversation] = useState<Conversation | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeConversation = getActiveConversation();
  const messages = activeConversation?.messages || [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useKeyboardShortcuts({
    onFocusInput: () => inputRef.current?.focus(),
    onNewConversation: handleNewConversation,
    onOpenTerminal: () => setShowTerminal(true),
    onClosePanel: () => {
      setShowTerminal(false);
      setShowEvals(false);
      setSelectedFile(null);
      setViewingConversation(null);
    },
    onToggleTheme: toggleTheme,
  });

  function updateMsg(convoId: string, leoMsgId: string, updater: (m: Message) => Message) {
    const convo = conversations.find((c) => c.id === convoId);
    const msgs = convo?.messages || [];
    updateConversation(convoId, msgs.map((m) => m.id === leoMsgId ? updater(m) : m));
  }

  function handleSelectConversation(id: string) {
    const convo = conversations.find((c) => c.id === id);
    if (!convo) return;
    if (id === activeConversationId && convo.messages.length > 0) {
      setViewingConversation(convo);
      return;
    }
    switchConversation(id);
    setSidebarOpen(false);
  }

  function handleNewConversation() {
    createConversation();
    setSidebarOpen(false);
  }

  async function handleSend() {
    if (!input.trim() || sending) return;

    let convoId = activeConversationId;
    if (!convoId) {
      const newConvo = createConversation();
      convoId = newConvo.id;
    }

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
      status: "done",
      timestamp: Date.now(),
    };

    const leoMsgId = crypto.randomUUID();
    const leoMsg: Message = {
      id: leoMsgId,
      role: "leo",
      content: "",
      steps: [],
      plan: [],
      status: "pending",
      timestamp: Date.now(),
    };

    const currentMessages = getActiveConversation()?.messages || [];
    updateConversation(convoId, [...currentMessages, userMsg, leoMsg]);
    setInput("");
    setSending(true);

    try {
      if (isMultiAgent) {
        const res = await fetch("http://localhost:8000/agent/multi", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task: userMsg.content, user_id: userId }),
        });
        const data = await res.json();
        
        setSending(false);
        setRefreshTrigger((n) => n + 1);
        updateMsg(convoId!, leoMsgId, (m) => ({
          ...m, 
          content: data.final_answer || "Multi-agent task complete.", 
          steps: data.steps || [],
          status: "done" as const,
        }));
        return;
      }

      const url = `http://localhost:8000/agent/stream?task=${encodeURIComponent(userMsg.content)}&user_id=${encodeURIComponent(userId)}&max_steps=10`;
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const id = convoId!;

        switch (data.type) {
          case "plan":
          case "plan_update":
            updateMsg(id, leoMsgId, (m) => ({ ...m, plan: data.plan }));
            break;
          case "tool_start":
            updateMsg(id, leoMsgId, (m) => ({
              ...m,
              steps: [...(m.steps || []), {
                step: data.step, type: "tool_call" as const,
                tool: data.tool, params: data.params,
              }],
            }));
            break;
          case "tool_result":
            updateMsg(id, leoMsgId, (m) => ({
              ...m,
              steps: (m.steps || []).map((s) =>
                s.step === data.step ? { ...s, result: data.result } : s
              ),
            }));
            break;
          case "thought":
            updateMsg(id, leoMsgId, (m) => ({
              ...m,
              steps: [...(m.steps || []), {
                step: data.step, type: "thought" as const, content: data.content
              }],
            }));
            break;
          case "done":
            eventSource.close();
            setSending(false);
            setRefreshTrigger((n) => n + 1);
            updateMsg(id, leoMsgId, (m) => ({
              ...m, content: data.content, plan: data.plan,
              status: "done" as const,
            }));
            break;
          case "agent_error":
            eventSource.close();
            setSending(false);
            updateMsg(id, leoMsgId, (m) => ({
              ...m, content: data.content, plan: data.plan,
              status: "error" as const,
            }));
            break;
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setSending(false);
        updateMsg(convoId!, leoMsgId, (m) => ({
          ...m, content: "Connection to LEO lost.", status: "error" as const,
        }));
      };
    } catch {
      setSending(false);
    }
  }

  const hasOverlay = showTerminal || showEvals || !!selectedFile || !!viewingConversation;

  return (
    <LoginGate>
      <div className="leo-layout">
        {/* ── Mobile sidebar backdrop ── */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="leo-backdrop"
              onClick={() => setSidebarOpen(false)}
            />
          )}
        </AnimatePresence>

        {/* ── Sidebar ── */}
        <aside className={`leo-sidebar ${sidebarOpen ? "leo-sidebar--open" : ""}`}>
          <Sidebar
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            onDeleteConversation={deleteConversation}
            onRenameConversation={renameConversation}
            onFileSelect={setSelectedFile}
            refreshTrigger={refreshTrigger}
            userId={userId}
          />
        </aside>

        {/* ── Main ── */}
        <main className="leo-main">
          {/* Header */}
          <header className="leo-header">
            <div className="leo-header__left">
              <button
                className="leo-icon-btn leo-mobile-only"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
              </button>
              <div className="leo-logo">
                <span className="leo-logo__icon"><Zap size={18} className="text-indigo-400" /></span>
                <span className="leo-logo__name">LEO</span>
                <span className="leo-logo__tag">beta</span>
              </div>
            </div>

            <div className="leo-header__right">
              <button
                onClick={() => setShowTerminal(true)}
                className="leo-header-btn"
              >
                <TerminalSquare size={14} />
                <span>Terminal</span>
                <kbd>⌘/</kbd>
              </button>
              <button
                onClick={() => setShowEvals(true)}
                className="leo-header-btn"
              >
                <FlaskConical size={14} />
                <span>Evals</span>
              </button>
              <div className="leo-header-divider" />
              <button onClick={toggleTheme} className="leo-icon-btn">
                {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              </button>
              {session?.user?.image && (
                <img
                  src={session.user.image}
                  alt="avatar"
                  className="leo-avatar"
                />
              )}
            </div>
          </header>

          {/* Content area */}
          <div className="leo-content">
            {/* Overlays */}
            <AnimatePresence>
              {selectedFile && (
                <motion.div
                  key="file-preview"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="leo-overlay"
                >
                  <FilePreview
                    filename={selectedFile}
                    onClose={() => setSelectedFile(null)}
                  />
                </motion.div>
              )}
              {showTerminal && (
                <motion.div
                  key="terminal"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="leo-overlay"
                >
                  <TerminalPanel onClose={() => setShowTerminal(false)} />
                </motion.div>
              )}
              {showEvals && (
                <motion.div
                  key="evals"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="leo-overlay"
                >
                  <EvalDashboard onClose={() => setShowEvals(false)} />
                </motion.div>
              )}
              {viewingConversation && (
                <motion.div
                  key="convo-viewer"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="leo-overlay"
                >
                  <ConversationViewer
                    conversation={viewingConversation}
                    onClose={() => setViewingConversation(null)}
                    onResume={(c) => {
                      setViewingConversation(null);
                      switchConversation(c.id);
                    }}
                    userId={userId}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Messages */}
            <div className="leo-messages">
              <div className="leo-messages__inner">
                {!loaded ? null : messages.length === 0 ? (
                  <EmptyState onNewChat={handleNewConversation} />
                ) : (
                  <AnimatePresence initial={false}>
                    {messages.map((m) => (
                      <ChatMessage
                        key={m.id}
                        message={m}
                        allMessages={messages}
                        userId={userId}
                      />
                    ))}
                  </AnimatePresence>
                )}
                {sending &&
                  messages[messages.length - 1]?.status === "pending" &&
                  !messages[messages.length - 1]?.content &&
                  !messages[messages.length - 1]?.steps?.length && (
                    <TypingIndicator />
                  )}
                <div ref={bottomRef} />
              </div>
            </div>

            {/* Input area */}
            <div className="leo-input-area">
              <TaskTemplates
                visible={messages.length === 0}
                onSelect={(p) => setInput(p)}
              />
              <ChatInput
                value={input}
                onChange={setInput}
                onSend={handleSend}
                disabled={sending}
                inputRef={inputRef}
                isMultiAgent={isMultiAgent}
                onToggleMultiAgent={() => setIsMultiAgent(!isMultiAgent)}
              />
            </div>
          </div>
        </main>
      </div>
    </LoginGate>
  );
}

function EmptyState({ onNewChat }: { onNewChat: () => void }) {
  return (
    <div className="leo-empty">
      <div className="leo-empty__icon flex justify-center text-indigo-400">
        <TerminalSquare size={48} strokeWidth={1.5} />
      </div>
      <h2 className="leo-empty__title">What are we building today?</h2>
      <p className="leo-empty__subtitle">
        LEO can write, run, debug, and deploy code in any language.
        <br />
        Just describe what you need.
      </p>
      <div className="leo-empty__actions">
        <button onClick={onNewChat} className="leo-btn leo-btn--primary">
          <Plus size={14} />
          New task
        </button>
        <button className="leo-btn leo-btn--secondary">
          <Zap size={14} />
          See examples
        </button>
      </div>
    </div>
  );
}