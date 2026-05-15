"use client";

import { clsx } from "clsx";

interface StatusBadgeProps {
  status: "BUY" | "SELL" | "WAIT" | "connected" | "disconnected";
  size?: "sm" | "md";
}

export function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const colors = {
    BUY: "bg-green-500/10 text-green-400 border-green-500/20",
    SELL: "bg-red-500/10 text-red-400 border-red-500/20",
    WAIT: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    connected: "bg-green-500/10 text-green-400 border-green-500/20",
    disconnected: "bg-red-500/10 text-red-400 border-red-500/20",
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center font-semibold rounded-full border",
        colors[status],
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm"
      )}
    >
      {status}
    </span>
  );
}
