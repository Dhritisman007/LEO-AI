"use client";
import { useEffect, useSyncExternalStore } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { WifiOff } from "lucide-react";
import { API_URL } from "../lib/api";
import {
  initResilientFetch,
  subscribeNetworkStatus,
  getNetworkOffline,
  getNetworkOfflineServerSnapshot,
} from "../lib/networkStatus";

export default function NetworkStatusBanner() {
  useEffect(() => {
    initResilientFetch(API_URL);
  }, []);

  const offline = useSyncExternalStore(
    subscribeNetworkStatus,
    getNetworkOffline,
    getNetworkOfflineServerSnapshot
  );

  return (
    <AnimatePresence>
      {offline && (
        <motion.div
          initial={{ y: -48, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -48, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="leo-offline-banner"
          role="status"
        >
          <WifiOff size={13} className="leo-offline-banner__icon" />
          <span>LEO backend is offline — retrying...</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
