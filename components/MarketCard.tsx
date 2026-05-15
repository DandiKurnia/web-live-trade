"use client";

import { TickData } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";
import { Sparkline } from "./PriceChart";
import Link from "next/link";
import { MOCK_CANDLES, MOCK_SIGNALS, SYMBOLS_CONFIG } from "@/lib/mock-data";

interface MarketCardProps {
  data: TickData | undefined;
  symbol: string;
}

export function MarketCard({ data, symbol }: MarketCardProps) {
  const config = SYMBOLS_CONFIG.find((s) => s.symbol === symbol);
  const mockSignal = MOCK_SIGNALS[symbol];
  const sparkData = MOCK_CANDLES[symbol]?.slice(-20).map((c) => c.close) || [];
  const decimals = config?.decimals ?? 5;

  const sparkColor =
    mockSignal?.signal === "BUY" ? "#22c55e" : mockSignal?.signal === "SELL" ? "#ef4444" : "#3b82f6";

  return (
    <Link href={`/market/${symbol}`}>
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 hover:border-neutral-600 transition-all hover:shadow-lg hover:shadow-black/20 group">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-white group-hover:text-blue-400 transition-colors">
              {symbol.replace(".m", "")}
            </h3>
            <p className="text-xs text-neutral-500">{config?.name || symbol}</p>
          </div>
          {mockSignal && <StatusBadge status={mockSignal.signal} />}
        </div>

        {data ? (
          <>
            <div className="flex items-end justify-between mb-3">
              <div>
                <p className="text-xl font-mono font-bold text-white">
                  {data.bid.toFixed(decimals)}
                </p>
                <p className="text-xs text-neutral-500 mt-0.5">
                  Ask: {data.ask.toFixed(decimals)}
                </p>
              </div>
              <Sparkline data={sparkData} color={sparkColor} />
            </div>

            <div className="flex items-center justify-between text-xs">
              <span className="text-neutral-500">
                Spread: <span className="text-neutral-300 font-mono">{data.spread.toFixed(decimals)}</span>
              </span>
              <span className="text-neutral-500">
                {new Date(data.time).toLocaleTimeString()}
              </span>
            </div>
          </>
        ) : (
          <div className="h-20 flex items-center justify-center">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-neutral-600 animate-pulse" />
              <span className="text-xs text-neutral-500">Waiting for data...</span>
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}
