"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useMarketSocket } from "@/lib/hooks";
import { fetchSignal, fetchAnalysis, fetchTradePlan, fetchAISummary, fetchActiveAlerts } from "@/lib/api";
import { MOCK_CANDLES, SYMBOLS_CONFIG } from "@/lib/mock-data";
import { DashboardShell } from "@/components/DashboardShell";
import { PriceChart } from "@/components/PriceChart";
import { IndicatorCard } from "@/components/IndicatorCard";
import { TimeframeSelector } from "@/components/TimeframeSelector";
import { MultiTimeframePanel } from "@/components/MultiTimeframePanel";
import { SignalLifecycleCard } from "@/components/SignalLifecycleCard";
import { TradePlanCard } from "@/components/TradePlanCard";
import { AIOpinionCard } from "@/components/AIOpinionCard";
import { AIAnalysisButton } from "@/components/AIAnalysisButton";
import { ADXCard, MACDCard, SupportResistanceCard, FibonacciCard, PullbackStatusCard, RiskCheckCard, MarketConditionBadge } from "@/components/AnalysisCards";
import { ActiveAlertBanner } from "@/components/ActiveAlertBanner";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function SymbolPage() {
  const params = useParams();
  const symbol = params.symbol as string;
  const { prices, connected } = useMarketSocket([symbol]);
  const [signal, setSignal] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [tradePlan, setTradePlan] = useState<any>(null);
  const [aiSummary, setAiSummary] = useState<any>(null);
  const [activeAlert, setActiveAlert] = useState<any>(null);
  const [timeframe, setTimeframe] = useState("M5");

  const config = SYMBOLS_CONFIG.find((s) => s.symbol.toLowerCase() === symbol.toLowerCase());
  const decimals = config?.decimals ?? 5;
  const tick = prices[symbol];
  const candles = MOCK_CANDLES[symbol] || [];

  async function loadData() {
    try { setSignal(await fetchSignal(symbol)); } catch {}
    try { setAnalysis(await fetchAnalysis(symbol)); } catch {}
    try { setTradePlan(await fetchTradePlan(symbol)); } catch {}
    try { setAiSummary(await fetchAISummary(symbol)); } catch {}
    try {
      const alertData = await fetchActiveAlerts();
      const symbolAlert = alertData.alerts?.find((a: any) => a.symbol.toLowerCase() === symbol.toLowerCase());
      setActiveAlert(symbolAlert || null);
    } catch {}
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [symbol]);

  return (
    <DashboardShell connected={connected}>
      <div className="space-y-6">
        {/* Warning banner */}
        <div className="rounded-lg bg-yellow-500/5 border border-yellow-500/20 px-4 py-2">
          <p className="text-xs text-yellow-400">
            Demo analysis only. No automatic live order execution.
          </p>
        </div>

        {/* Active AI Alert */}
        <ActiveAlertBanner alert={activeAlert} currentPrice={tick?.bid} />

        {/* Header */}
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="p-2 rounded-lg hover:bg-[var(--border)] text-neutral-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={18} />
          </Link>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-white">
                {symbol.replace(".m", "")}
              </h1>
              {signal?.status && (
                <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  {signal.status}
                </span>
              )}
            </div>
            <p className="text-sm text-neutral-500">{config?.name || symbol}</p>
          </div>
          {tick && (
            <div className="text-right">
              <p className="text-2xl font-mono font-bold text-white">
                {tick.bid.toFixed(decimals)}
              </p>
              <p className="text-xs text-neutral-500">
                Spread: {tick.spread.toFixed(decimals)}
              </p>
            </div>
          )}
        </div>

        {/* Chart */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-neutral-400">Price Chart</h2>
            <TimeframeSelector selected={timeframe} onChange={setTimeframe} />
          </div>
          <PriceChart data={candles} height={300} />
        </div>

        {/* Indicators row */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <IndicatorCard label="Bid" value={tick ? tick.bid.toFixed(decimals) : "—"} />
          <IndicatorCard label="Ask" value={tick ? tick.ask.toFixed(decimals) : "—"} />
          <IndicatorCard label="Spread" value={tick ? tick.spread.toFixed(decimals) : "—"} />
          <IndicatorCard
            label="RSI (14)"
            value={analysis?.m5?.rsi14?.toFixed(1) || "—"}
            trend={analysis?.m5?.rsi14 > 60 ? "up" : analysis?.m5?.rsi14 < 40 ? "down" : "neutral"}
          />
          <IndicatorCard
            label="ATR (14)"
            value={analysis?.m5?.atr14?.toFixed(5) || "—"}
          />
        </div>

        {/* ADX + MACD + S/R row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <ADXCard value={analysis?.m5?.adx14} condition={analysis?.m5?.market_condition} />
          <MACDCard macd={analysis?.m5?.macd} />
          <SupportResistanceCard sr={analysis?.m5?.support_resistance} />
        </div>

        {/* Fibonacci + Pullback */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <FibonacciCard fib={analysis?.fibonacci} levels={analysis?.fibonacci_levels} />
          <PullbackStatusCard pullback={analysis?.pullback} />
        </div>

        {/* Risk check */}
        {signal && (
          <RiskCheckCard blocks={signal.blocked_reasons} warnings={signal.warnings} />
        )}

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left column */}
          <div className="space-y-6">
            <MultiTimeframePanel
              h1={analysis?.h1 || null}
              m30={analysis?.m30 || null}
              m15={analysis?.m15 || null}
              m5={analysis?.m5 || null}
              marketCondition={analysis?.market_condition}
            />
            <SignalLifecycleCard data={signal} />
          </div>

          {/* Right column */}
          <div className="space-y-6">
            <TradePlanCard data={tradePlan} onUpdate={loadData} />
            <AIAnalysisButton symbol={symbol} onResult={(data) => setAiSummary(data)} />
            <AIOpinionCard data={aiSummary} />
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
