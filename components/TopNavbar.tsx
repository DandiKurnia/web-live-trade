"use client";

import { Search, Wifi, WifiOff, User } from "lucide-react";

interface TopNavbarProps {
  connected: boolean;
}

export function TopNavbar({ connected }: TopNavbarProps) {
  return (
    <header className="h-14 border-b border-[var(--border)] bg-[var(--card)] flex items-center px-4 gap-4 sticky top-0 z-10">
      <div className="flex items-center gap-2 flex-1">
        <Search size={16} className="text-neutral-500" />
        <input
          type="text"
          placeholder="Search symbol..."
          className="bg-transparent text-sm text-white placeholder-neutral-500 outline-none w-full max-w-xs"
        />
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          {connected ? (
            <Wifi size={14} className="text-green-400" />
          ) : (
            <WifiOff size={14} className="text-red-400" />
          )}
          <span className="text-xs text-neutral-400">
            {connected ? "Live" : "Offline"}
          </span>
        </div>

        <div className="w-8 h-8 rounded-full bg-[var(--border)] flex items-center justify-center">
          <User size={14} className="text-neutral-400" />
        </div>
      </div>
    </header>
  );
}
