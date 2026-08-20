"use client";

/** Bursar workspace: collect payments, view balances & receipts, clearance states. */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel, Badge, ConfirmDialog } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { activeContext } from "../lib/academics";

interface PaymentRow { id: string; student_id: string; status: string; method: string; amount_pesewas: number; receipt_id: string | null }

const fmt = (p: number) => `GH¢ ${(p / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

export default function FinancePage() {
  const [ctx, setCtx] = useState<Awaited<ReturnType<typeof activeContext>> | null>(null);
  const [payments, setPayments] = useState<PaymentRow[]>([]);
  const [clearances, setClearances] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // payment form
  const [studentQ, setStudentQ] = useState("");
  const [students, setStudents] = useState<any[]>([]);
  const [studentId, setStudentId] = useState("");
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("CASH");
  const [balance, setBalance] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [override, setOverride] = useState<any | null>(null);
  const [overrideReason, setOverrideReason] = useState("");

  useEffect(() => {
    activeContext().then(setCtx).catch((e) => setError(e.message));
  }, []);

  const reload = async (termId: string) => {
    try {
      const p = await api(`/payments?limit=15`);
      setPayments(p.items);
      const c = await api(`/fees/clearance?term_id=${termId}`);
      setClearances(c.items);
    } catch (e) {
      if (e instanceof ApiClientError && e.status !== 403) setError(e.message);
    }
  };

  useEffect(() => {
    if (ctx?.term) reload(ctx.term.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ctx?.term]);

  useEffect(() => {
    if (!studentQ || studentQ.length < 2) { setStudents([]); return; }
    api(`/students?q=${encodeURIComponent(studentQ)}&limit=8`)
      .then((r) => setStudents(r.items)).catch(() => {});
  }, [studentQ]);

  useEffect(() => {
    if (!studentId) { setBalance(null); return; }
    api(`/fees/balances?student_id=${studentId}`)
      .then((r) => setBalance(r.balance_pesewas)).catch(() => setBalance(null));
  }, [studentId]);

  const collect = async () => {
    if (!studentId || !amount || !ctx?.term) return;
    setBusy(true); setError(null); setNotice(null);
    try {
      const pesewas = Math.round(parseFloat(amount) * 100);
      const res = await api("/payments/initiate", {
        method: "POST",
        body: { student_id: studentId, amount_pesewas: pesewas, method, term_id: ctx.term.id },
      });
      if (res.status === "CONFIRMED") {
        setNotice(`Payment confirmed — receipt issued${res.receipt_id ? " (see receipts below)" : ""}.`);
      } else {
        setNotice(`Payment ${res.status.toLowerCase()} — provider ref ${res.provider_reference}. Confirm via webhook simulation.`);
      }
      setAmount(""); setStudentId(""); setStudentQ("");
      reload(ctx.term.id);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Payment failed.");
    } finally { setBusy(false); }
  };

  const confirmOverride = async () => {
    if (!override || !ctx?.term) return;
    setBusy(true); setError(null);
    try {
      await api("/fees/clearance/override", {
        method: "POST",
        body: { student_id: override.student_id, term_id: ctx.term.id,
                clearance_type: "REPORT_CARD", state: "WAIVED", reason: overrideReason },
      });
      setNotice("Clearance waived (audited).");
      setOverride(null); setOverrideReason("");
      reload(ctx.term.id);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Override failed.");
    } finally { setBusy(false); }
  };

  if (!ctx) return <Loading />;

  return (
    <>
      <PageHeader title="Finance" subtitle={`${ctx.year?.name} · ${ctx.term?.name} — ledger-derived balances, receipts & clearance`} />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Record payment">
          <div className="grid gap-3 px-4 py-3">
            <Field label="Find student">
              <input className="input" placeholder="Search name or code…" value={studentQ}
                     onChange={(e) => { setStudentQ(e.target.value); setStudentId(""); }} />
            </Field>
            {students.length > 0 && !studentId && (
              <ul className="border border-slate-200 rounded-md divide-y divide-slate-100 text-sm max-h-44 overflow-auto">
                {students.map((s) => (
                  <li key={s.id}>
                    <button className="w-full text-left px-3 py-1.5 hover:bg-slate-50"
                            onClick={() => { setStudentId(s.id); setStudentQ(s.full_name); }}>
                      {s.full_name} <span className="text-xs text-slate-400">({s.admission_code})</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {studentId && balance !== null && (
              <p className="text-sm text-slate-600">
                Current balance: <strong className={balance > 0 ? "text-red-600" : "text-emerald-600"}>{fmt(balance)}</strong>
              </p>
            )}
            <div className="grid grid-cols-2 gap-3">
              <Field label="Amount (GHS)">
                <input className="input" type="number" min="0" step="0.01" value={amount}
                       onChange={(e) => setAmount(e.target.value)} placeholder="e.g. 500.00" />
              </Field>
              <Field label="Method">
                <select className="input" value={method} onChange={(e) => setMethod(e.target.value)}>
                  <option value="CASH">Cash</option>
                  <option value="MTN_MOMO">MTN MoMo (simulated)</option>
                  <option value="TELECEL_CASH">Telecel Cash (simulated)</option>
                  <option value="AT_MONEY">AT Money (simulated)</option>
                </select>
              </Field>
            </div>
            <button className="btn-primary" onClick={collect} disabled={busy || !studentId || !amount}>
              {busy ? "Processing…" : method === "CASH" ? "Collect cash & issue receipt" : "Initiate payment"}
            </button>
          </div>
        </Panel>

        <Panel title="Recent payments">
          {payments.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">No payments recorded yet.</p>
          ) : (
            <table className="tbl">
              <thead><tr><th>Status</th><th>Method</th><th>Amount</th><th>Receipt</th></tr></thead>
              <tbody>
                {payments.map((p) => (
                  <tr key={p.id}>
                    <td><Badge value={p.status} /></td>
                    <td>{p.method.replaceAll("_", " ")}</td>
                    <td>{fmt(p.amount_pesewas)}</td>
                    <td>
                      {p.receipt_id ? (
                        <a className="text-brand-700 hover:underline text-xs"
                           href={`/api/v1/receipts/${p.receipt_id}/pdf`} target="_blank">PDF</a>
                      ) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      </div>

      <div className="mt-4">
        <Panel title={`Financial clearance — ${ctx.term?.name} (report card gate)`}>
          {clearances.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">
              No clearance rows yet — states materialize when evaluated (e.g. at report publication).
            </p>
          ) : (
            <>
              <table className="tbl">
                <thead><tr><th>Student</th><th>Charged</th><th>Paid</th><th>State</th><th></th></tr></thead>
                <tbody>
                  {clearances.slice(0, 40).map((c) => (
                    <tr key={c.student_id}>
                      <td className="font-mono text-xs">{c.student_id.slice(0, 8)}…</td>
                      <td>{fmt(c.charged_pesewas)}</td>
                      <td>{fmt(c.paid_pesewas)}</td>
                      <td><Badge value={c.state} /></td>
                      <td className="text-right">
                        {c.state === "BLOCKED" && (
                          <button className="btn-secondary !py-1" onClick={() => setOverride(c)}>Waive…</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {clearances.length > 40 && (
                <p className="px-4 py-2 text-xs text-slate-400 border-t border-slate-100">
                  Showing 40 of {clearances.length}
                </p>
              )}
            </>
          )}
        </Panel>
      </div>

      <ConfirmDialog open={!!override} title="Waive financial clearance"
        body="This override is audited with your account and reason. The report card gate will treat this student as WAIVED."
        confirmLabel="Waive (audited)" danger
        onConfirm={confirmOverride} onCancel={() => { setOverride(null); setOverrideReason(""); }} />
      {override && (
        <div className="fixed inset-0 z-40" onClick={() => setOverride(null)} />
      )}
      {override && (
        <div className="fixed z-50 bottom-4 left-1/2 -translate-x-1/2 bg-white border border-slate-200 rounded-lg shadow-lg p-4 w-96">
          <Field label="Reason (required, audited)">
            <input className="input" value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} />
          </Field>
        </div>
      )}
    </>
  );
}
