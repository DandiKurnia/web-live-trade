"use client";

import { clsx } from "clsx";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface TimeframeData {
  trend: string;
  ema20: number;
  ema50: number;
  rsi14: number;
  atr14: number;
}

interface MultiTimeframePanelProps {
  h1: TimeframeData | null;
  m30: TimeframeData | null;
  m15: TimeframeData | null;
  m5: TimeframeData | null;
  marketCondition?: string;
}

function TrendIcon({ trend }: { trend: string }) {
  if (trend.includes("BULLISH")) return <TrendingUp size={14} className="text-green-400" />;
  if (trend.includes("BEARISH")) return <TrendingDown size={14} className="text-red-400" />;
  return <Minus size={14} className="text-neutral-400" />;
}

function TimeframeRow({ label, data }: { label: string; data: TimeframeData | null }) {
  if (!data) {
    return (
      <div className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0">
        <span className="text-sm font-medium text-neutral-300">{label}</span>
        <span className="text-xs text-neutral-500">No data</span>
      </div>
    );
  }

  const trendColor =
    data.trend.includes("BULLISH") ? "text-green-400" :
    data.trend.includes("BEARISH") ? "text-red-400" : "text-neutral-400";

  return (
    <div className="py-3 border-b border-[var(--border)] last:border-0">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-neutral-200">{label}</span>
          <TrendIcon trend={data.trend} />
        </div>
        <span className={clsx("text-xs font-semibold", trendColor)}>{data.trend}</span>
      </div>
      <div className="grid grid-cols-4 gap-2 text-xs">
        <div>
          <p className="text-neutral-500">EMA20</p>
          <p className="font-mono text-neutral-300">{data.ema20.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-neutral-500">EMA50</p>
          <p className="font-mono text-neutral-300">{data.ema50.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-neutral-500">RSI</p>
          <p className="font-mono text-neutral-300">{data.rsi14.toFixed(1)}</p>
        </div>
        <div>
          <p className="text-neutral-500">ATR</p>
          <p className="font-mono text-neutral-300">{data.atr14.toFixed(4)}</p>
        </div>
      </div>
    </div>
  );
}

export function MultiTimeframePanel({ h1, m30, m15, m5, marketCondition }: MultiTimeframePanelProps) {
  const conditionColor =
    marketCondition === "TRENDING_UP" ? "text-green-400" :
    marketCondition === "TRENDING_DOWN" ? "text-red-400" : "text-yellow-400";

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-neutral-400">Multi-Timeframe Analysis</h3>
        {marketCondition && (
          <span className={clsx("text-xs font-semibold", conditionColor)}>
            {marketCondition?.replace("_", " ")}
          </span>
        )}
      </div>
      <TimeframeRow label="H1" data={h1} />
      <TimeframeRow label="M30" data={m30} />
      <TimeframeRow label="M15" data={m15} />
      <TimeframeRow label="M5" data={m5} />
    </div>
  );
}
