"use client";

import { useEffect, useState } from "react";
import { clsx } from "clsx";
import { fetchTradeHistory, fetchSignalHistory } from "@/lib/api";

export function SignalHistoryTable() {
  const [tab, setTab] = useState<"trades" | "signals" | "alerts">("trades");
  const [trades, setTrades] = useState<any[]>([]);
  const [signals, setSignals] = useState<any[]>([]);
  const [resolvedAlerts, setResolvedAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [tradeData, signalData] = await Promise.all([
          fetchTradeHistory(20),
          fetchSignalHistory(30),
        ]);
        setTrades(tradeData.trades || []);
        setSignals(signalData.signals || []);
        setResolvedAlerts(signalData.resolved_alerts || []);
      } catch {}
      setLoading(false);
    }
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading && trades.length === 0 && signals.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-8 text-center">
        <p className="text-sm text-neutral-500">Loading history...</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-[var(--border)]">
        <button
          onClick={() => setTab("trades")}
          className={clsx(
            "px-4 py-2.5 text-xs font-medium transition-colors",
            tab === "trades" ? "text-blue-400 border-b-2 border-blue-400" : "text-neutral-500 hover:text-neutral-300"
          )}
        >
          Trade History ({trades.length})
        </button>
        <button
          onClick={() => setTab("signals")}
          className={clsx(
            "px-4 py-2.5 text-xs font-medium transition-colors",
            tab === "signals" ? "text-blue-400 border-b-2 border-blue-400" : "text-neutral-500 hover:text-neutral-300"
          )}
        >
          Signal History ({signals.length})
        </button>
        <button
          onClick={() => setTab("alerts")}
          className={clsx(
            "px-4 py-2.5 text-xs font-medium transition-colors",
            tab === "alerts" ? "text-blue-400 border-b-2 border-blue-400" : "text-neutral-500 hover:text-neutral-300"
          )}
        >
          AI Alerts ({resolvedAlerts.length})
        </button>
      </div>

      {tab === "trades" && <TradeHistoryTab data={trades} />}
      {tab === "signals" && <SignalHistoryTab data={signals} />}
      {tab === "alerts" && <ResolvedAlertsTab data={resolvedAlerts} />}
    </div>
  );
}

