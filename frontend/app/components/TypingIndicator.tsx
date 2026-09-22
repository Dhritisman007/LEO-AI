"use client";
import type { ReactElement } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Wrench, Brain, Search, FileText,
  Play, GitBranch, Loader2, Zap
} from "lucide-react";

type Props = {
  toolName?: string;
  message?: string;
};

const TOOL_CONFIG: Record<string, { icon: ReactElement; label: string; color: string }> = {
  write_file:   { icon: <FileText size={13} />,  label: "Writing file",    color: "#a78bfa" },
  read_file:    { icon: <FileText size={13} />,  label: "Reading file",    color: "#a78bfa" },
  run_code:     { icon: <Play size={13} />,      label: "Running code",    color: "#4ade80" },
  run_python:   { icon: <Play size={13} />,      label: "Running Python",  color: "#4ade80" },
  run_shell:    { icon: <Play size={13} />,      label: "Running command", color: "#4ade80" },
  web_search:   { icon: <Search size={13} />,    label: "Searching web",   color: "#60a5fa" },
  list_files:   { icon: <FileText size={13} />,  label: "Listing files",   color: "#a78bfa" },
  git_create_branch:     { icon: <GitBranch size={13} />, label: "Creating branch",  color: "#f59e0b" },
  git_commit_changes:    { icon: <GitBranch size={13} />, label: "Committing",       color: "#f59e0b" },
  git_push_branch:       { icon: <GitBranch size={13} />, label: "Pushing to GitHub", color: "#f59e0b" },
  git_open_pull_request: { icon: <GitBranch size={13} />, label: "Opening PR",       color: "#f59e0b" },
};

export default function TypingIndicator({ toolName, message }: Props) {
  const config = toolName ? TOOL_CONFIG[toolName] : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.2 }}
      className="typing-wrap"
    >
      <div className="typing-header">
        <span className="typing-avatar flex items-center justify-center">
          <Zap size={14} className="text-indigo-400" fill="currentColor" />
        </span>
        <span className="typing-name">LEO</span>
      </div>

      <div className="typing-bubble">
        <AnimatePresence mode="wait">
          {config ? (
            <motion.div
              key={toolName}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 6 }}
              transition={{ duration: 0.15 }}
              className="typing-tool"
            >
              <span
                className="typing-tool__icon"
                style={{ color: config.color }}
              >
                {config.icon}
              </span>
              <span className="typing-tool__label">
                {message || config.label}
              </span>
              <span className="typing-tool__detail">
                {toolName?.replace(/_/g, " ")}
              </span>
            </motion.div>
          ) : (
            <motion.div
              key="thinking"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="typing-thinking"
            >
              <Brain size={13} className="typing-thinking__icon" />
              <span>{message || "Thinking"}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Animated dots */}
        <div className="typing-dots">
          <span style={{ animationDelay: "0ms" }} />
          <span style={{ animationDelay: "180ms" }} />
          <span style={{ animationDelay: "360ms" }} />
        </div>
      </div>
    </motion.div>
  );
}
