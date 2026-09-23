"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap } from "lucide-react";
import { API_URL } from "../lib/api";

const SLOW_THRESHOLD_MS = 3000;
const RETRY_INTERVAL_MS = 5000;

export default function BackendHealthCheck() {
  const [waking, setWaking] = useState(false);

  useEffect(() => {
    let stopped = false;
    let retryTimeout: ReturnType<typeof setTimeout> | null = null;

    function scheduleRetry() {
      if (stopped) return;
      retryTimeout = setTimeout(attempt, RETRY_INTERVAL_MS);
    }

    function attempt() {
      if (stopped) return;
      let settled = false;

      const slowTimer = setTimeout(() => {
        if (!settled && !stopped) setWaking(true);
      }, SLOW_THRESHOLD_MS);

      fetch(`${API_URL}/health`, { cache: "no-store" })
        .then((res) => res.ok)
        .catch(() => false)
        .then((ok) => {
          settled = true;
          clearTimeout(slowTimer);
          if (stopped) return;
          if (ok) {
            setWaking(false);
            stopped = true;
          } else {
            setWaking(true);
            scheduleRetry();
          }
        });
    }

    attempt();

    return () => {
      stopped = true;
      if (retryTimeout) clearTimeout(retryTimeout);
    };
  }, []);

  return (
    <AnimatePresence>
      {waking && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="leo-waking-overlay"
        >
          <div className="leo-waking-overlay__spinner">
            <div className="leo-waking-overlay__ring" />
            <Zap size={24} className="leo-waking-overlay__icon" fill="currentColor" fillOpacity={0.25} />
          </div>
          <h1 className="leo-waking-overlay__title">LEO is waking up...</h1>
          <p className="leo-waking-overlay__note">(free tier — usually takes 20-30 seconds)</p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
