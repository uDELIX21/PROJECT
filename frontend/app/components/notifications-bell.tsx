"use client";

/** In-app notification bell: unread count, dropdown list, mark-read. */
import React, { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

interface Notif { id: string; kind: string; title: string; body: string; read: boolean; created_at: string }

export function NotificationsBell() {
  const [items, setItems] = useState<Notif[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const load = async () => {
    try { setItems((await api("/communications/notifications")).items); } catch { /* silent */ }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 60000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const unread = items.filter((i) => !i.read).length;

  const markAll = async () => {
    const ids = items.filter((i) => !i.read).map((i) => i.id);
    if (ids.length === 0) return;
    try {
      await api("/communications/notifications/read", { method: "POST", body: ids });
      load();
    } catch { /* ignore */ }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="relative rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm hover:bg-slate-50"
        aria-label={`Notifications (${unread} unread)`}
      >
        🔔
        {unread > 0 && (
          <span className="absolute -top-1.5 -right-1.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-lg border border-slate-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2">
            <p className="text-xs font-semibold text-slate-600">Notifications</p>
            {unread > 0 && (
              <button className="text-xs text-brand-700 hover:underline" onClick={markAll}>
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-auto">
            {items.length === 0 ? (
              <p className="px-3 py-4 text-xs text-slate-400">No notifications.</p>
            ) : (
              items.map((n) => (
                <div key={n.id} className={`border-b border-slate-50 px-3 py-2 ${n.read ? "" : "bg-brand-50/40"}`}>
                  <p className="text-xs font-medium text-slate-700">{n.title}</p>
                  <p className="mt-0.5 text-xs text-slate-500 line-clamp-3">{n.body}</p>
                  <p className="mt-0.5 text-[10px] text-slate-400">
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
