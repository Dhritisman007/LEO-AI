"use client";
import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Copy, RefreshCw, Trash2, BookOpen, Share } from "lucide-react";

type MenuItem = {
  icon: JSX.Element;
  label: string;
  action: () => void;
  danger?: boolean;
  divider?: boolean;
};

type Props = {
  x: number;
  y: number;
  items: MenuItem[];
  onClose: () => void;
};

export default function ContextMenu({ x, y, items, onClose }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    function handleEsc(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }

    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleEsc);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleEsc);
    };
  }, [onClose]);

  // Adjust position to stay on screen
  const adjustedX = Math.min(x, window.innerWidth - 200);
  const adjustedY = Math.min(y, window.innerHeight - (items.length * 36 + 16));

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.92 }}
      transition={{ duration: 0.1 }}
      className="context-menu"
      style={{ left: adjustedX, top: adjustedY }}
    >
      {items.map((item, i) => (
        <div key={i}>
          {item.divider && i > 0 && <div className="context-menu__divider" />}
          <button
            className={`context-menu__item ${item.danger ? "context-menu__item--danger" : ""}`}
            onClick={() => {
              item.action();
              onClose();
            }}
          >
            <span className="context-menu__icon">{item.icon}</span>
            <span className="context-menu__label">{item.label}</span>
          </button>
        </div>
      ))}
    </motion.div>
  );
}
