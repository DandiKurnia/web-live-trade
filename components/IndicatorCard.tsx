"use client";

import { clsx } from "clsx";

interface IndicatorCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
}

export function IndicatorCard({ label, value, subtitle, trend = "neutral" }: IndicatorCardProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
      <p className="text-xs text-neutral-500 mb-1">{label}</p>
      <p
        className={clsx(
          "text-lg font-mono font-semibold",
          trend === "up" && "text-green-400",
          trend === "down" && "text-red-400",
          trend === "neutral" && "text-white"
        )}
      >
        {value}
      </p>
      {subtitle && <p className="text-xs text-neutral-500 mt-1">{subtitle}</p>}
    </div>
  );
}
