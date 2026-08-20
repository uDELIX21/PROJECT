"use client";

/** Bulk imports: upload → preview (errors/duplicates/parent matches) →
    resolve matches → confirm (atomic) → report. */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel, Badge } from "../components/ui";
import { api, ApiClientError } from "../lib/api";

const KINDS = ["STUDENTS", "TEACHERS", "PARENTS"];
const sevTone: Record<string, string> = {
  OK: "text-emerald-600", WARNING: "text-amber-600", ERROR: "text-red-600",
  DUPLICATE: "text-orange-600", MATCH_CANDIDATE: "text-sky-700",
};

export default function ImportsPage() {
  const [kind, setKind] = useState("STUDENTS");
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<any | null>(null);
  const [rows, setRows] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadHistory = async () => {
    try { setHistory((await api("/imports")).items); } catch { /* ignore */ }
  };
  useEffect(() => { loadHistory(); }, []);

  const loadPreview = async (jobId: string) => {
    const pv = await api(`/imports/${jobId}/preview`);
    setJob(pv.job);
    setRows(pv.rows);
  };

  const upload = async () => {
    if (!file) return;
    setBusy(true); setError(null); setNotice(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("kind", kind);
      const csrf = (await api("/auth/csrf")).csrf_token;
      const res = await fetch("/api/v1/imports/upload", {
        method: "POST", credentials: "same-origin",
        headers: { "X-CSRF-Token": csrf }, body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new ApiClientError(res.status, data?.error?.code ?? "UPLOAD_FAILED",
                                            data?.error?.message ?? "Upload failed");
      setNotice(`Parsed ${data.rows_total} row(s): ${data.rows_ok} ok, ${data.rows_error} error(s), ${data.rows_duplicate} duplicate(s), ${data.rows_match} parent match(es).`);
      await loadPreview(data.job_id);
      loadHistory();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally { setBusy(false); }
  };

  const resolveMatch = async (rowId: string, action: string, guardianId?: string) => {
    if (!job) return;
    setError(null);
    try {
      await api(`/imports/${job.id}/matches/${rowId}/resolve`, {
        method: "POST", body: { action, guardian_id: guardianId ?? null },
      });
      await loadPreview(job.id);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Failed.");
    }
  };

  const confirm = async () => {
    if (!job) return;
    setBusy(true); setError(null); setNotice(null);
    try {
      const r = await api(`/imports/${job.id}/confirm`, { method: "POST" });
      setNotice(`Import complete: ${r.created} created, ${r.skipped_duplicates} duplicate(s) skipped, ${r.warnings} warning(s).`);
      const rep = await api(`/imports/${job.id}`);
      setJob(rep);
      setRows([]);
      loadHistory();
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Import failed.");
    } finally { setBusy(false); }
  };

  return (
    <>
      <PageHeader title="Bulk import"
        subtitle="CSV/XLSX → validate → preview → confirm. Commits are transaction-safe: everything lands or nothing does." />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}

      <Panel title="1 · Upload file">
        <div className="flex flex-wrap items-end gap-3 px-4 py-3">
          <Field label="Type">
            <select className="input" value={kind} onChange={(e) => setKind(e.target.value)}>
              {KINDS.map((k) => <option key={k}>{k}</option>)}
            </select>
          </Field>
          <Field label="File (.csv or .xlsx)">
            <input type="file" accept=".csv,.xlsx" className="text-sm"
                   onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </Field>
          <button className="btn-secondary" onClick={() => window.open(`/api/v1/imports/templates/${kind}?format=csv`, "_blank")}>
            CSV template
          </button>
          <button className="btn-secondary" onClick={() => window.open(`/api/v1/imports/templates/${kind}?format=xlsx`, "_blank")}>
            XLSX template
          </button>
          <button className="btn-primary" onClick={upload} disabled={busy || !file}>
            {busy ? "Uploading…" : "Upload & validate"}
          </button>
        </div>
      </Panel>

      {job && rows.length > 0 && (
        <div className="mt-4">
          <Panel title={`2 · Preview — ${job.file_name}`} right={
            <div className="flex items-center gap-3 text-xs">
              <span className="text-emerald-600">{job.rows_ok} ok</span>
              <span className="text-amber-600">{job.rows_warning} warn</span>
              <span className="text-red-600">{job.rows_error} errors</span>
              <span className="text-orange-600">{job.rows_duplicate} dup</span>
              <span className="text-sky-700">{job.rows_match} matches</span>
            </div>
          }>
            <table className="tbl">
              <thead>
                <tr><th style={{ width: 50 }}>Row</th><th style={{ width: 130 }}>Status</th>
                    <th>Message / guidance</th></tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td className="text-xs">{r.row_no}</td>
                    <td className={`text-xs font-medium ${sevTone[r.severity] ?? ""}`}>
                      {r.severity.replaceAll("_", " ")}
                    </td>
                    <td className="text-sm">
                      {r.severity === "OK" ? (
                        <span className="text-slate-500">
                          {Object.entries(r.raw_row).filter(([, v]) => v).slice(0, 4)
                            .map(([k, v]) => `${k}=${v}`).join(" · ")}
                        </span>
                      ) : (
                        <>
                          <p>{r.message}</p>
                          {r.guidance && <p className="text-xs text-slate-400 mt-0.5">💡 {r.guidance}</p>}
                          {r.severity === "MATCH_CANDIDATE" && r.match_suggestion && !r.match_suggestion.resolved && (
                            <div className="mt-1.5 flex flex-wrap items-center gap-2">
                              {r.match_suggestion.candidates.map((c: any) => (
                                <span key={c.guardian_id} className="text-xs bg-sky-50 rounded px-2 py-1">
                                  {c.guardian_name} ({c.confidence})
                                </span>
                              ))}
                              <button className="btn-secondary !py-1 text-xs"
                                onClick={() => resolveMatch(r.id, "LINK", r.match_suggestion.candidates[0].guardian_id)}>
                                Link existing
                              </button>
                              <button className="btn-secondary !py-1 text-xs" onClick={() => resolveMatch(r.id, "NEW")}>
                                Create new guardian
                              </button>
                              <button className="btn-secondary !py-1 text-xs" onClick={() => resolveMatch(r.id, "SKIP")}>
                                Skip link
                              </button>
                            </div>
                          )}
                          {r.severity === "MATCH_CANDIDATE" && r.match_suggestion?.resolved && (
                            <p className="text-xs text-emerald-700 mt-1">
                              ✓ Resolved: {r.match_suggestion.action}
                            </p>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
              <p className="text-xs text-slate-500">
                Rows with errors block the import; duplicates are skipped; parent matches must be resolved (never auto-linked).
              </p>
              <button className="btn-primary" onClick={confirm} disabled={busy || job.stage !== "PREVIEWED"}>
                {busy ? "Importing…" : "Confirm import (atomic)"}
              </button>
            </div>
          </Panel>
        </div>
      )}

      <div className="mt-4">
        <Panel title="Import history">
          {history.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">No imports yet.</p>
          ) : (
            <table className="tbl">
              <thead><tr><th>When</th><th>Type</th><th>File</th><th>Rows</th><th>Stage</th><th>Result</th></tr></thead>
              <tbody>
                {history.map((j) => (
                  <tr key={j.id}>
                    <td className="text-xs text-slate-500 whitespace-nowrap">{new Date(j.created_at).toLocaleString()}</td>
                    <td>{j.kind}</td>
                    <td className="text-xs">{j.file_name}</td>
                    <td>{j.rows_total}</td>
                    <td><Badge value={j.stage === "COMPLETED" ? "CLEAR" : j.stage === "ROLLED_BACK" ? "WITHDRAWN" : "PENDING"} /></td>
                    <td className="text-xs text-slate-500">{j.summary?.created !== undefined ? `${j.summary.created} created` : j.summary?.error ?? "—"}</td>
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
