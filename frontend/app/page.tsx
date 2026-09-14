"use client";
import { useState, useRef, useEffect } from "react";
import { useSession } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TerminalSquare, FlaskConical, Sun, Moon,
  Menu, X, Plus, Zap, Bug, Activity, Globe, Terminal
} from "lucide-react";

import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import { useFileAttachment } from "./hooks/useFileAttachment";
import Sidebar from "./components/Sidebar";
import FilePreview from "./components/FilePreview";
import TerminalPanel from "./components/TerminalPanel";
import EvalDashboard from "./components/EvalDashboard";
import TaskTemplates from "./components/TaskTemplates";
import ConversationViewer from "./components/ConversationViewer";
import LoginGate from "./components/LoginGate";
import StatusBar from "./components/StatusBar";
import SkeletonMessage from "./components/SkeletonMessage";
import TypingIndicator from "./components/TypingIndicator";
import { useConversations } from "./hooks/useConversations";
import { useTheme } from "./hooks/useTheme";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { useSidebarResize } from "./hooks/useSidebarResize";
import { useReactions } from "./hooks/useReactions";
import ShortcutSheet from "./components/ShortcutSheet";
import { Message, Conversation } from "./types";

export default function Home() {
  const { data: session } = useSession();
  const userId = (session?.user as any)?.id || "anonymous";
  const { theme, toggleTheme } = useTheme();
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const taskStartTime = useRef<number>(0);

  const {
    conversations, activeConversationId, loaded,
    createConversation, updateConversation, updateMessage, deleteConversation,
    getActiveConversation, switchConversation, renameConversation,
  } = useConversations();

  const {
    attachments,
    error: attachError,
    addFiles,
    removeAttachment,
    clearAttachments,
  } = useFileAttachment();

  const [input, setInput] = useState("");
  const [isMultiAgent, setIsMultiAgent] = useState(false);
  const [sending, setSending] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showTerminal, setShowTerminal] = useState(false);
  const [showEvals, setShowEvals] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [viewingConversation, setViewingConversation] = useState<Conversation | null>(null);
  const [status, setStatus] = useState<{
    type: "idle" | "thinking" | "tool" | "done" | "error";
    message: string;
  }>({ type: "idle", message: "" });
  const [currentTool, setCurrentTool] = useState<string | undefined>(undefined);
  const [currentToolMsg, setCurrentToolMsg] = useState<string | undefined>(undefined);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showShortcuts, setShowShortcuts] = useState(false);

  const { width: sidebarWidth, resizing, onMouseDown: onSidebarResize } = useSidebarResize();
  const { toggleReaction, getReactions } = useReactions();

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
      setShowShortcuts(false);
    },
    onToggleTheme: toggleTheme,
    onShowShortcuts: () => setShowShortcuts(true),
  });

  function updateMsg(convoId: string, leoMsgId: string, updater: (m: Message) => Message) {
    updateMessage(convoId, leoMsgId, updater);
  }

  function handleDeleteMessage(messageId: string) {
    if (!activeConversationId) return;
    const msgs = getActiveConversation()?.messages || [];
    updateConversation(
      activeConversationId,
      msgs.filter((m) => m.id !== messageId)
    );
  }

  async function handleRegenerateMessage(messageId: string) {
    if (!activeConversationId) return;
    const msgs = getActiveConversation()?.messages || [];
    const msgIndex = msgs.findIndex((m) => m.id === messageId);
    if (msgIndex < 0) return;

    // Find the user message before this LEO message
    const userMsg = msgs.slice(0, msgIndex).reverse().find((m) => m.role === "user");
    if (!userMsg) return;

    // Remove the old LEO message and re-run
    const newMsgs = msgs.filter((m) => m.id !== messageId);
    updateConversation(activeConversationId, newMsgs);

    // Re-trigger with the same user message
    setInput(userMsg.content);
    setTimeout(() => handleSend(), 50);
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
    if ((!input.trim() && attachments.length === 0) || sending) return;
    taskStartTime.current = Date.now();

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
      attachments: attachments.map((a) => ({ name: a.name, type: a.type })),
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
    const taskText = input;
    setInput("");
    setSending(true);
    setStatus({ type: "thinking", message: "LEO is thinking..." });

    try {
      if (attachments.length > 0) {
        // Use multipart form for file upload
        const formData = new FormData();
        formData.append("task", taskText || "Analyze this file and describe what it contains");
        formData.append("user_id", userId);
        formData.append("max_steps", "10");
        formData.append("file", attachments[0].raw); // first file

        const res = await fetch("http://localhost:8000/agent/with-file", {
          method: "POST",
          body: formData,
        });

        const data = await res.json();
        const durationSec = Math.round((Date.now() - taskStartTime.current) / 1000);

        updateMsg(convoId, leoMsgId, (m) => ({
          ...m,
          content: data.final_answer || "No response.",
          steps: data.steps || [],
          plan: data.plan || [],
          status: data.final_answer?.startsWith("ERROR") ? "error" as const : "done" as const,
          duration: durationSec,
        }));
        
        clearAttachments();
        setSending(false);
        setRefreshTrigger((n) => n + 1);
        setStatus({ type: "idle", message: "" });
      } else {
        if (isMultiAgent) {
          const res = await fetch("http://localhost:8000/agent/multi", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task: userMsg.content, user_id: userId }),
          });
          const data = await res.json();
          
          setSending(false);
          setRefreshTrigger((n) => n + 1);
          setStatus({ type: "done", message: "Task completed successfully" });
          setTimeout(() => setStatus({ type: "idle", message: "" }), 3000);
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
            case "thinking":
              setCurrentTool(undefined);
              setCurrentToolMsg("Thinking...");
              setStatus({ type: "thinking", message: "LEO is reasoning..." });
              break;
            case "tool_start": {
              setCurrentTool(data.tool);
              const smartMessages: Record<string, string> = {
                write_file: `Writing ${data.params?.filename || "file"}`,
                read_file: `Reading ${data.params?.filename || "file"}`,
                run_code: `Running ${data.params?.language || "code"}`,
                web_search: `Searching for "${data.params?.query?.slice(0, 25) || "..."}..."`,
                git_create_branch: `Creating branch ${data.params?.branch_name || ""}`,
                git_commit_changes: "Committing changes",
                git_push_branch: "Pushing to GitHub",
                git_open_pull_request: "Opening pull request",
              };
              setCurrentToolMsg(smartMessages[data.tool] || `Using ${data.tool}`);

              const toolMessages: Record<string, string> = {
                write_file: `Writing ${data.params?.filename || "file"}...`,
                read_file: `Reading ${data.params?.filename || "file"}...`,
                run_code: `Running ${data.params?.language || "code"}...`,
                run_shell: `Running command...`,
                web_search: `Searching for "${data.params?.query?.slice(0, 30) || "..."}"`,
                git_create_branch: `Creating branch ${data.params?.branch_name || ""}...`,
                git_commit_changes: `Committing changes...`,
                git_push_branch: `Pushing to GitHub...`,
                git_open_pull_request: `Opening pull request...`,
                list_files: `Listing workspace files...`,
              };
              setStatus({
                type: "tool",
                message: toolMessages[data.tool] || `Using ${data.tool}...`,
              });
              updateMsg(id, leoMsgId, (m) => ({
                ...m,
                steps: [...(m.steps || []), {
                  step: data.step, type: "tool_call" as const,
                  tool: data.tool, params: data.params,
                }],
              }));
              break;
            }
            case "tool_result":
              updateMsg(id, leoMsgId, (m) => ({
                ...m,
                steps: (m.steps || []).map((s) =>
                  s.step === data.step ? { ...s, result: data.result } : s
                ),
              }));
              break;
            case "thought":
              setCurrentTool(undefined);
              setCurrentToolMsg("Thinking...");
              setStatus({ type: "thinking", message: "LEO is reasoning..." });
              updateMsg(id, leoMsgId, (m) => ({
                ...m,
                steps: [...(m.steps || []), {
                  step: data.step, type: "thought" as const, content: data.content
                }],
              }));
              break;
            case "done":
              const durationMs = Date.now() - taskStartTime.current;
              const durationSec = Math.round(durationMs / 1000);
              eventSource.close();
              setSending(false);
              setRefreshTrigger((n) => n + 1);
              setCurrentTool(undefined);
              setCurrentToolMsg(undefined);
              setStatus({ type: "done", message: "Task completed successfully" });
              setTimeout(() => setStatus({ type: "idle", message: "" }), 3000);
              updateMsg(id, leoMsgId, (m) => ({
                ...m, content: data.content, plan: data.plan || m.plan,
                status: "done" as const,
                duration: durationSec,
              }));
              break;
            case "agent_error":
              eventSource.close();
              setSending(false);
              setCurrentTool(undefined);
              setCurrentToolMsg(undefined);
              setStatus({ type: "error", message: "LEO encountered an issue" });
              setTimeout(() => setStatus({ type: "idle", message: "" }), 4000);
              updateMsg(id, leoMsgId, (m) => ({
                ...m, content: data.content, plan: data.plan || m.plan,
                status: "error" as const,
              }));
              break;
          }
        };

        eventSource.onerror = () => {
          eventSource.close();
          setSending(false);
          setStatus({ type: "error", message: "Connection lost" });
          setTimeout(() => setStatus({ type: "idle", message: "" }), 3000);
          updateMsg(convoId!, leoMsgId, (m) => ({
            ...m, content: "Connection to LEO lost.", status: "error" as const,
          }));
        };
      }
    } catch {
      setSending(false);
      clearAttachments();
      setStatus({ type: "error", message: "Failed to connect" });
      setTimeout(() => setStatus({ type: "idle", message: "" }), 3000);
    }
  }

  const hasOverlay = showTerminal || showEvals || !!selectedFile || !!viewingConversation;

  return (
    <>
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
          <aside
            className={`leo-sidebar ${sidebarOpen ? "leo-sidebar--open" : ""}`}
            style={{ width: sidebarWidth }}
          >
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

            {/* Resize handle */}
            <div
              className={`sidebar-resize-handle ${resizing ? "sidebar-resize-handle--active" : ""}`}
              onMouseDown={onSidebarResize}
              title="Drag to resize"
            />
          </aside>

          {/* Prevent text selection while resizing */}
          {resizing && <div className="resize-overlay" />}

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
                <button
                  onClick={() => setShowShortcuts(true)}
                  className="leo-icon-btn"
                  title="Keyboard shortcuts (?)"
                >
                  <span style={{ fontSize: "14px", fontWeight: 700, color: "#444" }}>?</span>
                </button>
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

            {/* Status Bar */}
            <StatusBar status={status} />

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
                    <EmptyState onSelect={(prompt) => { setInput(prompt); inputRef.current?.focus(); }} />
                  ) : (
                    <AnimatePresence initial={false}>
                      {messages.map((m) => (
                        <ChatMessage
                          key={m.id}
                          message={m}
                          allMessages={messages}
                          userId={userId}
                          onToggleReaction={toggleReaction}
                          getReactions={getReactions}
                          onDelete={handleDeleteMessage}
                          onRegenerate={handleRegenerateMessage}
                        />
                      ))}
                    </AnimatePresence>
                  )}
                  {sending &&
                    messages[messages.length - 1]?.status === "pending" &&
                    !messages[messages.length - 1]?.content &&
                    !messages[messages.length - 1]?.steps?.length && (
                      <TypingIndicator
                        toolName={currentTool}
                        message={currentToolMsg}
                      />
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
                  attachments={attachments}
                  onAttach={addFiles}
                  onRemoveAttachment={removeAttachment}
                  attachError={attachError}
                />
              </div>
            </div>
          </main>
        </div>
      </LoginGate>
      <ShortcutSheet
        open={showShortcuts}
        onClose={() => setShowShortcuts(false)}
      />
    </>
  );
}

