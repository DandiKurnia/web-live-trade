"use client";

import { clsx } from "clsx";
import { approveTradePlan, rejectTradePlan } from "@/lib/api";
import { useState } from "react";

interface TradePlanCardProps {
  data: {
    id?: number;
    symbol?: string;
    direction?: string;
    status?: string;
    entry_price?: number;
    stop_loss?: number;
    take_profit_1?: number;
    take_profit_2?: number;
    risk_reward?: number;
    confidence?: number;
    risk_percent?: number;
    manual_approval_required?: boolean;
    created_at?: string;
    message?: string;
  } | null;
  onUpdate?: () => void;
}

export function TradePlanCard({ data, onUpdate }: TradePlanCardProps) {
  const [loading, setLoading] = useState(false);

  if (!data || data.status === "NO_PLAN") {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-2">Trade Plan</h3>
        <p className="text-xs text-neutral-500">No active trade plan</p>
      </div>
    );
  }

  const dirColor = data.direction === "BUY" ? "text-green-400" : "text-red-400";
  const statusColor =
    data.status === "PENDING" ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" :
    data.status === "APPROVED" ? "bg-green-500/10 text-green-400 border-green-500/20" :
    data.status === "REJECTED" ? "bg-red-500/10 text-red-400 border-red-500/20" :
    "bg-neutral-500/10 text-neutral-400 border-neutral-500/20";

  async function handleApprove() {
    if (!data?.id) return;
    setLoading(true);
    try {
      await approveTradePlan(data.id);
      onUpdate?.();
    } catch {}
    setLoading(false);
  }

  async function handleReject() {
    if (!data?.id) return;
    setLoading(true);
    try {
      await rejectTradePlan(data.id);
      onUpdate?.();
    } catch {}
    setLoading(false);
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-neutral-400">Trade Plan</h3>
        <span className={clsx("px-2 py-0.5 rounded-full text-xs font-semibold border", statusColor)}>
          {data.status}
        </span>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <span className={clsx("text-lg font-bold", dirColor)}>{data.direction}</span>
        <span className="text-sm text-neutral-400">{data.symbol?.replace(".m", "")}</span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs mb-4">
        <div>
          <p className="text-neutral-500">Entry</p>
          <p className="font-mono text-white">{data.entry_price?.toFixed(5)}</p>
        </div>
        <div>
          <p className="text-neutral-500">Stop Loss</p>
          <p className="font-mono text-red-400">{data.stop_loss?.toFixed(5)}</p>
        </div>
        <div>
          <p className="text-neutral-500">TP1</p>
          <p className="font-mono text-green-400">{data.take_profit_1?.toFixed(5)}</p>
        </div>
        <div>
          <p className="text-neutral-500">TP2</p>
          <p className="font-mono text-green-400">{data.take_profit_2?.toFixed(5)}</p>
        </div>
        <div>
          <p className="text-neutral-500">Risk/Reward</p>
          <p className="font-mono text-blue-400">{data.risk_reward?.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-neutral-500">Confidence</p>
          <p className="font-mono text-white">{data.confidence}%</p>
        </div>
      </div>

      {data.status === "PENDING" && data.manual_approval_required && (
        <div className="flex gap-2 mt-4">
          <button
            onClick={handleApprove}
            disabled={loading}
            className="flex-1 px-4 py-2 rounded-lg bg-green-500/20 text-green-400 text-sm font-medium hover:bg-green-500/30 transition-colors disabled:opacity-50"
          >
            Approve
          </button>
          <button
            onClick={handleReject}
            disabled={loading}
            className="flex-1 px-4 py-2 rounded-lg bg-red-500/20 text-red-400 text-sm font-medium hover:bg-red-500/30 transition-colors disabled:opacity-50"
          >
            Reject
          </button>
        </div>
      )}

      <p className="text-xs text-neutral-600 mt-3">
        No automatic order execution. Manual approval only.
      </p>
    </div>
  );
}
