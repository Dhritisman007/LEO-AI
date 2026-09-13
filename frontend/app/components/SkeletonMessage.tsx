"use client";
import { motion } from "framer-motion";

export default function SkeletonMessage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="skeleton-wrap"
    >
      {/* Avatar row */}
      <div className="skeleton-header">
        <div className="skeleton-avatar" />
        <div className="skeleton-name" />
      </div>

      {/* Shimmer lines */}
      <div className="skeleton-body">
        <div className="skeleton-line skeleton-line--90" />
        <div className="skeleton-line skeleton-line--75" />
        <div className="skeleton-line skeleton-line--85" />
        <div className="skeleton-line skeleton-line--60" />
      </div>
    </motion.div>
  );
}
