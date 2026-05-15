"use client";

import { useState, useEffect } from "react";
import { triggerAIAnalysis, fetchAISummary } from "@/lib/api";
import { SYMBOLS_CONFIG } from "@/lib/mock-data";
import { Bot, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import { clsx } from "clsx";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AIAnalysisButtonProps {
  symbol?: string;
  onResult?: (data: any) => void;
}

export function AIAnalysisButton({ symbol, onResult }: AIAnalysisButtonProps) {
  const [selectedSymbol, setSelectedSymbol] = useState(symbol || SYMBOLS_CONFIG[0].symbol);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);
  const [schedulerStatus, setSchedulerStatus] = useState<any>(null);

  useEffect(() => {
    async function loadStatus() {
      try {
        const res = await fetch(`${API_BASE}/api/ai/status`);
        if (res.ok) setSchedulerStatus(await res.json());
      } catch {}
    }
    loadStatus();
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((c) => Math.max(0, c - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await triggerAIAnalysis(selectedSymbol);
      setResult(data);
      onResult?.(data);
      setCooldown(schedulerStatus?.manual_cooldown_seconds || 15);
    } catch (e: any) {
      if (e.message?.includes("429") || e.message?.includes("Cooldown")) {
        const match = e.message.match(/(\d+)\s*seconds/);
        setCooldown(match ? parseInt(match[1]) : 15);
        setError("Cooldown active. Please wait.");
      } else {
        setError(e.message || "AI analysis failed");
      }
    }
    setLoading(false);
  }

  const isDisabled = loading || cooldown > 0;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
      <div className="flex items-center gap-2 mb-4">
        <Bot size={18} className="text-blue-400" />
        <h3 className="text-sm font-medium text-white">Manual AI Analysis</h3>
      </div>

      <div className="flex gap-2 mb-4">
        {!symbol && (
          <select
            value={selectedSymbol}
            onChange={(e) => { setSelectedSymbol(e.target.value); setResult(null); setError(null); }}
            className="flex-1 px-3 py-2 rounded-lg bg-[var(--background)] border border-[var(--border)] text-sm text-white outline-none focus:border-blue-500 transition-colors"
          >
            {SYMBOLS_CONFIG.map((s) => (
              <option key={s.symbol} value={s.symbol}>
                {s.symbol.replace(".m", "")} — {s.name}
              </option>
            ))}
          </select>
        )}
        <button
          onClick={handleAnalyze}
          disabled={isDisabled}
          className={clsx(
            "px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2",
            isDisabled
              ? "bg-neutral-800 text-neutral-500 cursor-not-allowed"
              : "bg-blue-500 hover:bg-blue-600 text-white"
          )}
        >
          {loading ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              Analyzing...
            </>
          ) : cooldown > 0 ? (
            <>
              <Clock size={14} />
              {cooldown}s
            </>
          ) : (
            <>
              <Bot size={14} />
              Run AI Analysis
            </>
          )}
        </button>
      </div>

      {/* Scheduler info */}
      {schedulerStatus && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-neutral-500 mb-3">
          <span>Auto: {schedulerStatus.auto_enabled ? "ON" : "OFF"}</span>
          <span>Schedule: :{schedulerStatus.allowed_minutes?.join(", :")}</span>
          <span>TZ: {schedulerStatus.timezone}</span>
          {schedulerStatus.next_auto_run_at && (
            <span>Next: {new Date(schedulerStatus.next_auto_run_at).toLocaleTimeString()}</span>
          )}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/5 border border-red-500/10">
          <XCircle size={14} className="text-red-400" />
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}

      {result && result.success && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle size={14} className="text-green-400" />
            <span className="text-xs text-green-400">Analysis complete</span>
          </div>

          {/* Direction badge */}
          <div className={clsx(
            "rounded-lg border p-3",
            result.direction === "BUY" ? "bg-green-500/10 border-green-500/20" :
            result.direction === "SELL" ? "bg-red-500/10 border-red-500/20" :
            "bg-neutral-500/10 border-neutral-500/20"
          )}>
            <div className="flex items-center justify-between">
              <div>
                <span className={clsx(
                  "text-lg font-bold",
                  result.direction === "BUY" ? "text-green-400" :
                  result.direction === "SELL" ? "text-red-400" : "text-neutral-300"
                )}>
                  {result.direction}
                </span>
                {result.entry_price_source && result.entry_price_source !== "NONE" && (
                  <p className="text-xs text-neutral-500">
                    Entry uses {result.entry_price_source} price
                  </p>
                )}
              </div>
              {result.entry_price && (
                <div className="text-right">
                  <p className="text-sm font-mono font-bold text-white">{result.entry_price.toFixed(5)}</p>
                  <p className="text-[10px] text-neutral-500">Entry</p>
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <p className="text-xs text-neutral-500">Bias</p>
              <p className={clsx(
                "text-sm font-semibold",
                result.ai_bias === "BULLISH" ? "text-green-400" :
                result.ai_bias === "BEARISH" ? "text-red-400" : "text-neutral-300"
              )}>
                {result.ai_bias}
              </p>
            </div>
            <div>
              <p className="text-xs text-neutral-500">Confidence</p>
              <p className="text-sm font-mono text-white">{result.ai_confidence}%</p>
            </div>
            <div>
              <p className="text-xs text-neutral-500">Recommendation</p>
              <p className={clsx(
                "text-sm font-semibold",
                result.recommendation === "VALID_SETUP" ? "text-green-400" :
                result.recommendation === "AVOID" ? "text-red-400" :
                result.recommendation === "WATCH" ? "text-blue-400" : "text-yellow-400"
              )}>
                {result.recommendation}
              </p>
            </div>
          </div>

          {/* SL/TP */}
          {(result.stop_loss || result.take_profit_1) && (
            <div className="grid grid-cols-4 gap-2 text-xs">
              <div>
                <p className="text-neutral-500">SL</p>
                <p className="font-mono text-red-400">{result.stop_loss?.toFixed(5) ?? "—"}</p>
              </div>
              <div>
                <p className="text-neutral-500">TP1</p>
                <p className="font-mono text-green-400">{result.take_profit_1?.toFixed(5) ?? "—"}</p>
              </div>
              <div>
                <p className="text-neutral-500">TP2</p>
                <p className="font-mono text-green-400">{result.take_profit_2?.toFixed(5) ?? "—"}</p>
              </div>
              <div>
                <p className="text-neutral-500">R:R</p>
                <p className="font-mono text-blue-400">{result.risk_reward?.toFixed(2) ?? "—"}</p>
              </div>
            </div>
          )}

          {result.summary && (
            <p className="text-xs text-neutral-300">{result.summary}</p>
          )}

          {result.entry_reason && (
            <p className="text-xs text-neutral-400">{result.entry_reason}</p>
          )}

          {result.risk_warning && (
            <div className="p-2 rounded-lg bg-red-500/5 border border-red-500/10">
              <p className="text-xs text-red-400">{result.risk_warning}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
