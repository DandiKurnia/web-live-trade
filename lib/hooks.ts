"use client";

import { useEffect, useRef, useState } from "react";
import { getWsUrl, fetchPrice } from "./api";
import { TickData } from "./types";

export function useMarketSocket(symbols: string[]) {
  const [prices, setPrices] = useState<Record<string, TickData>>({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollingTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const symbolsRef = useRef(symbols);
  symbolsRef.current = symbols;

  useEffect(() => {
    let disposed = false;

    function startPolling() {
      if (pollingTimer.current) return;
      pollingTimer.current = setInterval(async () => {
        for (const symbol of symbolsRef.current) {
          try {
            const data = await fetchPrice(symbol);
            if (data.success) {
              setPrices((prev) => ({
                ...prev,
                [symbol]: {
                  symbol,
                  bid: data.bid,
                  ask: data.ask,
                  spread: data.spread,
                  time: data.time,
                },
              }));
            }
          } catch {}
        }
      }, 3000);
    }

    function stopPolling() {
      if (pollingTimer.current) {
        clearInterval(pollingTimer.current);
        pollingTimer.current = null;
      }
    }

    function connectWs() {
      if (disposed) return;
      const ws = new WebSocket(getWsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        stopPolling();
        ws.send(JSON.stringify({ action: "subscribe", symbols: symbolsRef.current }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data) as TickData;
        setPrices((prev) => ({ ...prev, [data.symbol]: data }));
      };

      ws.onclose = () => {
        setConnected(false);
        if (!disposed) {
          startPolling();
          reconnectTimer.current = setTimeout(connectWs, 5000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connectWs();

    return () => {
      disposed = true;
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      stopPolling();
    };
  }, []);

  return { prices, connected };
}
