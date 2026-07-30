"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import {
  Wrench, CheckCircle2, XCircle, Brain,
  Loader2, BookOpen, Copy, Check, ChevronDown, ChevronUp
} from "lucide-react";
import { Message } from "../types";
import PlanTracker from "./PlanTracker";
import ExplainPanel from "./ExplainPanel";

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

function timeAgo(ts: number) {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

function extractCode(message: Message) {
  const writeStep = message.steps?.find(
    (s) => s.type === "tool_call" && s.tool === "write_file" && s.params?.content
  );
  if (writeStep) return { code: writeStep.params.content, filename: writeStep.params.filename || "code" };
  const match = message.content?.match(/```[\w]*\n([\s\S]*?)```/);
  if (match) return { code: match[1], filename: "snippet" };
  return null;
}

function StepCard({ step }: { step: any }) {
  const [expanded, setExpanded] = useState(false);

  const configMap: Record<string, any> = {
    tool_call: { color: "step-tool", icon: <Wrench size={12} />, label: `${step.tool}` },
    done: { color: "step-done", icon: <CheckCircle2 size={12} />, label: "Complete" },
    error: { color: "step-error", icon: <XCircle size={12} />, label: "Error" },
    thought: { color: "step-thought", icon: <Brain size={12} />, label: "Thinking" },
  };
  const config = configMap[step.type] || { color: "step-thought", icon: <Brain size={12} />, label: "Step" };

  const hasDetail = step.params || step.result || step.content;

  return (
    <div className={`step-card ${config.color}`}>
      <button
        className="step-card__header"
        onClick={() => hasDetail && setExpanded(!expanded)}
        style={{ cursor: hasDetail ? "pointer" : "default" }}
      >
        <span className="step-card__icon">{config.icon}</span>
        <span className="step-card__label">{config.label}</span>
        {step.result && (
          <span className={`step-card__status ${step.result.success ? "success" : "fail"}`}>
            {step.result.success ? "✓" : "✗"}
          </span>
        )}
        {hasDetail && (
          <span className="step-card__toggle">
            {expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
          </span>
        )}
      </button>
      {expanded && hasDetail && (
        <div className="step-card__detail">
          {step.params && (
            <pre className="step-card__code">
              {JSON.stringify(step.params, null, 2)}
            </pre>
          )}
          {step.result?.stdout && (
            <pre className="step-card__output">{step.result.stdout}</pre>
          )}
          {step.result?.stderr && (
            <pre className="step-card__output step-card__output--err">{step.result.stderr}</pre>
          )}
          {step.content && (
            <p className="step-card__text">{step.content}</p>
          )}
        </div>
      )}
    </div>
  );
}

type Props = {
  message: Message;
  allMessages: Message[];
  userId: string;
};

export default function ChatMessage({ message, allMessages, userId }: Props) {
  const [showExplain, setShowExplain] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState("");
  const [copied, setCopied] = useState(false);
  const [stepsExpanded, setStepsExpanded] = useState(true);

  const codeInfo = message.role === "leo" ? extractCode(message) : null;
  const hasCode = !!codeInfo;
  const stepCount = message.steps?.length || 0;
  const visibleSteps = stepsExpanded ? message.steps : message.steps?.slice(-3);

  async function handleExplain() {
    if (!codeInfo) return;
    setShowExplain(true);
    setExplaining(true);
    setExplanation("");
    const task = allMessages.find((_, i) => allMessages[i + 1]?.id === message.id)?.content || "";
    try {
      const res = await fetch("http://localhost:8000/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: codeInfo.code, filename: codeInfo.filename, task, user_id: userId }),
      });
      if (!res.body) throw new Error();
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        setExplanation((prev) => prev + decoder.decode(value, { stream: true }));
      }
    } catch {
      setExplanation("Could not generate explanation.");
    } finally {
      setExplaining(false);
    }
  }

  function handleCopy() {
    if (!codeInfo) return;
    navigator.clipboard.writeText(codeInfo.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (message.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
        className="msg-user-wrap"
      >
        <div className="msg-user">{message.content}</div>
        <span className="msg-timestamp">{timeAgo(message.timestamp)}</span>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
      className="msg-leo-wrap"
    >
      {/* Avatar row */}
      <div className="msg-leo__header">
        <span className="msg-leo__avatar">🐐</span>
        <span className="msg-leo__name">LEO</span>
        {message.status === "pending" && (
          <Loader2 size={12} className="msg-leo__spinner" />
        )}
        <span className="msg-timestamp ml-auto">{timeAgo(message.timestamp)}</span>
      </div>

      {/* Plan */}
      {message.plan && message.plan.length > 0 && (
        <PlanTracker plan={message.plan} />
      )}

      {/* Memory hint */}
      {message.recalled_memories && message.recalled_memories.length > 0 && (
        <div className="msg-memory-hint">
          🧠 Using {message.recalled_memories.length} similar past task{message.recalled_memories.length > 1 ? "s" : ""} as context
        </div>
      )}

      {/* Steps */}
      {stepCount > 0 && (
        <div className="msg-steps">
          {stepCount > 3 && (
            <button
              className="msg-steps__toggle"
              onClick={() => setStepsExpanded(!stepsExpanded)}
            >
              {stepsExpanded ? (
                <><ChevronUp size={11} /> Hide steps</>
              ) : (
                <><ChevronDown size={11} /> {stepCount} steps — show all</>
              )}
            </button>
          )}
          <div className="msg-steps__list">
            {visibleSteps?.map((s) => <StepCard key={s.step} step={s} />)}
          </div>
        </div>
      )}

      {/* Final reply */}
      {message.content && (
        <div className={`msg-bubble ${message.status === "error" ? "msg-bubble--error" : ""}`}>
          {message.content}
        </div>
      )}

      {/* PR Review */}
      {message.review && message.status === "done" && (
        <div className={`review-card ${message.review.score >= 8 ? "review-card--good"
            : message.review.score >= 6 ? "review-card--ok"
              : "review-card--bad"
          }`}>
          <div className="review-card__header">
            <span>{message.review.approve ? "✅" : "⚠️"}</span>
            <span className="review-card__score">
              Code review · {message.review.score}/10
            </span>
            <span className="review-card__summary">{message.review.summary}</span>
          </div>
          {(message.review.what_was_done_well?.length > 0 ||
            message.review.blocking_issues?.length > 0) && (
              <div className="review-card__body">
                {message.review.what_was_done_well?.slice(0, 2).map((w, i) => (
                  <p key={i} className="review-good">✓ {w}</p>
                ))}
                {message.review.blocking_issues?.slice(0, 2).map((issue, i) => (
                  <p key={i} className="review-bad">
                    ✗ {issue}
                    {message.review?.rewrite_needed && " (auto-fixed)"}
                  </p>
                ))}
              </div>
            )}
        </div>
      )}

      {/* Actions */}
      {message.status === "done" && hasCode && (
        <div className="msg-actions">
          <button
            onClick={handleExplain}
            disabled={explaining}
            className="msg-action-btn"
          >
            {explaining ? <Loader2 size={12} className="spin" /> : <BookOpen size={12} />}
            {showExplain ? "Re-explain" : "Explain code"}
          </button>
          <button onClick={handleCopy} className="msg-action-btn">
            {copied ? <><Check size={12} /> Copied!</> : <><Copy size={12} /> Copy</>}
          </button>
        </div>
      )}

      {/* Explanation */}
      {showExplain && (
        <ExplainPanel
          explanation={explanation}
          loading={explaining}
          onClose={() => { setShowExplain(false); setExplanation(""); }}
        />
      )}
    </motion.div>
  );
}
