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
import { TerminalSquare, FlaskConical, Bot } from "lucide-react";

export default function Home() {
  const { data: session } = useSession();
  const userId = (session?.user as any)?.id || "anonymous";

  const {
    conversations,
    activeConversationId,
    loaded,
    createConversation,
    updateConversation,
    deleteConversation,
    getActiveConversation,
    switchConversation,
  } = useConversations();

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showTerminal, setShowTerminal] = useState(false);
  const [showEvals, setShowEvals] = useState(false);
  const [viewingConversation, setViewingConversation] = useState<Conversation | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeConversation = getActiveConversation();
  const messages = activeConversation?.messages || [];

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
      const url = `http://localhost:8000/agent/stream?task=${encodeURIComponent(userMsg.content)}&user_id=${encodeURIComponent(userId)}&max_steps=10`;
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        const convo = conversations.find((c) => c.id === convoId);
        const msgs = convo?.messages || [];

        const updateMsg = (updater: (m: Message) => Message) => {
          updateConversation(
            convoId!,
            msgs.map((m) => (m.id === leoMsgId ? updater(m) : m))
          );
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

          case "thought":
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
            updateMsg((m) => ({
              ...m,
              content: data.content,
              plan: data.plan,
              status: "done" as const,
            }));
            break;

          case "agent_error":
            eventSource.close();
            setSending(false);
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
        const convo = conversations.find((c) => c.id === convoId);
        const msgs = convo?.messages || [];
        updateConversation(
          convoId!,
          msgs.map((m) =>
            m.id === leoMsgId
              ? { ...m, content: "Connection to LEO lost.", status: "error" as const }
              : m
          )
        );
      };
    } catch {
      setSending(false);
    }
  }

  return (
    <LoginGate>
      <main className="flex h-screen bg-zinc-950 text-white">
        {/* Sidebar */}
        <div className="w-56 flex-shrink-0">
          <Sidebar
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            onDeleteConversation={deleteConversation}
            onFileSelect={setSelectedFile}
            refreshTrigger={refreshTrigger}
            userId={userId}
          />
        </div>

        {/* Main area */}
        <div className="flex-1 flex flex-col relative">
          {/* Overlays */}
          {selectedFile && (
            <FilePreview filename={selectedFile} onClose={() => setSelectedFile(null)} />
          )}
          {showTerminal && <TerminalPanel onClose={() => setShowTerminal(false)} />}
          {showEvals && <EvalDashboard onClose={() => setShowEvals(false)} />}
          {viewingConversation && (
            <ConversationViewer
              conversation={viewingConversation}
              onClose={() => setViewingConversation(null)}
              onResume={handleResumeConversation}
            />
          )}

          {/* Header */}
          <div className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot size={24} className="text-zinc-300" />
              <span className="font-bold text-lg">LEO</span>
              <span className="text-zinc-500 text-sm ml-1">— autonomous coding agent</span>
            </div>
            <div className="flex items-center gap-2">
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
                messages.map((m) => <ChatMessage key={m.id} message={m} />)
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
          />
        </div>
      </main>
    </LoginGate>
  );
}