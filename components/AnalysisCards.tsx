"use client";

import { clsx } from "clsx";

interface AnalysisCardsProps {
  analysis: any;
}

export function ADXCard({ value, condition }: { value?: number; condition?: string }) {
  const color =
    (value ?? 0) >= 25 ? "text-green-400" :
    (value ?? 0) >= 20 ? "text-yellow-400" : "text-red-400";

  const label =
    (value ?? 0) >= 25 ? "Strong Trend" :
    (value ?? 0) >= 20 ? "Acceptable" : "Ranging";

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
      <p className="text-xs text-neutral-500 mb-1">ADX (14)</p>
      <p className={clsx("text-lg font-mono font-semibold", color)}>{value?.toFixed(1) ?? "—"}</p>
      <p className="text-xs text-neutral-500 mt-1">{label}</p>
    </div>
  );
}

export function MACDCard({ macd }: { macd?: { macd_line: number; signal_line: number; histogram: number } }) {
  if (!macd) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
        <p className="text-xs text-neutral-500 mb-1">MACD</p>
        <p className="text-sm text-neutral-500">No data</p>
      </div>
    );
  }

  const histColor = macd.histogram > 0 ? "text-green-400" : macd.histogram < 0 ? "text-red-400" : "text-neutral-400";
  const momentum = macd.histogram > 0 ? "Bullish" : macd.histogram < 0 ? "Bearish" : "Neutral";

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
      <p className="text-xs text-neutral-500 mb-2">MACD</p>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <p className="text-neutral-500">Line</p>
          <p className="font-mono text-neutral-300">{macd.macd_line.toFixed(5)}</p>
        </div>
        <div>
          <p className="text-neutral-500">Signal</p>
          <p className="font-mono text-neutral-300">{macd.signal_line.toFixed(5)}</p>
        </div>
        <div>
          <p className="text-neutral-500">Histogram</p>
          <p className={clsx("font-mono font-semibold", histColor)}>{macd.histogram.toFixed(5)}</p>
        </div>
      </div>
      <p className={clsx("text-xs mt-2", histColor)}>Momentum: {momentum}</p>
    </div>
  );
}

export function SupportResistanceCard({ sr }: { sr?: any }) {
  if (!sr) return null;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
      <p className="text-xs text-neutral-500 mb-2">Support / Resistance</p>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <p className="text-neutral-500">Nearest Resistance</p>
          <p className="font-mono text-red-400">{sr.nearest_resistance?.toFixed(5) ?? "—"}</p>
          <p className="text-neutral-600 mt-0.5">{sr.distance_to_resistance_atr?.toFixed(2) ?? "—"} ATR away</p>
        </div>
        <div>
          <p className="text-neutral-500">Nearest Support</p>
          <p className="font-mono text-green-400">{sr.nearest_support?.toFixed(5) ?? "—"}</p>
          <p className="text-neutral-600 mt-0.5">{sr.distance_to_support_atr?.toFixed(2) ?? "—"} ATR away</p>
        </div>
      </div>
    </div>
  );
}

