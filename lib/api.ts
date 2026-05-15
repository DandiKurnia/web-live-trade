const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export async function fetchPrice(symbol: string) {
  const res = await fetch(`${API_BASE}/api/price/${symbol}`);
  if (!res.ok) throw new Error(`Failed to fetch price for ${symbol}`);
  return res.json();
}

export async function fetchSymbols() {
  const res = await fetch(`${API_BASE}/api/symbols`);
  if (!res.ok) throw new Error("Failed to fetch symbols");
  return res.json();
}

export async function fetchCandles(symbol: string, timeframe = "M1", limit = 100) {
  const res = await fetch(`${API_BASE}/api/candles/${symbol}?timeframe=${timeframe}&limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch candles for ${symbol}`);
  return res.json();
}

export async function fetchSignal(symbol: string) {
  const res = await fetch(`${API_BASE}/api/signals/${symbol}`);
  if (!res.ok) throw new Error(`Failed to fetch signal for ${symbol}`);
  return res.json();
}

export async function fetchAnalysis(symbol: string) {
  const res = await fetch(`${API_BASE}/api/analysis/${symbol}`);
  if (!res.ok) throw new Error(`Failed to fetch analysis for ${symbol}`);
  return res.json();
}

export async function fetchTradePlan(symbol: string) {
  const res = await fetch(`${API_BASE}/api/trade-plans/${symbol}`);
  if (!res.ok) throw new Error(`Failed to fetch trade plan for ${symbol}`);
  return res.json();
}

export async function approveTradePlan(planId: number) {
  const res = await fetch(`${API_BASE}/api/trade-plans/${planId}/approve`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to approve trade plan");
  return res.json();
}

export async function rejectTradePlan(planId: number) {
  const res = await fetch(`${API_BASE}/api/trade-plans/${planId}/reject`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to reject trade plan");
  return res.json();
}

export async function fetchAISummary(symbol: string) {
  const res = await fetch(`${API_BASE}/api/ai/summary/${symbol}`);
  if (!res.ok) throw new Error(`Failed to fetch AI summary for ${symbol}`);
  return res.json();
}

export async function triggerAIAnalysis(symbol: string) {
  const res = await fetch(`${API_BASE}/api/ai/analyze/${symbol}`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to trigger AI analysis for ${symbol}`);
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Failed to fetch health");
  return res.json();
}

export function getWsUrl() {
  return `${WS_BASE}/ws/market`;
}

export function getSignalWsUrl() {
  return `${WS_BASE}/ws/signals`;
}

export async function fetchTradeHistory(limit = 20) {
  const res = await fetch(`${API_BASE}/api/trade-history?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch trade history");
  return res.json();
}

export async function fetchSignalHistory(limit = 30) {
  const res = await fetch(`${API_BASE}/api/signal-history?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch signal history");
  return res.json();
}

export async function fetchActiveAlerts() {
  const res = await fetch(`${API_BASE}/api/ai/active-alerts`);
  if (!res.ok) throw new Error("Failed to fetch active alerts");
  return res.json();
}