const SUGGESTIONS = [
  {
    icon: <Terminal size={22} className="text-indigo-400" fill="currentColor" fillOpacity={0.2} />,
    title: "Build a REST API",
    description: "FastAPI or Express with routes, models, and error handling",
    prompt: "Build a complete REST API with FastAPI including GET, POST, PUT and DELETE endpoints for a todo list. Add proper error handling and run it.",
    color: "group-hover:border-indigo-500/40 group-hover:bg-indigo-500/5 hover:shadow-[0_0_24px_rgba(99,102,241,0.15)]",
  },
  {
    icon: <FlaskConical size={22} className="text-green-400" fill="currentColor" fillOpacity={0.2} />,
    title: "Write unit tests",
    description: "Generate comprehensive tests with edge cases",
    prompt: "Write a Python function that validates email addresses, then write comprehensive unit tests covering valid emails, invalid formats, edge cases, and boundary conditions. Run the tests.",
    color: "group-hover:border-green-500/40 group-hover:bg-green-500/5 hover:shadow-[0_0_24px_rgba(34,197,94,0.15)]",
  },
  {
    icon: <Bug size={22} className="text-amber-400" fill="currentColor" fillOpacity={0.2} />,
    title: "Debug my code",
    description: "Find bugs, fix them, and explain what went wrong",
    prompt: "Write a Python binary search function with a subtle bug in it, then find the bug, explain why it's wrong, fix it, and run tests to verify the fix.",
    color: "group-hover:border-amber-500/40 group-hover:bg-amber-500/5 hover:shadow-[0_0_24px_rgba(245,158,11,0.15)]",
  },
  {
    icon: <Activity size={22} className="text-blue-400" fill="currentColor" fillOpacity={0.2} />,
    title: "Data analysis",
    description: "Process data, calculate stats, visualize results",
    prompt: "Write a Python script that generates a dataset of 100 student grades, calculates mean, median, standard deviation, and grade distribution, then prints a formatted report.",
    color: "group-hover:border-blue-500/40 group-hover:bg-blue-500/5 hover:shadow-[0_0_24px_rgba(59,130,246,0.15)]",
  },
  {
    icon: <Globe size={22} className="text-pink-400" fill="currentColor" fillOpacity={0.2} />,
    title: "Web scraper",
    description: "Extract data from websites with Python",
    prompt: "Write a Python web scraper using requests and BeautifulSoup that fetches the top stories from Hacker News and prints the title, score, and URL for each. Run it.",
    color: "group-hover:border-pink-500/40 group-hover:bg-pink-500/5 hover:shadow-[0_0_24px_rgba(236,72,153,0.15)]",
  },
  {
    icon: <Zap size={22} className="text-purple-400" fill="currentColor" fillOpacity={0.2} />,
    title: "Explain a concept",
    description: "Deep dive into any programming topic",
    prompt: "Explain how async/await works in Python with practical examples showing the difference between synchronous and asynchronous execution. Show real code examples.",
    color: "group-hover:border-purple-500/40 group-hover:bg-purple-500/5 hover:shadow-[0_0_24px_rgba(168,85,247,0.15)]",
  },
];

