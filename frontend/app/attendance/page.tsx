"use client";

/** Daily roll call with offline-first sync: statuses queue locally and sync
    through /sync/mutations; submit requires a connection. */
import React, { useEffect, useMemo, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel, Badge } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { activeContext, rosterFor, streamsFor } from "../lib/academics";
import { enqueue, latestStatus, subscribeSync } from "../lib/offline/sync";
import { makeAttendanceMutation } from "../lib/offline/engine";

const STATUSES = ["PRESENT", "ABSENT", "LATE", "EXCUSED", "LEFT_EARLY"] as const;

export default function AttendancePage() {
  const [ctx, setCtx] = useState<Awaited<ReturnType<typeof activeContext>> | null>(null);
  const [streams, setStreams] = useState<any[]>([]);
  const [streamId, setStreamId] = useState("");
  const [date, setDate] = useState("");
  const [roster, setRoster] = useState<any[]>([]);
  const [statuses, setStatuses] = useState<Record<string, string>>({});
  const [sheetStatus, setSheetStatus] = useState<string | null>(null);
  const [sheetId, setSheetId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [summary, setSummary] = useState<any | null>(null);
  const [online, setOnline] = useState(true);
  const [, forceTick] = useState(0);

  useEffect(() => subscribeSync(() => forceTick((t) => t + 1)), []);
  useEffect(() => {
    const f = () => setOnline(navigator.onLine);
    window.addEventListener("online", f); window.addEventListener("offline", f);
    return () => { window.removeEventListener("online", f); window.removeEventListener("offline", f); };
  }, []);
  const statusByRef = useMemo(() => latestStatus(), [statuses, online]);

  useEffect(() => {
    activeContext().then(async (c) => {
      setCtx(c);
      if (c.year) setStreams(await streamsFor(c.year.id));
      setDate(new Date().toISOString().slice(0, 10));
    }).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!streamId) return;
    rosterFor(streamId).then(setRoster).catch((e) => setError(e.message));
  }, [streamId]);

  useEffect(() => {
    if (!streamId || !date) return;
    api(`/attendance/sheets?class_stream_id=${streamId}&sheet_date=${date}`)
      .then((r) => {
        const m: Record<string, string> = {};
        for (const rec of r.records) m[rec.enrollment_id] = rec.status;
        setStatuses(m);
        setSheetStatus(r.sheet?.status ?? null);
        setSheetId(r.sheet?.id ?? null);
      })
      .catch((e) => {
        if (e instanceof ApiClientError && e.status === 404) { setStatuses({}); setSheetStatus(null); }
        else setError(e.message);
      });
  }, [streamId, date]);

  const setStatus = (enrollmentId: string, status: string) => {
    setStatuses((prev) => ({ ...prev, [enrollmentId]: status }));
    if (!ctx?.term || sheetStatus === "SUBMITTED") return;
    void enqueue(makeAttendanceMutation(streamId, ctx.term.id, date, enrollmentId, status, null));
  };

  const submit = async () => {
    if (!ctx?.term) return;
    setError(null); setNotice(null);
    try {
      // ensure sheet exists server-side (offline-created records sync separately)
      let id = sheetId;
      if (!id) {
        const res = await api("/attendance/sheets", {
          method: "PUT",
          body: { class_stream_id: streamId, term_id: ctx.term.id, sheet_date: date,
                  records: roster.map((r) => ({ enrollment_id: r.enrollment.id,
                                                 status: statuses[r.enrollment.id] ?? "PRESENT" })) },
        });
        id = res.id;
      }
      await api("/attendance/sheets/submit", { method: "POST", body: { sheet_id: id } });
      setSheetStatus("SUBMITTED");
      setNotice("Attendance submitted.");
      const s = await api(`/attendance/summary?class_stream_id=${streamId}&term_id=${ctx.term.id}`);
      setSummary(s);
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Submit failed.");
    }
  };

  if (!ctx) return <Loading label="Loading…" />;
  const editable = sheetStatus !== "SUBMITTED";

  return (
    <>
      <PageHeader title="Attendance" subtitle="Roll call syncs offline too — submit when connected" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}
      {!online && (
        <div className="mb-4 rounded-md border border-slate-300 bg-slate-100 px-4 py-2 text-sm text-slate-700">
          Offline: statuses are saved on this device and will sync automatically.
        </div>
      )}

      <Panel title="Roll call">
        <div className="flex flex-wrap items-end gap-3 px-4 py-3 border-b border-slate-100">
          <Field label="Class">
            <select className="input" value={streamId} onChange={(e) => setStreamId(e.target.value)}>
              <option value="">Select…</option>
              {streams.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
          <Field label="Date">
            <input type="date" className="input" value={date} onChange={(e) => setDate(e.target.value)} />
          </Field>
          <button className="btn-secondary" disabled={!streamId || !editable || !online} onClick={submit}
            title={!online ? "Submitting requires a connection — statuses stay queued offline" : undefined}>
            Submit
          </button>
          {sheetStatus && <Badge value={sheetStatus} />}
        </div>
        {streamId && roster.length === 0 && <p className="px-4 py-4 text-sm text-slate-500">No active enrollments.</p>}
        {roster.length > 0 && (
          <table className="tbl">
            <thead>
              <tr><th>Code</th><th>Name</th><th>Status</th><th style={{ width: 90 }}>Sync</th></tr>
            </thead>
            <tbody>
              {roster.map((r) => {
                const ref = `stream=${streamId};date=${date};enrollment=${r.enrollment.id}`;
                const item = statusByRef.get(ref);
                return (
                  <tr key={r.id}>
                    <td className="font-mono text-xs">{r.admission_code}</td>
                    <td>{r.full_name}</td>
                    <td>
                      <select className="input !py-1 !w-44" disabled={!editable}
                        value={statuses[r.enrollment.id] ?? "PRESENT"}
                        onChange={(e) => setStatus(r.enrollment.id, e.target.value)}>
                        {STATUSES.map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
                      </select>
                    </td>
                    <td>
                      {!item ? <span className="text-xs text-slate-400">—</span>
                        : item.status === "SYNCED" ? <span className="text-xs text-emerald-600">✓ synced</span>
                        : item.status === "PENDING" ? <span className="text-xs text-amber-600">pending…</span>
                        : item.status === "CONFLICT" ? <span className="text-xs text-red-600">conflict</span>
                        : <span className="text-xs text-red-600">failed</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Panel>

      {summary && (
        <div className="mt-4">
          <Panel title="Term summary (this class)">
            <table className="tbl">
              <thead><tr><th>Student</th><th>Days recorded</th><th>Attendance %</th></tr></thead>
              <tbody>
                {summary.items.map((i: any) => (
                  <tr key={i.student_id}>
                    <td>{i.student_name}</td>
                    <td>{i.days_recorded}</td>
                    <td>{i.percentage ?? "—"}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </div>
      )}
    </>
  );
}
