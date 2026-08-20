"use client";

/** Fee structures & billing runs (amounts are school configuration, never code). */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel } from "../../components/ui";
import { api, ApiClientError } from "../../lib/api";
import { activeContext } from "../../lib/academics";

const fmt = (p: number) => `GH¢ ${(p / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
const FEE_TYPES = ["TUITION", "FEEDING", "ICT_LAB", "PTA_LEVY", "TRANSPORT", "EXAMINATION", "OTHER"];

export default function FeesPage() {
  const [ctx, setCtx] = useState<Awaited<ReturnType<typeof activeContext>> | null>(null);
  const [grades, setGrades] = useState<any[]>([]);
  const [structures, setStructures] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // new structure form
  const [gradeId, setGradeId] = useState("");
  const [name, setName] = useState("");
  const [items, setItems] = useState([{ fee_type: "TUITION", display_name: "Tuition", amount: "", period: "PER_TERM" }]);
  const [billingPreview, setBillingPreview] = useState<any[] | null>(null);
  const [busy, setBusy] = useState(false);

  const reload = async (yearId: string) => {
    try {
      setStructures((await api(`/fees/structures?academic_year_id=${yearId}`)).items);
    } catch (e) {
      if (e instanceof ApiClientError && e.status !== 403) setError(e.message);
    }
  };

  useEffect(() => {
    activeContext().then(async (c) => {
      setCtx(c);
      setGrades((await api("/classes/grades")).items);
      if (c.year) reload(c.year.id);
    }).catch((e) => setError(e.message));
  }, []);

  const create = async () => {
    if (!ctx?.year || !gradeId) return;
    setBusy(true); setError(null); setNotice(null);
    try {
      await api("/fees/structures", {
        method: "POST",
        body: {
          academic_year_id: ctx.year.id, name: name || "Fee structure", grade_id: gradeId,
          items: items.filter((i) => i.amount).map((i) => ({
            fee_type: i.fee_type, display_name: i.display_name || undefined,
            amount_pesewas: Math.round(parseFloat(i.amount) * 100), period: i.period,
          })),
        },
      });
      setNotice("Fee structure saved (configuration row — no code changes).");
      reload(ctx.year.id);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Failed.");
    } finally { setBusy(false); }
  };

  const preview = async () => {
    if (!ctx?.year || !ctx.term) return;
    setError(null);
    try {
      const r = await api("/fees/billing/preview", {
        method: "POST",
        body: { academic_year_id: ctx.year.id, term_id: ctx.term.id },
      });
      setBillingPreview(r.items);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Preview failed.");
    }
  };

  const applyBilling = async () => {
    if (!ctx?.year || !ctx.term) return;
    setBusy(true); setError(null);
    try {
      const r = await api("/fees/billing/apply", {
        method: "POST",
        body: { academic_year_id: ctx.year.id, term_id: ctx.term.id },
      });
      setNotice(`Billing applied: ${r.created} new charge(s), ${r.skipped_existing} already charged.`);
      setBillingPreview(null);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Billing failed.");
    } finally { setBusy(false); }
  };

  if (!ctx) return <Loading />;

  return (
    <>
      <PageHeader title="Fee structures"
        subtitle="Initial tuition values live here as configuration (spec §19) — edit freely per year/grade" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title={`Active structures — ${ctx.year?.name}`}>
          {structures.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">No structures yet for this year.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {structures.map((s) => (
                <div key={s.id} className="px-4 py-3">
                  <p className="text-sm font-medium">{s.name}
                    <span className="ml-2 text-xs text-slate-400">
                      {s.band ? s.band.replaceAll("_", " ") : "grade-scoped"}
                    </span>
                  </p>
                  <ul className="mt-1 text-xs text-slate-600 space-y-0.5">
                    {s.items.map((i: any, k: number) => (
                      <li key={k}>• {i.display_name}: {fmt(i.amount_pesewas)} / {i.period.replaceAll("_", " ").toLowerCase()}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="New structure">
          <div className="grid gap-3 px-4 py-3">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Grade">
                <select className="input" value={gradeId} onChange={(e) => setGradeId(e.target.value)}>
                  <option value="">Select…</option>
                  {grades.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
                </select>
              </Field>
              <Field label="Name">
                <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Basic 4 fees" />
              </Field>
            </div>
            {items.map((it, i) => (
              <div key={i} className="grid grid-cols-4 gap-2 items-end">
                <select className="input" value={it.fee_type}
                        onChange={(e) => setItems(items.map((x, j) => j === i ? { ...x, fee_type: e.target.value } : x))}>
                  {FEE_TYPES.map((t) => <option key={t}>{t}</option>)}
                </select>
                <input className="input col-span-1" type="number" min="0" step="0.01" placeholder="GHS"
                       value={it.amount}
                       onChange={(e) => setItems(items.map((x, j) => j === i ? { ...x, amount: e.target.value } : x))} />
                <select className="input" value={it.period}
                        onChange={(e) => setItems(items.map((x, j) => j === i ? { ...x, period: e.target.value } : x))}>
                  <option value="PER_TERM">per term</option>
                  <option value="PER_YEAR">per year</option>
                  <option value="ONE_OFF">one-off</option>
                </select>
                <button className="btn-secondary !py-2" onClick={() => setItems(items.filter((_, j) => j !== i))}>✕</button>
              </div>
            ))}
            <div className="flex gap-2">
              <button className="btn-secondary" onClick={() => setItems([...items, { fee_type: "OTHER", display_name: "", amount: "", period: "PER_TERM" }])}>+ item</button>
              <button className="btn-primary" onClick={create} disabled={busy || !gradeId}>Save structure</button>
            </div>
          </div>
        </Panel>
      </div>

      <div className="mt-4">
        <Panel title={`Billing run — ${ctx.term?.name}`} right={
          <div className="flex gap-2">
            <button className="btn-secondary !py-1.5" onClick={preview}>Preview</button>
            <button className="btn-primary !py-1.5" onClick={applyBilling} disabled={busy}>Apply</button>
          </div>
        }>
          {billingPreview === null ? (
            <p className="px-4 py-4 text-sm text-slate-500">
              Preview which charges will be raised before applying. Applying is idempotent — existing charges are never duplicated.
            </p>
          ) : (
            <p className="px-4 py-3 text-sm">
              {billingPreview.length} student(s) eligible · {billingPreview.reduce((n, s) => n + s.charges.length, 0)} charge line(s)
            </p>
          )}
        </Panel>
      </div>
    </>
  );
}
