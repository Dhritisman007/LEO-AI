"use client";
import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Keyboard } from "lucide-react";

const SHORTCUTS = [
  {
    category: "Navigation",
    items: [
      { keys: ["⌘", "K"], desc: "Focus input" },
      { keys: ["⌘", "N"], desc: "New conversation" },
      { keys: ["Esc"], desc: "Close any panel" },
      { keys: ["?"], desc: "Show this cheat sheet" },
    ],
  },
  {
    category: "Messaging",
    items: [
      { keys: ["⌘", "↵"], desc: "Send message" },
      { keys: ["Shift", "↵"], desc: "New line in input" },
      { keys: ["⌘", "T"], desc: "Toggle theme" },
    ],
  },
  {
    category: "Tools",
    items: [
      { keys: ["⌘", "/"], desc: "Open terminal" },
      { keys: ["⌘", "E"], desc: "Send selected code to LEO" },
      { keys: ["⌘", "L"], desc: "Open LEO in VS Code" },
    ],
  },
  {
    category: "Messages",
    items: [
      { keys: ["Right-click"], desc: "Message context menu" },
      { keys: ["Click step"], desc: "Expand/collapse steps" },
    ],
  },
];

type Props = {
  open: boolean;
  onClose: () => void;
};

export default function ShortcutSheet({ open, onClose }: Props) {
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if (e.key === "?" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
        e.preventDefault();
        if (open) onClose();
      }
      if (e.key === "Escape" && open) onClose();
    }
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="shortcut-backdrop"
            onClick={onClose}
          />

          {/* Sheet */}
          <motion.div
            initial={{ opacity: 0, scale: 0.94, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: 10 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="shortcut-sheet"
          >
            <div className="shortcut-sheet__header">
              <div className="shortcut-sheet__title">
                <Keyboard size={16} />
                Keyboard shortcuts
              </div>
              <button className="shortcut-sheet__close" onClick={onClose}>
                <X size={16} />
              </button>
            </div>

            <div className="shortcut-sheet__body">
              {SHORTCUTS.map((section) => (
                <div key={section.category} className="shortcut-section">
                  <p className="shortcut-section__title">{section.category}</p>
                  <div className="shortcut-section__items">
                    {section.items.map((item, i) => (
                      <div key={i} className="shortcut-item">
                        <span className="shortcut-item__desc">{item.desc}</span>
                        <div className="shortcut-item__keys">
                          {item.keys.map((key, j) => (
                            <span key={j} className="shortcut-key">{key}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="shortcut-sheet__footer">
              Press <span className="shortcut-key">?</span> to toggle this sheet
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
