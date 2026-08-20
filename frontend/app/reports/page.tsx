"use client";

/** Report cards: staff generate → finalize → publish; parents see published PDFs. */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel, Badge } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { useSession, hasPerm } from "../lib/session";
import { activeContext, streamsFor, rosterFor } from "../lib/academics";

export default function ReportsPage() {
  const { me } = useSession();
  const isStaff = me && (hasPerm(me, "MANAGE_REPORTS"));
  const [ctx, setCtx] = useState<Awaited<ReturnType<typeof activeContext>> | null>(null);
  const [streams, setStreams] = useState<any[]>([]);
  const [streamId, setStreamId] = useState("");
  const [roster, setRoster] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    activeContext().then(async (c) => {
      setCtx(c);
      if (c.year && isStaff) setStreams(await streamsFor(c.year.id));
    }).catch((e) => setError(e.message));
  }, [me, isStaff]);

  useEffect(() => {
    if (!streamId) return;
    rosterFor(streamId).then(setRoster).catch((e) => setError(e.message));
  }, [streamId]);

  const loadReports = async (studentId?: string) => {
    if (!ctx?.term) return;
    try {
      const qs = studentId ? `&student_id=${studentId}` : "";
      const r = await api(`/reports?term_id=${ctx.term.id}${qs}`);
      setReports(r.items);
    } catch (e) {
      if (e instanceof ApiClientError) {
        if (e.status !== 403) setError(e.message);
      } else if (e instanceof Error) {
        setError(e.message);
      }
    }
  };

  useEffect(() => {
    if (ctx?.term) loadReports();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ctx?.term]);

  const act = async (reportId: string, action: "generate" | "finalize" | "publish", body?: any) => {
    setBusyId(reportId + action); setError(null); setNotice(null);
    try {
      if (action === "generate") {
        await api("/reports/generate", { method: "POST", body });
      } else {
        await api(`/reports/${reportId}/${action}`, { method: "POST", body: body ?? {} });
      }
      setNotice(`Report ${action} succeeded.`);
      await loadReports(body?.student_id);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Action failed.");
    } finally { setBusyId(null); }
  };

  if (!ctx) return <Loading />;

  const reportFor = (studentId: string) => reports.find((r) => r.student_id === studentId);

  return (
    <>
      <PageHeader title="Report cards"
        subtitle={`${ctx.term?.name ?? "—"} · ${ctx.year?.name ?? "—"} · publication respects financial clearance (Phase 5)`} />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}

      {isStaff ? (
        <>
          <Panel title="Class reports">
            <div className="px-4 py-3 border-b border-slate-100">
              <Field label="Class">
                <select className="input max-w-xs" value={streamId} onChange={(e) => setStreamId(e.target.value)}>
                  <option value="">Select…</option>
                  {streams.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </Field>
            </div>
            {streamId && roster.length === 0 && <p className="px-4 py-4 text-sm text-slate-500">No active enrollments.</p>}
            {roster.length > 0 && (
              <table className="tbl">
                <thead>
                  <tr><th>Code</th><th>Name</th><th>Status</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  {roster.map((r) => {
                    const rep = reportFor(r.id);
                    return (
                      <tr key={r.id}>
                        <td className="font-mono text-xs">{r.admission_code}</td>
                        <td>{r.full_name}</td>
                        <td>{rep ? <Badge value={rep.status} /> : <span className="text-slate-400">not generated</span>}</td>
                        <td className="space-x-1 whitespace-nowrap">
                          {!rep && (
                            <button className="btn-secondary !py-1"
                              disabled={busyId !== null}
                              onClick={() => act("", "generate", { student_id: r.id, term_id: ctx.term!.id })}>
                              Generate
                            </button>
                          )}
                          {rep?.status === "GENERATED" && (
                            <>
                              <button className="btn-secondary !py-1" disabled={busyId !== null}
                                onClick={() => act(rep.id, "finalize")}>Finalize</button>
                              <a className="btn-secondary !py-1" href={`/api/v1/reports/${rep.id}/pdf`} target="_blank">PDF</a>
                            </>
                          )}
                          {(rep?.status === "FINALIZED") && (
                            <button className="btn-primary !py-1" disabled={busyId !== null}
                              onClick={() => act(rep.id, "publish")}>Publish</button>
                          )}
                          {rep?.status === "PUBLISHED" && (
                            <a className="btn-secondary !py-1" href={`/api/v1/reports/${rep.id}/pdf`} target="_blank">PDF</a>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </Panel>
        </>
      ) : (
        <Panel title="Published reports (your children)">
          {reports.length === 0 ? (
            <p className="px-4 py-6 text-sm text-slate-500">
              No published reports yet. Reports appear here once the school publishes them.
            </p>
          ) : (
            <table className="tbl">
              <thead><tr><th>Report</th><th>Published</th><th></th></tr></thead>
              <tbody>
                {reports.map((r) => (
                  <tr key={r.id}>
                    <td>{r.student_id.slice(0, 8)}…</td>
                    <td className="text-slate-500">{r.published_at ? new Date(r.published_at).toLocaleString() : "—"}</td>
                    <td><a className="btn-primary !py-1" href={`/api/v1/reports/${r.id}/pdf`} target="_blank">Open PDF</a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      )}
    </>
  );
}
