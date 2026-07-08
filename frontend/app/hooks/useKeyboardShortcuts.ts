"use client";
import { useEffect } from "react";

type Shortcuts = {
  onFocusInput: () => void;
  onNewConversation: () => void;
  onOpenTerminal: () => void;
  onClosePanel: () => void;
  onToggleTheme: () => void;
};

export function useKeyboardShortcuts({
  onFocusInput,
  onNewConversation,
  onOpenTerminal,
  onClosePanel,
  onToggleTheme,
}: Shortcuts) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const isMac = navigator.platform.toUpperCase().includes("MAC");
      const modifier = isMac ? e.metaKey : e.ctrlKey;

      // Cmd+K → focus input
      if (modifier && e.key === "k") {
        e.preventDefault();
        onFocusInput();
      }

      // Cmd+N → new conversation
      if (modifier && e.key === "n") {
        e.preventDefault();
        onNewConversation();
      }

      // Cmd+/ → open terminal
      if (modifier && e.key === "/") {
        e.preventDefault();
        onOpenTerminal();
      }

      // Cmd+T → toggle theme
      if (modifier && e.key === "t") {
        e.preventDefault();
        onToggleTheme();
      }

      // Esc → close any open panel
      if (e.key === "Escape") {
        onClosePanel();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onFocusInput, onNewConversation, onOpenTerminal, onClosePanel, onToggleTheme]);
}
