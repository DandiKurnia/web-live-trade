"use client";

import { clsx } from "clsx";

interface AIOpinionCardProps {
  data: {
    success?: boolean;
    trigger_type?: string;
    ai_bias?: string;
    direction?: string;
    ai_confidence?: number;
    recommendation?: string;
    setup_quality?: string;
    entry_price?: number | null;
    entry_price_source?: string;
    stop_loss?: number | null;
    take_profit_1?: number | null;
    take_profit_2?: number | null;
    risk_reward?: number | null;
    summary?: string;
    entry_reason?: string;
    risk_warning?: string;
    should_create_trade_plan?: boolean;
    manual_approval_required?: boolean;
    notes?: string[];
    ai_available?: boolean;
    status?: string;
    exit_price?: number | null;
    exit_reason?: string | null;
    profit_loss?: number | null;
    resolved_at?: string | null;
    created_at?: string;
    message?: string;
  } | null;
}

export function AIOpinionCard({ data }: AIOpinionCardProps) {
  if (!data || data.ai_available === false) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-2">AI Second Opinion</h3>
        <p className="text-xs text-neutral-500">AI provider unavailable</p>
      </div>
    );
  }

  if (!data.ai_bias && !data.direction) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-2">AI Second Opinion</h3>
        <p className="text-xs text-neutral-500">{data.message || "No AI summary yet. Click 'Run AI Analysis' or wait for auto schedule."}</p>
      </div>
    );
  }

  const dirColor =
    data.direction === "BUY" ? "text-green-400" :
    data.direction === "SELL" ? "text-red-400" : "text-neutral-300";

  const dirBg =
    data.direction === "BUY" ? "bg-green-500/10 border-green-500/20" :
    data.direction === "SELL" ? "bg-red-500/10 border-red-500/20" :
    "bg-neutral-500/10 border-neutral-500/20";

  const recColor =
    data.recommendation === "VALID_SETUP" ? "bg-green-500/10 text-green-400 border-green-500/20" :
    data.recommendation === "WATCH" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
    data.recommendation === "AVOID" ? "bg-red-500/10 text-red-400 border-red-500/20" :
    "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";

  const qualityColor =
    data.setup_quality === "STRONG" ? "text-green-400" :
    data.setup_quality === "GOOD" ? "text-blue-400" :
    data.setup_quality === "FAIR" ? "text-yellow-400" : "text-red-400";

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-neutral-400">AI Second Opinion</h3>
        <div className="flex items-center gap-2">
          {data.status === "ACTIVE" && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 animate-pulse">
              ACTIVE
            </span>
          )}
          {data.status && ["SL_HIT", "TP1_HIT", "TP2_HIT"].includes(data.status) && (
            <span className={clsx(
              "px-1.5 py-0.5 rounded text-[10px] font-bold border",
              data.status === "SL_HIT"
                ? "bg-red-500/20 text-red-400 border-red-500/30"
                : "bg-green-500/20 text-green-400 border-green-500/30"
            )}>
              {data.status.replace("_", " ")}
            </span>
          )}
          {data.trigger_type && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-neutral-800 text-neutral-400">
              {data.trigger_type}
            </span>
          )}
          <span className={clsx("px-2 py-0.5 rounded-full text-xs font-semibold border", recColor)}>
            {data.recommendation}
          </span>
        </div>
      </div>

      {/* Direction badge */}
      <div className={clsx("rounded-lg border p-3 mb-4", dirBg)}>
        <div className="flex items-center justify-between">
          <div>
            <span className={clsx("text-lg font-bold", dirColor)}>{data.direction}</span>
            {data.entry_price_source && data.entry_price_source !== "NONE" && (
              <p className="text-xs text-neutral-500 mt-0.5">
                Entry uses {data.entry_price_source} price
              </p>
            )}
          </div>
          {data.entry_price && (
            <div className="text-right">
              <p className="text-sm font-mono font-bold text-white">{data.entry_price.toFixed(5)}</p>
              <p className="text-[10px] text-neutral-500">Entry Price</p>
            </div>
          )}
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div>
          <p className="text-xs text-neutral-500">Bias</p>
          <p className={clsx("text-sm font-semibold",
            data.ai_bias === "BULLISH" ? "text-green-400" :
            data.ai_bias === "BEARISH" ? "text-red-400" : "text-neutral-300"
          )}>{data.ai_bias}</p>
        </div>
        <div>
          <p className="text-xs text-neutral-500">Confidence</p>
          <p className="text-sm font-mono text-white">{data.ai_confidence}%</p>
        </div>
        <div>
          <p className="text-xs text-neutral-500">Quality</p>
          <p className={clsx("text-sm font-semibold", qualityColor)}>{data.setup_quality}</p>
        </div>
      </div>

      {/* SL/TP row */}
      {(data.stop_loss || data.take_profit_1) && (
        <div className="grid grid-cols-4 gap-2 mb-4 text-xs">
          <div>
            <p className="text-neutral-500">SL</p>
            <p className="font-mono text-red-400">{data.stop_loss?.toFixed(5) ?? "—"}</p>
          </div>
          <div>
            <p className="text-neutral-500">TP1</p>
            <p className="font-mono text-green-400">{data.take_profit_1?.toFixed(5) ?? "—"}</p>
          </div>
          <div>
            <p className="text-neutral-500">TP2</p>
            <p className="font-mono text-green-400">{data.take_profit_2?.toFixed(5) ?? "—"}</p>
          </div>
          <div>
            <p className="text-neutral-500">R:R</p>
            <p className="font-mono text-blue-400">{data.risk_reward?.toFixed(2) ?? "—"}</p>
          </div>
        </div>
      )}

      {/* Summary */}
      {data.summary && (
        <p className="text-xs text-neutral-300 mb-2">{data.summary}</p>
      )}

      {/* Entry reason */}
      {data.entry_reason && (
        <p className="text-xs text-neutral-400 mb-2">{data.entry_reason}</p>
      )}

      {/* Risk warning */}
      {data.risk_warning && (
        <div className="mt-3 p-2 rounded-lg bg-red-500/5 border border-red-500/10">
          <p className="text-xs text-red-400">{data.risk_warning}</p>
        </div>
      )}

      {/* Notes */}
      {data.notes && data.notes.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-neutral-500 mb-1">Notes:</p>
          <ul className="space-y-0.5">
            {data.notes.map((note, i) => (
              <li key={i} className="text-xs text-neutral-400 flex items-start gap-1.5">
                <span className="text-neutral-600 mt-0.5">•</span>
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-[var(--border)] flex items-center justify-between">
        {data.created_at && (
          <p className="text-[10px] text-neutral-600">
            {new Date(data.created_at).toLocaleString()}
          </p>
        )}
        {data.manual_approval_required && (
          <p className="text-[10px] text-yellow-500">Manual approval required</p>
        )}
      </div>
    </div>
  );
}
