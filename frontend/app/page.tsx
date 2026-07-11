"use client";
import { useState, useRef, useEffect } from "react";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import Sidebar from "./components/Sidebar";
import FilePreview from "./components/FilePreview";
import TerminalPanel from "./components/TerminalPanel";
import EvalDashboard from "./components/EvalDashboard";
import TaskTemplates from "./components/TaskTemplates";
import ConversationViewer from "./components/ConversationViewer";
import LoginGate from "./components/LoginGate";
import { useConversations } from "./hooks/useConversations";
import { Message, Conversation } from "./types";
import { useSession } from "next-auth/react";
import { TerminalSquare, FlaskConical, Bot, Sun, Moon, Menu } from "lucide-react";
import TypingIndicator from "./components/TypingIndicator";
import { useTheme } from "./hooks/useTheme";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import toast from "react-hot-toast";

export default function Home() {
  const { data: session } = useSession();
  const userId = (session?.user as any)?.id || "anonymous";
  const { theme, toggleTheme } = useTheme();

  const {
    conversations,
    activeConversationId,
    loaded,
    createConversation,
    updateConversation,
    updateMessage,
    deleteConversation,
    getActiveConversation,
    switchConversation,
    renameConversation,
  } = useConversations();

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [multiAgent, setMultiAgent] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showTerminal, setShowTerminal] = useState(false);
  const [showEvals, setShowEvals] = useState(false);
  const [viewingConversation, setViewingConversation] = useState<Conversation | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeConversation = getActiveConversation();
  const messages = activeConversation?.messages || [];

  const inputRef = useRef<HTMLTextAreaElement>(null);

  useKeyboardShortcuts({
    onFocusInput: () => inputRef.current?.focus(),
    onNewConversation: () => {
      setViewingConversation(null);
      createConversation();
    },
    onOpenTerminal: () => setShowTerminal(true),
    onClosePanel: () => {
      setShowTerminal(false);
      setShowEvals(false);
      setSelectedFile(null);
      setViewingConversation(null);
    },
    onToggleTheme: toggleTheme,
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function setMessages(updater: (prev: Message[]) => Message[]) {
    if (!activeConversationId) return;
    const current = getActiveConversation()?.messages || [];
    const next = updater(current);
    updateConversation(activeConversationId, next);
  }

  function handleSelectConversation(id: string) {
    const convo = conversations.find((c) => c.id === id);
    if (!convo) return;

    // If clicking the active conversation — open in viewer
    if (id === activeConversationId && convo.messages.length > 0) {
      setViewingConversation(convo);
      return;
    }

    switchConversation(id);
  }

  function handleNewConversation() {
    createConversation();
  }

  function handleResumeConversation(convo: Conversation) {
    setViewingConversation(null);
    switchConversation(convo.id);
  }

  async function handleSend() {
    if (!input.trim() || sending) return;

    // If no active conversation, create one
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
      if (multiAgent) {
        fetch("http://localhost:8000/agent/multi", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task: userMsg.content, user_id: userId }),
        })
          .then((res) => res.json())
          .then((data) => {
            setSending(false);
            setRefreshTrigger((n) => n + 1);
            if (data.final_answer) {
              updateMessage(convoId!, leoMsgId, (m) => ({
                ...m,
                content: data.final_answer,
                steps: data.steps,
                status: "done" as const,
              }));
              toast.success("LEO completed the task 🐐");
            } else {
              toast.error("LEO ran into an issue");
              updateMessage(convoId!, leoMsgId, (m) => ({
                ...m,
                content: data.detail || "Error",
                status: "error" as const,
              }));
            }
          })
          .catch((err) => {
            setSending(false);
            updateMessage(convoId!, leoMsgId, (m) => ({
              ...m,
              content: "Connection to LEO lost.",
              status: "error" as const,
            }));
          });
      } else {
        const url = `http://localhost:8000/agent/stream?task=${encodeURIComponent(userMsg.content)}&user_id=${encodeURIComponent(userId)}&max_steps=10`;
        const eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        const updateMsg = (updater: (m: Message) => Message) => {
          updateMessage(convoId!, leoMsgId, updater);
        };

        switch (data.type) {
          case "plan":
            updateMsg((m) => ({ ...m, plan: data.plan }));
            break;

          case "plan_update":
            updateMsg((m) => ({ ...m, plan: data.plan }));
            break;

          case "tool_start":
            updateMsg((m) => ({
              ...m,
              steps: [
                ...(m.steps || []),
                {
                  step: data.step,
                  type: "tool_call" as const,
                  tool: data.tool,
                  params: data.params,
                },
              ],
            }));
            break;

          case "tool_result":
            updateMsg((m) => ({
              ...m,
              steps: (m.steps || []).map((s) =>
                s.step === data.step ? { ...s, result: data.result } : s
              ),
            }));
            break;

          case "thinking":
            updateMsg((m) => ({
              ...m,
              steps: [
                ...(m.steps || []),
                { step: data.step, type: "thought" as const, content: data.content },
              ],
            }));
            break;

          case "done":
            eventSource.close();
            setSending(false);
            setRefreshTrigger((n) => n + 1);
            toast.success("LEO completed the task 🐐");
            updateMsg((m) => ({
              ...m,
              content: data.content,
              plan: data.plan,
              critique: data.critique || null,
              status: "done" as const,
            }));
            break;

          case "agent_error":
            eventSource.close();
            setSending(false);
            toast.error("LEO ran into an issue");
            updateMsg((m) => ({
              ...m,
              content: data.content,
              plan: data.plan,
              status: "error" as const,
            }));
            break;
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setSending(false);
        updateMessage(convoId!, leoMsgId, (m) => ({
          ...m,
          content: m.content || "Connection to LEO lost.",
          status: "error" as const,
        }));
      };
      }
    } catch {
      setSending(false);
    }
  }

  async function handleResume(checkpointId: string) {
    if (!activeConversationId) return;
    setSending(true);

    try {
      const res = await fetch("http://localhost:8000/agent/resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ checkpoint_id: checkpointId, user_id: userId, additional_steps: 20 }),
      });
      const data = await res.json();
      
      if (res.ok) {
        toast.success("Task resumed successfully");
        const leoMsgId = Math.random().toString(36).substring(7);
        const leoMsg: Message = {
          id: leoMsgId,
          role: "leo",
          content: data.final_answer || "Task complete",
          steps: data.steps,
          plan: data.plan,
          critique: data.critique || null,
          status: (data.final_answer && data.final_answer.startsWith("ERROR")) ? "error" : "done",
          timestamp: Date.now(),
        };
        const currentMessages = getActiveConversation()?.messages || [];
        updateConversation(activeConversationId, [...currentMessages, leoMsg]);
      } else {
        toast.error("Failed to resume task: " + data.detail);
      }
    } catch (err) {
      toast.error("Error connecting to server");
    } finally {
      setSending(false);
      setRefreshTrigger(n => n + 1);
    }
  }

  return (
    <LoginGate>
      <main className="flex h-screen bg-zinc-950 text-white overflow-hidden">
        {/* Sidebar — hidden on mobile, shown on desktop */}
        <div className={`
          fixed inset-y-0 left-0 z-30 w-56 flex-shrink-0 transform transition-transform duration-200
          md:relative md:translate-x-0
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}>
          <Sidebar
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={(id) => {
              handleSelectConversation(id);
              setSidebarOpen(false);
            }}
            onNewConversation={() => {
              handleNewConversation();
              setSidebarOpen(false);
            }}
            onDeleteConversation={deleteConversation}
            onRenameConversation={renameConversation}
            onFileSelect={setSelectedFile}
            refreshTrigger={refreshTrigger}
            userId={userId}
          />
        </div>

        {/* Mobile overlay — tap to close sidebar */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black/50 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main area */}
        <div className="flex-1 flex flex-col relative min-w-0">
          {/* Overlays */}
          {selectedFile && (
            <FilePreview filename={selectedFile} onClose={() => setSelectedFile(null)} />
          )}
          {showTerminal && <TerminalPanel onClose={() => setShowTerminal(false)} />}
          {showEvals && <EvalDashboard onClose={() => setShowEvals(false)} />}
          {viewingConversation && (
            <ConversationViewer
              conversation={viewingConversation}
              userId={userId}
              onClose={() => setViewingConversation(null)}
              onResume={handleResumeConversation}
            />
          )}

          {/* Header */}
          <div className="border-b border-zinc-800 px-4 md:px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden text-zinc-400 hover:text-white mr-2"
              >
                <Menu size={20} />
              </button>
              <Bot size={24} className="text-zinc-300" />
              <span className="font-bold text-lg">LEO</span>
              <span className="text-zinc-500 text-sm ml-1 hidden sm:inline">— autonomous coding agent</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleTheme}
                className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white border border-zinc-700 hover:border-zinc-500 rounded-lg px-3 py-1.5 transition"
              >
                {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
                {theme === "dark" ? "Light" : "Dark"}
              </button>
              <button
                onClick={() => setShowTerminal(true)}
                className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white border border-zinc-700 hover:border-zinc-500 rounded-lg px-3 py-1.5 transition"
              >
                <TerminalSquare size={14} />
                Terminal
              </button>
              <button
                onClick={() => setShowEvals(true)}
                className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white border border-zinc-700 hover:border-zinc-500 rounded-lg px-3 py-1.5 transition"
              >
                <FlaskConical size={14} />
                Evals
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className="max-w-2xl mx-auto">
              {!loaded ? null : messages.length === 0 ? (
                <div className="text-center text-zinc-500 mt-20">
                  <p className="text-lg">Give LEO a task to get started</p>
                  <p className="text-sm mt-2 text-zinc-600">
                    Try one of the templates below or type your own task
                  </p>
                </div>
              ) : (
                messages.map((m) => (
                  <ChatMessage
                    key={m.id}
                    message={m}
                    allMessages={messages}
                    userId={userId}
                    onResume={handleResume}
                  />
                ))
              )}
              {sending && messages.length > 0 && 
                messages[messages.length - 1].status === "pending" &&
                messages[messages.length - 1].content === "" &&
                (!messages[messages.length - 1].steps || messages[messages.length - 1].steps?.length === 0) && (
                  <TypingIndicator />
              )}
              <div ref={bottomRef} />
            </div>
          </div>

          {/* Templates + Input */}
          <TaskTemplates
            visible={messages.length === 0}
            onSelect={(prompt) => setInput(prompt)}
          />
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={sending}
            inputRef={inputRef}
            multiAgent={multiAgent}
            onToggleMultiAgent={() => setMultiAgent(!multiAgent)}
          />
        </div>
      </main>
    </LoginGate>
  );
}