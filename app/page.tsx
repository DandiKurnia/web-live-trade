"use client";

import { useEffect, useState } from "react";
import { useMarketSocket } from "@/lib/hooks";
import { fetchSignal } from "@/lib/api";
import { MOCK_CANDLES } from "@/lib/mock-data";
import { DashboardShell } from "@/components/DashboardShell";
import { MarketCard } from "@/components/MarketCard";
import { SignalLifecycleCard } from "@/components/SignalLifecycleCard";
import { SignalHistoryTable } from "@/components/SignalHistoryTable";
import { PriceChart } from "@/components/PriceChart";
import { AIAnalysisButton } from "@/components/AIAnalysisButton";
import { Activity } from "lucide-react";

const SYMBOLS = ["XAUUSD.m", "EURUSD.m", "GBPUSD.m", "BTCUSD.m"];

export default function Dashboard() {
  const { prices, connected } = useMarketSocket(SYMBOLS);
  const [signals, setSignals] = useState<Record<string, any>>({});

  useEffect(() => {
    async function loadSignals() {
      for (const symbol of SYMBOLS) {
        try {
          const data = await fetchSignal(symbol);
          setSignals((prev) => ({ ...prev, [symbol]: data }));
        } catch {}
      }
    }
    loadSignals();
    const interval = setInterval(loadSignals, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <DashboardShell connected={connected}>
      <div className="space-y-6">
        {/* Warning banner */}
        <div className="rounded-lg bg-yellow-500/5 border border-yellow-500/20 px-4 py-2">
          <p className="text-xs text-yellow-400">
            Demo analysis only. No automatic live order execution.
          </p>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Dashboard</h1>
            <p className="text-sm text-neutral-500 mt-0.5">
              Live market overview
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-neutral-400">
            <Activity size={14} className={connected ? "text-green-400" : "text-red-400"} />
            {connected ? "Real-time" : "Polling"}
          </div>
        </div>

        <section>
          <h2 className="text-sm font-medium text-neutral-400 mb-3">Markets</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {SYMBOLS.map((symbol) => (
              <MarketCard key={symbol} symbol={symbol} data={prices[symbol]} />
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-sm font-medium text-neutral-400 mb-3">Price Overview — XAUUSD</h2>
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
            <PriceChart data={MOCK_CANDLES["XAUUSD.m"]} height={250} />
          </div>
        </section>

        <section>
          <h2 className="text-sm font-medium text-neutral-400 mb-3">Signal Status</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {SYMBOLS.map((symbol) => (
              <SignalLifecycleCard key={symbol} data={signals[symbol] || null} />
            ))}
          </div>
        </section>

        <section>
          <AIAnalysisButton />
        </section>

        <section>
          <h2 className="text-sm font-medium text-neutral-400 mb-3">Signal History</h2>
          <SignalHistoryTable />
        </section>
      </div>
    </DashboardShell>
  );
}