function EmptyState({ onSelect }: { onSelect: (prompt: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center pt-16 pb-12 px-6 w-full max-w-4xl mx-auto h-full">
      <div className="text-center mb-14">
        <div className="flex justify-center mb-6 relative">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-indigo-500/10 rounded-full blur-[50px] pointer-events-none" />
          <div className="w-14 h-14 rounded-2xl bg-[#111] border border-[#222] flex items-center justify-center shadow-lg text-indigo-400 relative z-10">
            <Zap size={26} fill="currentColor" />
          </div>
        </div>
        
        <h1 className="text-[26px] font-bold tracking-tight text-[#ededee] mb-2">
          What are we building today?
        </h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full mb-10">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.title}
            className={`group flex items-center gap-4 p-5 rounded-[18px] bg-[#0c0c0c] border border-[#222] transition-all duration-200 text-left hover:bg-[#111] hover:border-[#333] ${s.color}`}
            onClick={() => onSelect(s.prompt)}
          >
            <div className="flex-shrink-0 w-11 h-11 rounded-[10px] flex items-center justify-center bg-[#151515] border border-[#2a2a2a] group-hover:scale-105 transition-transform shadow-sm">
              {s.icon}
            </div>
            
            <div className="flex-1 min-w-0 flex flex-col justify-center">
              <h3 className="font-medium text-[14.5px] text-[#ededee] mb-1 truncate">{s.title}</h3>
              <p className="text-[12.5px] text-[#777] truncate">{s.description}</p>
            </div>
            
            <div className="text-[#555] opacity-0 -translate-x-2 transition-all duration-200 group-hover:opacity-100 group-hover:translate-x-0 pr-2 flex-shrink-0">
              →
            </div>
          </button>
        ))}
      </div>
      
      <p className="text-gray-400 text-[14px] max-w-md mx-auto text-center leading-relaxed">
        LEO is an autonomous AI developer. Describe your task in detail or select one of the templates above.
      </p>
    </div>
  );
}