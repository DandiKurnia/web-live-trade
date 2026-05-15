"use client";

import { clsx } from "clsx";

interface SignalLifecycleCardProps {
  data: {
    symbol?: string;
    status?: string;
    direction?: string | null;
    confidence?: number;
    reasons?: string[];
    h1_trend?: string;
    m15_trend?: string;
    m5_trend?: string;
    rsi14?: number;
    atr14?: number;
    spread?: number;
    candle_time?: string;
    confirmation_reason?: string;
  } | null;
}

const STATUS_COLORS: Record<string, string> = {
  WAIT: "bg-neutral-500/10 text-neutral-400 border-neutral-500/20",
  WATCH_BUY: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  WATCH_SELL: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  BUY_CONFIRMED: "bg-green-500/10 text-green-400 border-green-500/20",
  SELL_CONFIRMED: "bg-red-500/10 text-red-400 border-red-500/20",
  BUY_PLAN_READY: "bg-green-500/20 text-green-300 border-green-500/30",
  SELL_PLAN_READY: "bg-red-500/20 text-red-300 border-red-500/30",
  TRADE_ACTIVE: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  TRADE_CLOSED: "bg-neutral-500/10 text-neutral-400 border-neutral-500/20",
  CANCELLED: "bg-red-500/10 text-red-400 border-red-500/20",
};

export function SignalLifecycleCard({ data }: SignalLifecycleCardProps) {
  if (!data) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-2">Signal Status</h3>
        <p className="text-xs text-neutral-500">No signal data</p>
      </div>
    );
  }

  const statusColor = STATUS_COLORS[data.status || "WAIT"] || STATUS_COLORS.WAIT;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-neutral-400">Signal Lifecycle</h3>
        <span className={clsx("px-2.5 py-1 rounded-full text-xs font-bold border", statusColor)}>
          {data.status}
        </span>
      </div>

      {data.confidence !== undefined && data.confidence > 0 && (
        <div className="mb-4">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-neutral-500">Confidence</span>
            <span className="text-neutral-300">{data.confidence}%</span>
          </div>
          <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
            <div
              className={clsx(
                "h-full rounded-full transition-all",
                data.confidence >= 70 ? "bg-green-500" :
                data.confidence >= 50 ? "bg-yellow-500" : "bg-red-500"
              )}
              style={{ width: `${data.confidence}%` }}
            />
          </div>
        </div>
      )}

      {data.reasons && data.reasons.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-neutral-500 mb-1">Reasons:</p>
          <ul className="space-y-0.5">
            {data.reasons.map((r, i) => (
              <li key={i} className="text-xs text-neutral-300 flex items-start gap-1.5">
                <span className="text-neutral-600 mt-0.5">•</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.confirmation_reason && (
        <div className="mt-3 p-2 rounded-lg bg-blue-500/5 border border-blue-500/10">
          <p className="text-xs text-blue-400">{data.confirmation_reason}</p>
        </div>
      )}

      {data.candle_time && (
        <p className="text-xs text-neutral-600 mt-3">
          Last candle: {new Date(data.candle_time).toLocaleString()}
        </p>
      )}
    </div>
  );
}
