"use client";

/** Discipline: sensitive records — staff manage, parents see resolved summaries only. */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel, Badge } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { useSession } from "../lib/session";

const CATEGORIES = ["DISRUPTION", "BULLYING", "FIGHTING", "TRUANCY", "DAMAGE_TO_PROPERTY",
  "DISRESPECT", "UNIFORM_VIOLATION", "ACADEMIC_DISHONESTY", "OTHER"];

export default function DisciplinePage() {
  const { me } = useSession();
  const [rows, setRows] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [studentQ, setStudentQ] = useState("");
  const [students, setStudents] = useState<any[]>([]);
  const [form, setForm] = useState({ student_id: "", category: "DISRUPTION", description: "", severity: "MINOR" });

  const reload = async () => {
    try { setRows((await api("/discipline")).items); }
    catch (e) { if (e instanceof ApiClientError) setError(e.message); }
  };

  useEffect(() => { if (me) reload(); /* eslint-disable-line */ }, [me]);

  useEffect(() => {
    if (studentQ.length < 2) { setStudents([]); return; }
    api(`/students?q=${encodeURIComponent(studentQ)}&limit=6`).then((r) => setStudents(r.items)).catch(() => {});
  }, [studentQ]);

  const create = async () => {
    if (!form.student_id || form.description.length < 5) return;
    setError(null); setNotice(null);
    try {
      await api("/discipline", { method: "POST", body: form });
      setNotice("Incident recorded (audited).");
      setForm({ student_id: "", category: "DISRUPTION", description: "", severity: "MINOR" });
      setStudentQ("");
      reload();
    } catch (e) { setError(e instanceof ApiClientError ? e.message : "Failed."); }
  };

  const resolve = async (id: string) => {
    const resolution = window.prompt("Resolution note (required, audited):");
    if (!resolution || resolution.trim().length < 5) return;
    setError(null);
    try {
      await api(`/discipline/${id}`, { method: "PATCH", body: { status: "RESOLVED", resolution: resolution.trim() } });
      setNotice("Incident resolved.");
      reload();
    } catch (e) { setError(e instanceof ApiClientError ? e.message : "Failed."); }
  };

  const notifyParent = async (id: string) => {
    setError(null);
    try {
      const r = await api(`/discipline/${id}/notify-parent`, { method: "POST" });
      setNotice(`Guardians notified (${r.notified}).`);
    } catch (e) { setError(e instanceof ApiClientError ? e.message : "Failed."); }
  };

  if (!me) return <Loading />;

  return (
    <>
      <PageHeader title="Discipline" subtitle="Restricted records — access is logged" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}

      <Panel title="Record incident">
        <div className="grid gap-3 px-4 py-3 lg:grid-cols-2">
          <div>
            <Field label="Find student">
              <input className="input" value={studentQ} placeholder="Search name or code…"
                onChange={(e) => { setStudentQ(e.target.value); setForm({ ...form, student_id: "" }); }} />
            </Field>
            {students.length > 0 && !form.student_id && (
              <ul className="mt-1 border border-slate-200 rounded-md divide-y divide-slate-100 text-sm max-h-36 overflow-auto">
                {students.map((s) => (
                  <li key={s.id}>
                    <button className="w-full text-left px-3 py-1.5 hover:bg-slate-50"
                      onClick={() => { setForm({ ...form, student_id: s.id }); setStudentQ(s.full_name); }}>
                      {s.full_name} <span className="text-xs text-slate-400">({s.admission_code})</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Category">
              <select className="input" value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </Field>
            <Field label="Severity">
              <select className="input" value={form.severity}
                onChange={(e) => setForm({ ...form, severity: e.target.value })}>
                <option>MINOR</option><option>MODERATE</option><option>SERIOUS</option>
              </select>
            </Field>
          </div>
          <div className="lg:col-span-2">
            <Field label="Description">
              <textarea className="input" rows={2} value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </Field>
          </div>
          <div>
            <button className="btn-primary" onClick={create}
              disabled={!form.student_id || form.description.length < 5}>Record incident</button>
          </div>
        </div>
      </Panel>

      <div className="mt-4">
        <Panel title="Incidents">
          {rows.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">No incidents visible to your role.</p>
          ) : (
            <table className="tbl">
              <thead><tr><th>Date</th><th>Category</th><th>Severity</th><th>Status</th><th>Detail</th><th></th></tr></thead>
              <tbody>
                {rows.map((i) => (
                  <tr key={i.id}>
                    <td className="text-xs text-slate-500 whitespace-nowrap">{i.incident_at?.slice(0, 10)}</td>
                    <td>{i.category?.replaceAll("_", " ")}</td>
                    <td><Badge value={i.severity} /></td>
                    <td><Badge value={i.status} /></td>
                    <td className="text-xs max-w-md truncate">{i.description ?? "(summary hidden)"}</td>
                    <td className="space-x-1 whitespace-nowrap text-right">
                      {i.status !== "RESOLVED" && (
                        <button className="btn-secondary !py-1" onClick={() => resolve(i.id)}>Resolve…</button>
                      )}
                      {!i.parent_notified_at && i.status !== "RESOLVED" && (
                        <button className="btn-secondary !py-1" onClick={() => notifyParent(i.id)}>Notify parent</button>
                      )}
                    </td>
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
