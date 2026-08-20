"use client";

/** Teacher appraisals: evaluator flow (create → score → submit) and teacher
    acknowledgement. Confidential: drafts hidden, colleagues blocked. */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel, Badge } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { hasPerm, useSession } from "../lib/session";

export default function AppraisalsPage() {
  const { me } = useSession();
  const canEvaluate = me && hasPerm(me, "APPRAISE_TEACHER");
  const [rows, setRows] = useState<any[]>([]);
  const [criteria, setCriteria] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selected, setSelected] = useState<any | null>(null);
  const [scores, setScores] = useState<Record<string, string>>({});
  const [teacherId, setTeacherId] = useState("");

  const reload = async () => {
    try {
      setRows((await api("/appraisals")).items);
    } catch (e) {
      if (e instanceof ApiClientError && e.status !== 403) setError(e.message);
    }
  };

  useEffect(() => {
    if (!me) return;
    reload();
    if (canEvaluate) {
      api("/appraisals/criteria").then((r) => setCriteria(r.items)).catch(() => {});
      api("/teachers").then((r) => setTeachers(r.items)).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me]);

  const open = async (id: string) => {
    setError(null);
    try {
      const a = await api(`/appraisals/${id}`);
      setSelected(a);
      const m: Record<string, string> = {};
      for (const s of a.scores) m[s.criterion_id] = String(s.score);
      setScores(m);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Failed to load.");
    }
  };

  const create = async () => {
    if (!teacherId) return;
    setError(null); setNotice(null);
    try {
      await api("/appraisals", {
        method: "POST",
        body: { teacher_id: teacherId, period_from: "2026-09-07", period_to: "2026-12-10" },
      });
      setNotice("Draft appraisal created.");
      reload();
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Failed.");
    }
  };

  const saveScores = async () => {
    if (!selected) return;
    setError(null);
    try {
      await api(`/appraisals/${selected.id}/scores`, {
        method: "PUT",
        body: {
          scores: criteria
            .filter((c) => scores[c.id] !== undefined && scores[c.id] !== "")
            .map((c) => ({ criterion_id: c.id, score: Number(scores[c.id]) })),
        },
      });
      setNotice("Scores saved.");
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Failed.");
    }
  };

  const submit = async () => {
    if (!selected) return;
    setError(null);
    try {
      const r = await api(`/appraisals/${selected.id}/submit`, {
        method: "POST", body: { overall_comment: "Submitted via portal." },
      });
      setNotice(`Submitted — overall rating ${r.overall_rating}.`);
      setSelected(null);
      reload();
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Failed.");
    }
  };

  const acknowledge = async () => {
    if (!selected) return;
    setError(null);
    try {
      await api(`/appraisals/${selected.id}/acknowledge`, { method: "POST" });
      setNotice("Acknowledged.");
      setSelected(null);
      reload();
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Failed.");
    }
  };

  if (!me) return <Loading />;

  return (
    <>
      <PageHeader title="Teacher appraisals"
        subtitle="Configurable criteria · confidential until submitted · acknowledgement recorded" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}

      {canEvaluate && (
        <Panel title="New appraisal">
          <div className="flex flex-wrap items-end gap-3 px-4 py-3">
            <Field label="Teacher">
              <select className="input" value={teacherId} onChange={(e) => setTeacherId(e.target.value)}>
                <option value="">Select…</option>
                {teachers.map((t) => <option key={t.id} value={t.id}>{t.full_name}</option>)}
              </select>
            </Field>
            <button className="btn-primary" onClick={create} disabled={!teacherId}>Create draft (current term)</button>
          </div>
        </Panel>
      )}

      <div className="mt-4">
        <Panel title={canEvaluate ? "All appraisals" : "My appraisals"}>
          {rows.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">Nothing here yet.</p>
          ) : (
            <table className="tbl">
              <thead><tr><th>Teacher</th><th>Period</th><th>Status</th><th>Rating</th><th></th></tr></thead>
              <tbody>
                {rows.map((a) => (
                  <tr key={a.id}>
                    <td className="font-mono text-xs">{a.teacher_id.slice(0, 8)}…</td>
                    <td>{a.period_from} → {a.period_to}</td>
                    <td><Badge value={a.status} /></td>
                    <td>{a.overall_rating ?? "—"}</td>
                    <td className="text-right">
                      <button className="btn-secondary !py-1" onClick={() => open(a.id)}>Open</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      </div>

      {selected && (
        <div className="mt-4">
          <Panel title={`${selected.teacher_name ?? "Appraisal"} — ${selected.status}`} right={
            <div className="flex gap-2">
              {selected.status === "DRAFT" && canEvaluate && (
                <>
                  <button className="btn-secondary !py-1.5" onClick={saveScores}>Save scores</button>
                  <button className="btn-primary !py-1.5" onClick={submit}>Submit</button>
                </>
              )}
              {selected.status === "SUBMITTED" && !canEvaluate && (
                <button className="btn-primary !py-1.5" onClick={acknowledge}>Acknowledge</button>
              )}
            </div>
          }>
            <table className="tbl">
              <thead><tr><th>Criterion</th><th style={{ width: 110 }}>Score</th></tr></thead>
              <tbody>
                {(selected.scores.length ? selected.scores : criteria.map((c) => ({ criterion_id: c.id, criterion: c.name, max_score: c.max_score, score: null }))).map((s: any) => (
                  <tr key={s.criterion_id}>
                    <td>{s.criterion}</td>
                    <td>
                      {selected.status === "DRAFT" && canEvaluate ? (
                        <input type="number" min={0} max={s.max_score} className="input !py-1"
                          value={scores[s.criterion_id] ?? ""}
                          onChange={(e) => setScores({ ...scores, [s.criterion_id]: e.target.value })} />
                      ) : (
                        <span>{s.score ?? "—"} / {s.max_score}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {selected.overall_comment && (
              <p className="px-4 py-3 text-sm text-slate-600 border-t border-slate-100">
                {selected.overall_comment}
              </p>
            )}
          </Panel>
        </div>
      )}
    </>
  );
}
