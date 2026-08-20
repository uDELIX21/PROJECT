/** Small table-first UI kit (REQ-UI-01): no decorative card overload. */
"use client";

import React from "react";

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Panel({
  title,
  children,
  right,
}: {
  title?: string;
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <section className="bg-white border border-slate-200 rounded-lg shadow-sm">
      {(title || right) && (
        <header className="flex items-center justify-between px-4 py-2.5 border-b border-slate-200">
          {title && <h2 className="text-sm font-semibold text-slate-700">{title}</h2>}
          {right}
        </header>
      )}
      {children}
    </section>
  );
}

const badgeTones: Record<string, string> = {
  ACTIVE: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  ADMITTED: "bg-sky-50 text-sky-700 ring-sky-600/20",
  APPLICANT: "bg-slate-100 text-slate-600 ring-slate-500/20",
  ENROLLED: "bg-teal-50 text-teal-700 ring-teal-600/20",
  PROMOTED: "bg-indigo-50 text-indigo-700 ring-indigo-600/20",
  REPEATED: "bg-amber-50 text-amber-800 ring-amber-600/20",
  WITHDRAWN: "bg-red-50 text-red-700 ring-red-600/20",
  TRANSFERRED: "bg-orange-50 text-orange-700 ring-orange-600/20",
  GRADUATED: "bg-violet-50 text-violet-700 ring-violet-600/20",
  SUSPENDED: "bg-rose-50 text-rose-700 ring-rose-600/20",
  CLOSED: "bg-slate-100 text-slate-600 ring-slate-500/20",
  DRAFT: "bg-slate-100 text-slate-600 ring-slate-500/20",
  ARCHIVED: "bg-slate-100 text-slate-500 ring-slate-400/20",
  CLEAR: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  BLOCKED: "bg-red-50 text-red-700 ring-red-600/20",
};

export function Badge({ value }: { value: string }) {
  const tone = badgeTones[value] ?? "bg-slate-100 text-slate-600 ring-slate-500/20";
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${tone}`}
    >
      {value.replaceAll("_", " ")}
    </span>
  );
}

export function ErrorBanner({ message, onClose }: { message: string; onClose?: () => void }) {
  return (
    <div
      role="alert"
      className="mb-4 flex items-start justify-between gap-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <span>{message}</span>
      {onClose && (
        <button onClick={onClose} className="text-red-500 hover:text-red-700" aria-label="Dismiss">
          ✕
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="px-4 py-10 text-center">
      <p className="text-sm font-medium text-slate-600">{title}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-8 justify-center text-sm text-slate-500">
      <span
        className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-700"
        aria-hidden
      />
      {label}
    </div>
  );
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel = "Confirm",
  danger,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  body: string;
  confirmLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl" role="dialog" aria-modal>
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        <p className="mt-2 text-sm text-slate-600">{body}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className={danger ? "btn-danger" : "btn-primary"} onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
