export const SYMBOLS_CONFIG = [
  { symbol: "XAUUSD.m", name: "Gold vs USD", decimals: 2 },
  { symbol: "EURUSD.m", name: "Euro vs USD", decimals: 5 },
  { symbol: "GBPUSD.m", name: "Pound vs USD", decimals: 5 },
  { symbol: "BTCUSD.m", name: "Bitcoin vs USD", decimals: 2 },
];

export const MOCK_PRICES = {
  "XAUUSD.m": { bid: 2375.42, ask: 2375.68, spread: 0.26, change: 1.23 },
  "EURUSD.m": { bid: 1.08742, ask: 1.08758, spread: 0.00016, change: -0.15 },
  "GBPUSD.m": { bid: 1.2712, ask: 1.27138, spread: 0.00018, change: 0.32 },
  "BTCUSD.m": { bid: 68450.2, ask: 68470.8, spread: 20.6, change: 2.45 },
};

export const MOCK_SIGNALS: Record<string, { signal: "BUY" | "SELL" | "WAIT"; confidence: number; entry: number; sl: number; tp: number; reason: string }> = {
  "XAUUSD.m": { signal: "BUY", confidence: 78, entry: 2375.50, sl: 2370.00, tp: 2385.00, reason: "EMA20 > EMA50, RSI bullish momentum" },
  "EURUSD.m": { signal: "SELL", confidence: 65, entry: 1.08750, sl: 1.08900, tp: 1.08500, reason: "EMA20 < EMA50, RSI below 50" },
  "GBPUSD.m": { signal: "BUY", confidence: 72, entry: 1.27130, sl: 1.26900, tp: 1.27500, reason: "EMA crossover bullish, RSI rising" },
  "BTCUSD.m": { signal: "WAIT", confidence: 45, entry: 68460.00, sl: 67800.00, tp: 69200.00, reason: "Mixed signals, consolidation phase" },
};

function generateCandles(basePrice: number, count: number, volatility: number) {
  const candles = [];
  let price = basePrice;
  const now = Date.now();
  for (let i = count; i > 0; i--) {
    const open = price;
    const change = (Math.random() - 0.48) * volatility;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * volatility * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * 0.5;
    candles.push({
      time: new Date(now - i * 5 * 60 * 1000).toISOString(),
      open: +open.toFixed(5),
      high: +high.toFixed(5),
      low: +low.toFixed(5),
      close: +close.toFixed(5),
      volume: Math.floor(Math.random() * 500 + 100),
    });
    price = close;
  }
  return candles;
}

export const MOCK_CANDLES: Record<string, ReturnType<typeof generateCandles>> = {
  "XAUUSD.m": generateCandles(2370, 50, 3),
  "EURUSD.m": generateCandles(1.086, 50, 0.001),
  "GBPUSD.m": generateCandles(1.27, 50, 0.0012),
  "BTCUSD.m": generateCandles(68000, 50, 200),
};

export const MOCK_SIGNAL_HISTORY = [
  { time: "2024-05-14 07:30", symbol: "XAUUSD.m", signal: "BUY" as const, entry: 2374.20, sl: 2369.00, tp: 2384.00, result: "TP Hit" as const, pl: "+9.80" },
  { time: "2024-05-14 07:15", symbol: "EURUSD.m", signal: "SELL" as const, entry: 1.08800, sl: 1.08950, tp: 1.08600, result: "TP Hit" as const, pl: "+20.0 pips" },
  { time: "2024-05-14 06:45", symbol: "GBPUSD.m", signal: "BUY" as const, entry: 1.27050, sl: 1.26850, tp: 1.27350, result: "Active" as const, pl: "+7.0 pips" },
  { time: "2024-05-14 06:30", symbol: "BTCUSD.m", signal: "SELL" as const, entry: 68600.00, sl: 69000.00, tp: 68000.00, result: "SL Hit" as const, pl: "-400.00" },
  { time: "2024-05-14 06:00", symbol: "XAUUSD.m", signal: "BUY" as const, entry: 2368.50, sl: 2363.00, tp: 2378.00, result: "TP Hit" as const, pl: "+9.50" },
  { time: "2024-05-14 05:30", symbol: "EURUSD.m", signal: "BUY" as const, entry: 1.08650, sl: 1.08500, tp: 1.08850, result: "TP Hit" as const, pl: "+20.0 pips" },
  { time: "2024-05-14 05:00", symbol: "GBPUSD.m", signal: "SELL" as const, entry: 1.27200, sl: 1.27400, tp: 1.26900, result: "SL Hit" as const, pl: "-20.0 pips" },
  { time: "2024-05-14 04:30", symbol: "BTCUSD.m", signal: "BUY" as const, entry: 67800.00, sl: 67200.00, tp: 68800.00, result: "TP Hit" as const, pl: "+1000.00" },
];
