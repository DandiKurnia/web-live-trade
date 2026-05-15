"use client";

import { SignalData } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface SignalCardProps {
  data: SignalData | null;
  loading?: boolean;
  confidence?: number;
  entry?: number;
  sl?: number;
  tp?: number;
}

export function SignalCard({ data, loading, confidence, entry, sl, tp }: SignalCardProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 animate-pulse">
        <div className="h-4 bg-neutral-800 rounded w-1/2 mb-3" />
        <div className="h-8 bg-neutral-800 rounded w-3/4 mb-2" />
        <div className="h-3 bg-neutral-800 rounded w-full" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
        <p className="text-sm text-neutral-500">No signal data</p>
      </div>
    );
  }

  const direction = data.signal || data.direction || "WAIT";
  const displaySignal = (direction === "BUY" || direction === "SELL") ? direction as "BUY" | "SELL" : "WAIT";
  const reason = data.reason || (data.reasons && data.reasons.length > 0 ? data.reasons[0] : "");

  const SignalIcon =
    displaySignal === "BUY" ? TrendingUp : displaySignal === "SELL" ? TrendingDown : Minus;

  const iconColor =
    displaySignal === "BUY" ? "text-green-400" : displaySignal === "SELL" ? "text-red-400" : "text-yellow-400";

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <SignalIcon size={18} className={iconColor} />
          <h3 className="text-sm font-semibold text-white">{data.symbol.replace(".m", "")}</h3>
        </div>
        <StatusBadge status={displaySignal} size="md" />
      </div>

      <p className="text-xs text-neutral-500 mb-4 line-clamp-2">{reason}</p>

      {confidence !== undefined && (
        <div className="mb-4">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-neutral-500">Confidence</span>
            <span className="text-neutral-300">{confidence}%</span>
          </div>
          <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-blue-500"
              style={{ width: `${confidence}%` }}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-2 text-xs">
        {entry !== undefined && (
          <div>
            <p className="text-neutral-500">Entry</p>
            <p className="font-mono text-neutral-200">{entry.toFixed(2)}</p>
          </div>
        )}
        {sl !== undefined && (
          <div>
            <p className="text-neutral-500">SL</p>
            <p className="font-mono text-red-400">{sl.toFixed(2)}</p>
          </div>
        )}
        {tp !== undefined && (
          <div>
            <p className="text-neutral-500">TP</p>
            <p className="font-mono text-green-400">{tp.toFixed(2)}</p>
          </div>
        )}
      </div>

      {(data.ema20 || data.ema50 || data.rsi) && (
        <div className="mt-3 pt-3 border-t border-[var(--border)] grid grid-cols-3 gap-2 text-xs">
          <div>
            <p className="text-neutral-500">EMA20</p>
            <p className="font-mono text-neutral-300">{data.ema20?.toFixed(2) ?? "—"}</p>
          </div>
          <div>
            <p className="text-neutral-500">EMA50</p>
            <p className="font-mono text-neutral-300">{data.ema50?.toFixed(2) ?? "—"}</p>
          </div>
          <div>
            <p className="text-neutral-500">RSI</p>
            <p className="font-mono text-neutral-300">{data.rsi?.toFixed(1) ?? "—"}</p>
          </div>
        </div>
      )}
    </div>
  );
}
