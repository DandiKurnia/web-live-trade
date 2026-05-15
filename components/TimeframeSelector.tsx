"use client";

import { clsx } from "clsx";

interface TimeframeSelectorProps {
  selected: string;
  onChange: (tf: string) => void;
}

const TIMEFRAMES = ["M1", "M5", "M15", "H1", "H4", "D1"];

export function TimeframeSelector({ selected, onChange }: TimeframeSelectorProps) {
  return (
    <div className="flex gap-1">
      {TIMEFRAMES.map((tf) => (
        <button
          key={tf}
          onClick={() => onChange(tf)}
          className={clsx(
            "px-3 py-1.5 text-xs font-medium rounded-md transition-colors",
            selected === tf
              ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
              : "text-neutral-400 hover:text-white hover:bg-[var(--border)]"
          )}
        >
          {tf}
        </button>
      ))}
    </div>
  );
}
