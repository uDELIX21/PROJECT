"use client";

/** Communications: broadcast composer, SMS log, template editor (provider-swappable). */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel, Badge } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { activeContext, streamsFor } from "../lib/academics";

const EVENTS = ["ANNOUNCEMENT", "EMERGENCY_BROADCAST", "FEE_REMINDER", "REPORT_AVAILABLE"];
const AUDIENCES = [
  ["school", "Whole school"], ["ecd", "Early childhood"], ["primary", "Primary"],
  ["jhs", "Junior High"], ["class", "One class"], ["debtors", "Fee debtors"],
];

export default function CommunicationsPage() {
  const [ctx, setCtx] = useState<Awaited<ReturnType<typeof activeContext>> | null>(null);
  const [streams, setStreams] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [log, setLog] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [form, setForm] = useState({ event_code: "ANNOUNCEMENT", audience: "school",
    class_stream_id: "", message: "" });

  const reload = async () => {
    try {
      setTemplates((await api("/communications/templates")).items);
      setLog((await api("/communications/sms-log?limit=30")).items);
    } catch (e) {
      if (e instanceof ApiClientError && e.status !== 403) setError(e.message);
    }
  };

  useEffect(() => {
    activeContext().then(async (c) => {
      setCtx(c);
      if (c.year) setStreams(await streamsFor(c.year.id));
      reload();
    }).catch((e: any) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const send = async () => {
    setError(null); setNotice(null);
    try {
      const r = await api("/communications/broadcast", {
        method: "POST",
        body: {
          event_code: form.event_code, audience: form.audience,
          message: form.message || undefined,
          class_stream_id: form.audience === "class" ? form.class_stream_id : undefined,
        },
      });
      setNotice(`Broadcast complete: ${r.sent} SMS sent, ${r.skipped} skipped, ${r.recipients} guardian(s) reached.`);
      setForm({ ...form, message: "" });
      reload();
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Broadcast failed.");
    }
  };

  if (!ctx) return <Loading />;

  return (
    <>
      <PageHeader title="Communications"
        subtitle="SMS via provider abstraction (console stub in demo — Arkesel/Hubtel adapters available) + in-app notices" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Compose broadcast">
          <div className="grid gap-3 px-4 py-3">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Event">
                <select className="input" value={form.event_code}
                  onChange={(e) => setForm({ ...form, event_code: e.target.value })}>
                  {EVENTS.map((e) => <option key={e}>{e}</option>)}
                </select>
              </Field>
              <Field label="Audience">
                <select className="input" value={form.audience}
                  onChange={(e) => setForm({ ...form, audience: e.target.value })}>
                  {AUDIENCES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </Field>
            </div>
            {form.audience === "class" && (
              <Field label="Class">
                <select className="input" value={form.class_stream_id}
                  onChange={(e) => setForm({ ...form, class_stream_id: e.target.value })}>
                  <option value="">Select…</option>
                  {streams.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </Field>
            )}
            <Field label="Message" hint="Merged into the event template ({{message}}). Opt-outs are respected.">
              <textarea className="input" rows={3} value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })} />
            </Field>
            <button className="btn-primary" onClick={send}>Send broadcast</button>
          </div>
        </Panel>

        <Panel title="SMS templates">
          <div className="divide-y divide-slate-100 max-h-80 overflow-auto">
            {templates.filter((t) => t.channel === "SMS").map((t) => (
              <details key={t.id} className="px-4 py-2">
                <summary className="text-sm font-medium cursor-pointer">
                  {t.event_code} {!t.is_active && <span className="text-xs text-red-500">(inactive)</span>}
                </summary>
                <pre className="mt-1 text-xs text-slate-500 whitespace-pre-wrap">{t.template}</pre>
              </details>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4">
        <Panel title="SMS log">
          {log.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">No messages yet.</p>
          ) : (
            <table className="tbl">
              <thead><tr><th>Phone</th><th>Event</th><th>Provider</th><th>Status</th><th>Preview</th></tr></thead>
              <tbody>
                {log.map((m) => (
                  <tr key={m.id}>
                    <td className="font-mono text-xs whitespace-nowrap">{m.recipient_phone}</td>
                    <td className="text-xs">{m.event_code ?? "—"}</td>
                    <td className="text-xs">{m.provider_code}</td>
                    <td><span className={`text-xs font-medium ${m.status === "FAILED" ? "text-red-600" : m.status === "SKIPPED" ? "text-amber-600" : "text-emerald-700"}`}>{m.status}</span></td>
                    <td className="text-xs max-w-sm truncate">{m.body_preview}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      </div>
    </>
  );
}