export function FibonacciCard({ fib, levels }: { fib?: any; levels?: any }) {
  if (!fib || !fib.valid) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
        <p className="text-xs text-neutral-500 mb-1">Fibonacci</p>
        <p className="text-xs text-neutral-600">No valid Fibonacci levels (mixed trend)</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
      <p className="text-xs text-neutral-500 mb-2">Fibonacci Pullback Zone</p>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-neutral-400">Direction:</span>
        <span className={clsx("text-xs font-semibold", fib.direction === "BUY" ? "text-green-400" : "text-red-400")}>
          {fib.direction}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs mb-2">
        <div>
          <p className="text-neutral-500">Zone Low (61.8%)</p>
          <p className="font-mono text-neutral-300">{fib.zone_low?.toFixed(5)}</p>
        </div>
        <div>
          <p className="text-neutral-500">Zone High (38.2%)</p>
          <p className="font-mono text-neutral-300">{fib.zone_high?.toFixed(5)}</p>
        </div>
      </div>
      {levels && Object.keys(levels).length > 0 && (
        <div className="grid grid-cols-4 gap-1 text-[10px] text-neutral-500 mt-2 pt-2 border-t border-[var(--border)]">
          {Object.entries(levels).map(([key, val]) => (
            <div key={key}>
              <p>{(parseFloat(key) * 100).toFixed(1)}%</p>
              <p className="font-mono text-neutral-400">{(val as number).toFixed(2)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function PullbackStatusCard({ pullback }: { pullback?: any }) {
  if (!pullback) return null;

  const statusColor =
    pullback.status?.includes("READY") ? "text-green-400" :
    pullback.status === "WAITING_REJECTION" ? "text-yellow-400" :
    pullback.status === "WAITING_PULLBACK" ? "text-blue-400" : "text-neutral-400";

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
      <p className="text-xs text-neutral-500 mb-2">Pullback Entry</p>
      <p className={clsx("text-sm font-semibold mb-2", statusColor)}>{pullback.status}</p>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <p className="text-neutral-500">Near EMA20</p>
          <p className={pullback.near_ema20 ? "text-green-400" : "text-red-400"}>
            {pullback.near_ema20 ? "Yes" : "No"}
          </p>
        </div>
        <div>
          <p className="text-neutral-500">In Fib Zone</p>
          <p className={pullback.in_fib_zone ? "text-green-400" : "text-red-400"}>
            {pullback.in_fib_zone ? "Yes" : "No"}
          </p>
        </div>
        <div>
          <p className="text-neutral-500">Rejection Candle</p>
          <p className={pullback.rejection_candle ? "text-green-400" : "text-red-400"}>
            {pullback.rejection_candle ? "Yes" : "No"}
          </p>
        </div>
        <div>
          <p className="text-neutral-500">EMA Distance</p>
          <p className="font-mono text-neutral-300">{pullback.ema20_distance?.toFixed(5) ?? "—"}</p>
        </div>
      </div>
    </div>
  );
}

export function RiskCheckCard({ blocks, warnings }: { blocks?: string[]; warnings?: string[] }) {
  if ((!blocks || blocks.length === 0) && (!warnings || warnings.length === 0)) {
    return (
      <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4">
        <p className="text-xs text-green-400 font-medium">Risk Check: PASSED</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
      <p className="text-xs text-neutral-500 mb-2">Risk Check</p>
      {blocks && blocks.length > 0 && (
        <div className="mb-2">
          <p className="text-xs text-red-400 font-medium mb-1">Blocked:</p>
          <ul className="space-y-0.5">
            {blocks.map((b, i) => (
              <li key={i} className="text-xs text-red-400 flex items-start gap-1.5">
                <span className="mt-0.5">✕</span> {b}
              </li>
            ))}
          </ul>
        </div>
      )}
      {warnings && warnings.length > 0 && (
        <div>
          <p className="text-xs text-yellow-400 font-medium mb-1">Warnings:</p>
          <ul className="space-y-0.5">
            {warnings.map((w, i) => (
              <li key={i} className="text-xs text-yellow-400 flex items-start gap-1.5">
                <span className="mt-0.5">⚠</span> {w}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function MarketConditionBadge({ condition }: { condition?: string }) {
  const color =
    condition === "TRENDING_STRONG" ? "bg-green-500/10 text-green-400 border-green-500/20" :
    condition === "TRENDING" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
    condition === "TRENDING_UP" ? "bg-green-500/10 text-green-400 border-green-500/20" :
    condition === "TRENDING_DOWN" ? "bg-red-500/10 text-red-400 border-red-500/20" :
    condition === "RANGING" ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" :
    condition === "MIXED" ? "bg-orange-500/10 text-orange-400 border-orange-500/20" :
    "bg-neutral-500/10 text-neutral-400 border-neutral-500/20";

  return (
    <span className={clsx("px-2 py-0.5 rounded-full text-xs font-semibold border", color)}>
      {condition || "UNKNOWN"}
    </span>
  );
}
