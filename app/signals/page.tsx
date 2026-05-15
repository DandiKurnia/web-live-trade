"use client";

import { useEffect, useState } from "react";
import { useMarketSocket } from "@/lib/hooks";
import { fetchSignal } from "@/lib/api";
import { SignalData } from "@/lib/types";
import { MOCK_SIGNALS } from "@/lib/mock-data";
import { DashboardShell } from "@/components/DashboardShell";
import { SignalCard } from "@/components/SignalCard";
import { SignalHistoryTable } from "@/components/SignalHistoryTable";

const SYMBOLS = ["XAUUSD.m", "EURUSD.m", "GBPUSD.m", "BTCUSD.m"];

export default function SignalsPage() {
  const { connected } = useMarketSocket(SYMBOLS);
  const [signals, setSignals] = useState<Record<string, SignalData>>({});

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
        <div>
          <h1 className="text-xl font-bold text-white">Signals</h1>
          <p className="text-sm text-neutral-500 mt-0.5">
            Active trade signals and history
          </p>
        </div>

        <section>
          <h2 className="text-sm font-medium text-neutral-400 mb-3">Active Signals</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {SYMBOLS.map((symbol) => {
              const mock = MOCK_SIGNALS[symbol];
              return (
                <SignalCard
                  key={symbol}
                  data={signals[symbol] || null}
                  confidence={mock?.confidence}
                  entry={mock?.entry}
                  sl={mock?.sl}
                  tp={mock?.tp}
                />
              );
            })}
          </div>
        </section>

        <section>
          <h2 className="text-sm font-medium text-neutral-400 mb-3">Signal History</h2>
          <SignalHistoryTable />
        </section>
      </div>
    </DashboardShell>
  );
}
