export interface TickData {
  symbol: string;
  bid: number;
  ask: number;
  spread: number;
  time: string;
}

export interface SignalData {
  symbol: string;
  status: string;
  direction: string | null;
  confidence: number;
  reasons: string[];
  h1_trend?: string;
  m30_trend?: string;
  m15_trend?: string;
  m5_trend?: string;
  rsi14?: number;
  atr14?: number;
  spread?: number;
  timeframe?: string;
  candle_time?: string;
  confirmation_reason?: string;
  // Legacy fields (from old API)
  signal?: "BUY" | "SELL" | "WAIT";
  reason?: string;
  ema20?: number;
  ema50?: number;
  rsi?: number;
  bid?: number;
  ask?: number;
}
