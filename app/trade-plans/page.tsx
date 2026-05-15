"use client";

import { useEffect, useState } from "react";
import { useMarketSocket } from "@/lib/hooks";
import { fetchTradePlan } from "@/lib/api";
import { DashboardShell } from "@/components/DashboardShell";
import { TradePlanCard } from "@/components/TradePlanCard";

const SYMBOLS = ["XAUUSD.m", "EURUSD.m", "GBPUSD.m", "BTCUSD.m"];

export default function TradePlansPage() {
  const { connected } = useMarketSocket(SYMBOLS);
  const [plans, setPlans] = useState<Record<string, any>>({});

  async function loadPlans() {
    for (const symbol of SYMBOLS) {
      try {
        const data = await fetchTradePlan(symbol);
        setPlans((prev) => ({ ...prev, [symbol]: data }));
      } catch {}
    }
  }

  useEffect(() => {
    loadPlans();
    const interval = setInterval(loadPlans, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <DashboardShell connected={connected}>
      <div className="space-y-6">
        <div className="rounded-lg bg-yellow-500/5 border border-yellow-500/20 px-4 py-2">
          <p className="text-xs text-yellow-400">
            Demo analysis only. No automatic live order execution.
          </p>
        </div>

        <div>
          <h1 className="text-xl font-bold text-white">Trade Plans</h1>
          <p className="text-sm text-neutral-500 mt-0.5">
            Review and approve/reject trade plans
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {SYMBOLS.map((symbol) => (
            <TradePlanCard
              key={symbol}
              data={plans[symbol] || null}
              onUpdate={loadPlans}
            />
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
