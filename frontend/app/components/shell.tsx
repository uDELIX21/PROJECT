/** App shell: responsive sidebar (desktop) / topbar (mobile), session-aware nav. */
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import { api, isAuthError, setCsrf } from "../lib/api";
import { hasPerm, useSession } from "../lib/session";
import { NotificationsBell } from "./notifications-bell";
import { SyncBadge } from "./sync-badge";
import { startSyncEngine } from "../lib/offline/sync";

const NAV: { href: string; label: string; perm?: string }[] = [
  { href: "/", label: "Dashboard" },
  { href: "/students", label: "Students", perm: "VIEW_STUDENT" },
  { href: "/admissions", label: "New admission", perm: "EDIT_STUDENT" },
  { href: "/classes", label: "Classes", perm: "VIEW_STUDENT" },
  { href: "/marks", label: "Marks entry", perm: "ENTER_MARKS" },
  { href: "/attendance", label: "Attendance", perm: "ENTER_MARKS" },
  { href: "/results", label: "Results", perm: "VIEW_REPORT" },
  { href: "/ecd", label: "Early childhood", perm: "VIEW_STUDENT" },
  { href: "/reports", label: "Report cards", perm: "VIEW_REPORT" },
  { href: "/finance", label: "Finance", perm: "VIEW_FINANCE" },
  { href: "/finance/fees", label: "Fee structures", perm: "MANAGE_FEES" },
  { href: "/appraisals", label: "Appraisals", perm: "VIEW_TEACHER" },
  { href: "/discipline", label: "Discipline", perm: "VIEW_DISCIPLINE" },
  { href: "/pickup", label: "Pickup", perm: "VIEW_STUDENT" },
  { href: "/communications", label: "Communications", perm: "SEND_COMMUNICATION" },
  { href: "/imports", label: "Imports", perm: "IMPORT_DATA" },
  { href: "/users", label: "Users", perm: "MANAGE_USERS" },
  { href: "/settings", label: "Settings", perm: "MANAGE_SETTINGS" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { me, loading } = useSession();
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  // offline sync engine (IndexedDB outbox + flush on reconnect)
  useEffect(() => { startSyncEngine(); }, []);

  // redirect unauthenticated visitors to /login (effect, not render side-effect)
  React.useEffect(() => {
    if (!loading && !me && pathname !== "/login") router.replace("/login");
  }, [loading, me, pathname, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-slate-500">
        Loading…
      </div>
    );
  }

  if (!me) {
    if (pathname !== "/login") return null; // redirect in flight
    return <main className="min-h-screen">{children}</main>;
  }

  const items = NAV.filter((n) => !n.perm || hasPerm(me, n.perm));

  const logout = async () => {
    try {
      await api("/auth/logout", { method: "POST" });
    } catch (e) {
      if (!isAuthError(e)) console.error(e);
    }
    setCsrf(null);
    router.replace("/login");
  };

  return (
    <div className="min-h-screen flex">
      {/* sidebar (md+) */}
      <aside className="hidden md:flex md:w-56 md:flex-col border-r border-slate-200 bg-white">
        <div className="px-4 py-4 border-b border-slate-200">
          <p className="text-sm font-bold text-brand-800 leading-tight">{me.school.name}</p>
          {me.school.motto && <p className="text-[11px] text-slate-400 mt-0.5">{me.school.motto}</p>}
        </div>
        <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-auto">
          {items.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={`block rounded-md px-3 py-2 text-sm ${
                pathname === n.href
                  ? "bg-brand-50 text-brand-800 font-medium"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="px-4 py-3 border-t border-slate-200 text-xs text-slate-500">
          <div className="mb-2"><SyncBadge /></div>
          <p className="font-medium text-slate-700">{me.user.display_name ?? me.user.username}</p>
          <p className="mt-0.5">{me.roles.join(", ")}</p>
          {me.active_year && (
            <p className="mt-1">
              {me.active_year.name}
              {me.active_term ? ` · ${me.active_term.name}` : ""}
            </p>
          )}
          <button onClick={logout} className="mt-2 text-brand-700 hover:underline">
            Log out
          </button>
        </div>
      </aside>

      {/* main column */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* mobile topbar */}
        <header className="md:hidden sticky top-0 z-40 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
          <p className="text-sm font-bold text-brand-800 truncate">{me.school.name}</p>
          <div className="flex items-center gap-2">
            <SyncBadge />
            <NotificationsBell />
            <button
              className="btn-secondary !py-1.5"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-expanded={menuOpen}
            >
              Menu
            </button>
          </div>
        </header>
        {/* desktop topbar */}
        <header className="hidden md:flex sticky top-0 z-40 items-center justify-end gap-3 border-b border-slate-200 bg-white px-6 py-2">
          <NotificationsBell />
        </header>
        {menuOpen && (
          <nav className="md:hidden border-b border-slate-200 bg-white px-2 py-2 space-y-0.5">
            {items.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                onClick={() => setMenuOpen(false)}
                className="block rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                {n.label}
              </Link>
            ))}
            <button
              onClick={logout}
              className="block w-full text-left rounded-md px-3 py-2 text-sm text-brand-700"
            >
              Log out
            </button>
          </nav>
        )}
        <main className="flex-1 px-4 md:px-6 py-5 max-w-6xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
