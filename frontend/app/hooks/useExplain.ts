"use client";
import { useState } from "react";

export function useExplain() {
  const [explaining, setExplaining] = useState<string | null>(null); // message id being explained
  const [explanation, setExplanation] = useState<Record<string, string>>({}); // msgId -> text

  async function explainCode({
    messageId,
    code,
    filename,
    task,
    userId,
  }: {
    messageId: string;
    code: string;
    filename: string;
    task: string;
    userId: string;
  }) {
    setExplaining(messageId);
    setExplanation((prev) => ({ ...prev, [messageId]: "" }));

    try {
      const res = await fetch("http://localhost:8000/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, filename, task, user_id: userId }),
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setExplanation((prev) => ({
          ...prev,
          [messageId]: (prev[messageId] || "") + chunk,
        }));
      }
    } catch (e) {
      setExplanation((prev) => ({
        ...prev,
        [messageId]: "Could not generate explanation.",
      }));
    } finally {
      setExplaining(null);
    }
  }

  function clearExplanation(messageId: string) {
    setExplanation((prev) => {
      const next = { ...prev };
      delete next[messageId];
      return next;
    });
  }

  return { explaining, explanation, explainCode, clearExplanation };
}