function TradeHistoryTab({ data }: { data: any[] }) {
  if (data.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-sm text-neutral-500">No trade history yet. Approve a trade plan to see results here.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--border)] bg-[#0f1118]">
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Time</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Symbol</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Direction</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Entry</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">SL</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">TP1</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">R:R</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Status</th>
            <th className="text-right p-3 text-xs font-medium text-neutral-500">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => {
            const statusColor =
              row.status === "CLOSED" ? "bg-neutral-500/10 text-neutral-400" :
              row.status === "APPROVED" ? "bg-green-500/10 text-green-400" :
              row.status === "REJECTED" ? "bg-red-500/10 text-red-400" :
              "bg-yellow-500/10 text-yellow-400";

            return (
              <tr key={row.id} className="border-b border-[var(--border)] hover:bg-[#0f1118] transition-colors">
                <td className="p-3 text-xs text-neutral-400 whitespace-nowrap">
                  {row.created_at ? new Date(row.created_at).toLocaleString() : "—"}
                </td>
                <td className="p-3 font-mono text-xs text-neutral-200">{row.symbol?.replace(".m", "")}</td>
                <td className="p-3">
                  <span className={clsx(
                    "inline-flex px-2 py-0.5 rounded text-xs font-semibold",
                    row.direction === "BUY" ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
                  )}>
                    {row.direction}
                  </span>
                </td>
                <td className="p-3 font-mono text-xs text-neutral-300">{row.entry_price?.toFixed(5)}</td>
                <td className="p-3 font-mono text-xs text-red-400">{row.stop_loss?.toFixed(5)}</td>
                <td className="p-3 font-mono text-xs text-green-400">{row.take_profit_1?.toFixed(5)}</td>
                <td className="p-3 font-mono text-xs text-blue-400">{row.risk_reward?.toFixed(2)}</td>
                <td className="p-3">
                  <span className={clsx("inline-flex px-2 py-0.5 rounded text-xs font-medium", statusColor)}>
                    {row.status}
                  </span>
                </td>
                <td className="p-3 text-right font-mono text-xs text-neutral-300">{row.confidence}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function SignalHistoryTab({ data }: { data: any[] }) {
  if (data.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-sm text-neutral-500">No signal history yet. Signals are recorded when status changes.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--border)] bg-[#0f1118]">
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Time</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Symbol</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Status</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Direction</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">H1</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">M15</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">M5</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">ADX</th>
            <th className="text-right p-3 text-xs font-medium text-neutral-500">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => {
            const statusColor =
              row.status?.includes("CONFIRMED") ? "bg-green-500/10 text-green-400" :
              row.status?.includes("WATCH") ? "bg-blue-500/10 text-blue-400" :
              row.status === "CANCELLED" ? "bg-red-500/10 text-red-400" :
              row.status?.includes("PLAN_READY") ? "bg-purple-500/10 text-purple-400" :
              "bg-neutral-500/10 text-neutral-400";

            return (
              <tr key={row.id} className="border-b border-[var(--border)] hover:bg-[#0f1118] transition-colors">
                <td className="p-3 text-xs text-neutral-400 whitespace-nowrap">
                  {row.created_at ? new Date(row.created_at).toLocaleString() : "—"}
                </td>
                <td className="p-3 font-mono text-xs text-neutral-200">{row.symbol?.replace(".m", "")}</td>
                <td className="p-3">
                  <span className={clsx("inline-flex px-2 py-0.5 rounded text-xs font-medium", statusColor)}>
                    {row.status}
                  </span>
                </td>
                <td className="p-3 text-xs text-neutral-300">{row.direction || "—"}</td>
                <td className="p-3 text-xs text-neutral-400">{row.h1_trend || "—"}</td>
                <td className="p-3 text-xs text-neutral-400">{row.m15_trend || "—"}</td>
                <td className="p-3 text-xs text-neutral-400">{row.m5_trend || "—"}</td>
                <td className="p-3 font-mono text-xs text-neutral-300">{row.adx14?.toFixed(1) ?? "—"}</td>
                <td className="p-3 text-right font-mono text-xs text-neutral-300">{row.confidence}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ResolvedAlertsTab({ data }: { data: any[] }) {
  if (data.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-sm text-neutral-500">No resolved AI alerts yet. Alerts resolve when price hits SL or TP.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--border)] bg-[#0f1118]">
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Created</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Resolved</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Symbol</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Direction</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Result</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Entry</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">Exit</th>
            <th className="text-left p-3 text-xs font-medium text-neutral-500">P/L</th>
            <th className="text-right p-3 text-xs font-medium text-neutral-500">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => {
            const isProfit = (row.profit_loss ?? 0) >= 0;
            const resultColor = row.status === "SL_HIT"
              ? "bg-red-500/10 text-red-400"
              : "bg-green-500/10 text-green-400";

            return (
              <tr key={row.id} className="border-b border-[var(--border)] hover:bg-[#0f1118] transition-colors">
                <td className="p-3 text-xs text-neutral-400 whitespace-nowrap">
                  {row.created_at ? new Date(row.created_at).toLocaleString() : "—"}
                </td>
                <td className="p-3 text-xs text-neutral-400 whitespace-nowrap">
                  {row.resolved_at ? new Date(row.resolved_at).toLocaleString() : "—"}
                </td>
                <td className="p-3 font-mono text-xs text-neutral-200">{row.symbol?.replace(".m", "")}</td>
                <td className="p-3">
                  <span className={clsx(
                    "inline-flex px-2 py-0.5 rounded text-xs font-semibold",
                    row.direction === "BUY" ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
                  )}>
                    {row.direction}
                  </span>
                </td>
                <td className="p-3">
                  <span className={clsx("inline-flex px-2 py-0.5 rounded text-xs font-medium", resultColor)}>
                    {row.status?.replace("_", " ")}
                  </span>
                </td>
                <td className="p-3 font-mono text-xs text-neutral-300">{row.entry_price?.toFixed(5)}</td>
                <td className="p-3 font-mono text-xs text-neutral-300">{row.exit_price?.toFixed(5) ?? "—"}</td>
                <td className={clsx("p-3 font-mono text-xs font-semibold", isProfit ? "text-green-400" : "text-red-400")}>
                  {row.profit_loss != null ? `${isProfit ? "+" : ""}${row.profit_loss.toFixed(5)}` : "—"}
                </td>
                <td className="p-3 text-right font-mono text-xs text-neutral-300">{row.ai_confidence}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
