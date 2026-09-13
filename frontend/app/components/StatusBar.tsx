"use client";
import { motion, AnimatePresence } from "framer-motion";
import { Wrench, Brain, CheckCircle2, XCircle, Loader2 } from "lucide-react";

type Status = {
  type: "idle" | "thinking" | "tool" | "done" | "error";
  message: string;
  tool?: string;
};

const icons = {
  idle: null,
  thinking: <Loader2 size={11} className="status-bar__spin" />,
  tool: <Wrench size={11} />,
  done: <CheckCircle2 size={11} />,
  error: <XCircle size={11} />,
};

const colors = {
  idle: "",
  thinking: "status-bar--thinking",
  tool: "status-bar--tool",
  done: "status-bar--done",
  error: "status-bar--error",
};

export default function StatusBar({ status }: { status: Status }) {
  if (status.type === "idle") return <div className="status-bar-placeholder" />;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status.message}
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{ duration: 0.15 }}
        className={`status-bar ${colors[status.type]}`}
      >
        <span className="status-bar__icon">{icons[status.type]}</span>
        <span className="status-bar__text">{status.message}</span>

        {status.type === "thinking" && (
          <div className="status-bar__dots">
            <span />
            <span />
            <span />
          </div>
        )}

        {status.type === "done" && (
          <motion.div
            className="status-bar__flash"
            initial={{ opacity: 0.6 }}
            animate={{ opacity: 0 }}
            transition={{ duration: 0.8 }}
          />
        )}
      </motion.div>
    </AnimatePresence>
  );
}
