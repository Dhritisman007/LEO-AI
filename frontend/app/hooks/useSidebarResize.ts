"use client";
import { useState, useEffect, useRef, useCallback } from "react";

const MIN_WIDTH = 180;
const MAX_WIDTH = 400;
const DEFAULT_WIDTH = 240;
const STORAGE_KEY = "leo_sidebar_width";

export function useSidebarResize() {
  const [width, setWidth] = useState(() => {
    if (typeof window === "undefined") return DEFAULT_WIDTH;
    return parseInt(localStorage.getItem(STORAGE_KEY) || String(DEFAULT_WIDTH));
  });

  const [resizing, setResizing] = useState(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    startX.current = e.clientX;
    startWidth.current = width;
    setResizing(true);
  }, [width]);

  useEffect(() => {
    if (!resizing) return;

    function onMouseMove(e: MouseEvent) {
      const delta = e.clientX - startX.current;
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidth.current + delta));
      setWidth(newWidth);
    }

    function onMouseUp() {
      setResizing(false);
      localStorage.setItem(STORAGE_KEY, String(width));
    }

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [resizing, width]);

  return { width, resizing, onMouseDown };
}
