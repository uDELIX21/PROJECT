"use client";

/** Global offline/sync indicator: synced / pending / failed / conflict (REQ-OFF-02). */
import React, { useEffect, useState } from "react";
import { subscribeSync, flush, retryFailed } from "../lib/offline/sync";
import type { QueueSummary } from "../lib/offline/engine";

export function SyncBadge() {
  const [summary, setSummary] = useState<QueueSummary>({ pending: 0, synced: 0, failed: 0, conflict: 0 });
  const [online, setOnline] = useState(true);

  useEffect(() => subscribeSync((_items, s, on) => { setSummary(s); setOnline(on); }), []);

  const dirty = summary.pending + summary.failed + summary.conflict;

  return (
    <div className="flex items-center gap-2 text-xs">
      <span
        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-medium ${
          !online
            ? "bg-slate-200 text-slate-600"
            : dirty > 0
            ? "bg-amber-50 text-amber-700"
            : "bg-emerald-50 text-emerald-700"
        }`}
        title={!online ? "Offline — entries are stored locally and will sync when back online"
              : dirty > 0 ? "Some entries are waiting to sync" : "All changes synced"}
      >
        <span className={`h-1.5 w-1.5 rounded-full ${!online ? "bg-slate-500" : dirty > 0 ? "bg-amber-500" : "bg-emerald-500"}`} />
        {!online ? "Offline" : summary.pending > 0 ? `Syncing ${summary.pending}…`
          : summary.conflict > 0 ? `${summary.conflict} conflict(s)`
          : summary.failed > 0 ? `${summary.failed} failed` : "Synced"}
      </span>
      {(summary.failed > 0 || summary.pending > 0) && online && (
        <button
          className="text-brand-700 hover:underline"
          onClick={() => { void retryFailed(); void flush(); }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
