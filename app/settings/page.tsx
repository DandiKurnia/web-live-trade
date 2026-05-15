"use client";

import { useState } from "react";
import { DashboardShell } from "@/components/DashboardShell";
import { clsx } from "clsx";

export default function SettingsPage() {
  const [symbols, setSymbols] = useState("XAUUSD.m, EURUSD.m, GBPUSD.m, BTCUSD.m");
  const [timeframe, setTimeframe] = useState("M5");
  const [risk, setRisk] = useState("2");
  const [telegram, setTelegram] = useState(false);
  const [sound, setSound] = useState(true);
  const [theme, setTheme] = useState("dark");

  return (
    <DashboardShell connected={false}>
      <div className="space-y-6 max-w-2xl">
        <div>
          <h1 className="text-xl font-bold text-white">Settings</h1>
          <p className="text-sm text-neutral-500 mt-0.5">
            Configure your dashboard preferences
          </p>
        </div>

        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">
              Symbols to Monitor
            </label>
            <input
              type="text"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[var(--background)] border border-[var(--border)] text-sm text-white placeholder-neutral-500 outline-none focus:border-blue-500 transition-colors"
            />
            <p className="text-xs text-neutral-500 mt-1">Comma-separated symbol list</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">
              Default Timeframe
            </label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[var(--background)] border border-[var(--border)] text-sm text-white outline-none focus:border-blue-500 transition-colors"
            >
              <option value="M1">M1</option>
              <option value="M5">M5</option>
              <option value="M15">M15</option>
              <option value="H1">H1</option>
              <option value="H4">H4</option>
              <option value="D1">D1</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">
              Risk Percentage (%)
            </label>
            <input
              type="number"
              value={risk}
              onChange={(e) => setRisk(e.target.value)}
              min="0.5"
              max="10"
              step="0.5"
              className="w-full px-3 py-2 rounded-lg bg-[var(--background)] border border-[var(--border)] text-sm text-white outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-300">Telegram Notifications</p>
              <p className="text-xs text-neutral-500">Get signal alerts via Telegram</p>
            </div>
            <button
              onClick={() => setTelegram(!telegram)}
              className={clsx(
                "w-11 h-6 rounded-full transition-colors relative",
                telegram ? "bg-blue-500" : "bg-neutral-700"
              )}
            >
              <span
                className={clsx(
                  "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                  telegram ? "translate-x-6" : "translate-x-1"
                )}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-300">Sound Alerts</p>
              <p className="text-xs text-neutral-500">Play sound on new signals</p>
            </div>
            <button
              onClick={() => setSound(!sound)}
              className={clsx(
                "w-11 h-6 rounded-full transition-colors relative",
                sound ? "bg-blue-500" : "bg-neutral-700"
              )}
            >
              <span
                className={clsx(
                  "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                  sound ? "translate-x-6" : "translate-x-1"
                )}
              />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">
              Theme
            </label>
            <div className="flex gap-2">
              {["dark", "light", "system"].map((t) => (
                <button
                  key={t}
                  onClick={() => setTheme(t)}
                  className={clsx(
                    "px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize",
                    theme === t
                      ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                      : "bg-[var(--background)] border border-[var(--border)] text-neutral-400 hover:text-white"
                  )}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button className="px-6 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium transition-colors">
            Save Settings
          </button>
        </div>
      </div>
    </DashboardShell>
  );
}
