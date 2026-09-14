"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SmilePlus } from "lucide-react";

const REACTIONS = ["👍", "👎", "❤️", "🔥", "⭐", "🤔", "😮", "🐐"];

type Props = {
  messageId: string;
  activeReactions: string[];
  onToggle: (emoji: string) => void;
};

export default function ReactionPicker({ messageId, activeReactions, onToggle }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="reaction-wrap">
      {/* Active reactions display */}
      {activeReactions.length > 0 && (
        <div className="reaction-active">
          {activeReactions.map((emoji) => (
            <button
              key={emoji}
              className="reaction-active__btn"
              onClick={() => onToggle(emoji)}
              title="Remove reaction"
            >
              {emoji}
            </button>
          ))}
        </div>
      )}

      {/* Add reaction button */}
      <div className="reaction-trigger-wrap">
        <button
          className={`reaction-trigger ${open ? "reaction-trigger--open" : ""}`}
          onClick={() => setOpen(!open)}
          title="Add reaction"
        >
          <SmilePlus size={13} />
        </button>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, scale: 0.85, y: 4 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.85, y: 4 }}
              transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
              className="reaction-picker"
            >
              {REACTIONS.map((emoji) => (
                <button
                  key={emoji}
                  className={`reaction-picker__btn ${activeReactions.includes(emoji) ? "reaction-picker__btn--active" : ""}`}
                  onClick={() => {
                    onToggle(emoji);
                    setOpen(false);
                  }}
                  title={emoji}
                >
                  {emoji}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
