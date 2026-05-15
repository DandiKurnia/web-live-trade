"use client";

import { clsx } from "clsx";
import { AlertTriangle, Target, TrendingDown, TrendingUp } from "lucide-react";

interface ActiveAlertBannerProps {
  alert: {
    id: number;
    symbol: string;
    direction: string;
    ai_confidence: number;
    recommendation: string;
    setup_quality: string;
    entry_price: number | null;
    stop_loss: number | null;
    take_profit_1: number | null;
    take_profit_2: number | null;
    risk_reward: number | null;
    summary: string;
    status: string;
    exit_price?: number | null;
    exit_reason?: string | null;
    profit_loss?: number | null;
    resolved_at?: string | null;
    created_at: string;
  } | null;
  currentPrice?: number | null;
}

export function ActiveAlertBanner({ alert, currentPrice }: ActiveAlertBannerProps) {
  if (!alert) return null;

  const isActive = alert.status === "ACTIVE";
  const isResolved = ["SL_HIT", "TP1_HIT", "TP2_HIT"].includes(alert.status);
  const isBuy = alert.direction === "BUY";

  const borderColor = isResolved
    ? alert.status === "SL_HIT"
      ? "border-red-500/40"
      : "border-green-500/40"
    : isBuy
      ? "border-green-500/30"
      : "border-red-500/30";

  const bgColor = isResolved
    ? alert.status === "SL_HIT"
      ? "bg-red-500/5"
      : "bg-green-500/5"
    : isBuy
      ? "bg-green-500/5"
      : "bg-red-500/5";

  let currentPL: number | null = null;
  if (isActive && currentPrice && alert.entry_price) {
    currentPL = isBuy
      ? currentPrice - alert.entry_price
      : alert.entry_price - currentPrice;
  }

  return (
    <div className={clsx("rounded-xl border-2 p-4", borderColor, bgColor)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {isBuy ? (
            <TrendingUp size={18} className="text-green-400" />
          ) : (
            <TrendingDown size={18} className="text-red-400" />
          )}
          <span className={clsx("text-lg font-bold", isBuy ? "text-green-400" : "text-red-400")}>
            {alert.direction}
          </span>
          <span className="text-xs text-neutral-500">
            {alert.symbol.replace(".m", "")}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {isActive && (
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 animate-pulse">
              ACTIVE
            </span>
          )}
          {isResolved && (
            <span className={clsx(
              "px-2 py-0.5 rounded-full text-xs font-bold border",
              alert.status === "SL_HIT"
                ? "bg-red-500/20 text-red-400 border-red-500/30"
                : "bg-green-500/20 text-green-400 border-green-500/30"
            )}>
              {alert.status.replace("_", " ")}
            </span>
          )}
        </div>
      </div>

      {/* Price grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
        <div>
          <p className="text-[10px] text-neutral-500 uppercase">Entry</p>
          <p className="font-mono text-sm text-white">{alert.entry_price?.toFixed(5) ?? "—"}</p>
        </div>
        <div>
          <p className="text-[10px] text-neutral-500 uppercase">SL</p>
          <p className="font-mono text-sm text-red-400">{alert.stop_loss?.toFixed(5) ?? "—"}</p>
        </div>
        <div>
          <p className="text-[10px] text-neutral-500 uppercase">TP1</p>
          <p className="font-mono text-sm text-green-400">{alert.take_profit_1?.toFixed(5) ?? "—"}</p>
        </div>
        <div>
          <p className="text-[10px] text-neutral-500 uppercase">R:R</p>
          <p className="font-mono text-sm text-blue-400">{alert.risk_reward?.toFixed(2) ?? "—"}</p>
        </div>
      </div>

      {/* Current P/L for active alerts */}
      {isActive && currentPL !== null && (
        <div className="flex items-center gap-3 mb-3 p-2 rounded-lg bg-[var(--background)]">
          <Target size={14} className="text-neutral-400" />
          <span className="text-xs text-neutral-500">Current P/L:</span>
          <span className={clsx(
            "font-mono text-sm font-bold",
            currentPL >= 0 ? "text-green-400" : "text-red-400"
          )}>
            {currentPL >= 0 ? "+" : ""}{currentPL.toFixed(5)}
          </span>
        </div>
      )}

      {/* Resolved P/L */}
      {isResolved && alert.profit_loss !== null && (
        <div className="flex items-center gap-3 mb-3 p-2 rounded-lg bg-[var(--background)]">
          <Target size={14} className="text-neutral-400" />
          <span className="text-xs text-neutral-500">Result:</span>
          <span className={clsx(
            "font-mono text-sm font-bold",
            (alert.profit_loss ?? 0) >= 0 ? "text-green-400" : "text-red-400"
          )}>
            {(alert.profit_loss ?? 0) >= 0 ? "+" : ""}{alert.profit_loss?.toFixed(5)}
          </span>
          <span className="text-xs text-neutral-500">
            Exit: {alert.exit_price?.toFixed(5)}
          </span>
        </div>
      )}

      {/* Summary */}
      {alert.summary && (
        <p className="text-xs text-neutral-400">{alert.summary}</p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-3 pt-2 border-t border-[var(--border)]">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-neutral-600">
            Confidence: {alert.ai_confidence}%
          </span>
          <span className="text-[10px] text-neutral-600">
            Quality: {alert.setup_quality}
          </span>
        </div>
        <span className="text-[10px] text-neutral-600">
          {new Date(alert.created_at).toLocaleString()}
        </span>
      </div>
    </div>
  );
}
