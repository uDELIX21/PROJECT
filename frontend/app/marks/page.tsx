"use client";

/** Marks entry with offline-first sync (design §09):
    edits → IndexedDB outbox → POST /sync/mutations when online → server validation.
    Per-row states: synced / pending / failed / conflict (REQ-OFF-02). */
import React, { useEffect, useMemo, useRef, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel, Badge } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { activeContext, rosterFor, streamsFor, subjectsForGrade } from "../lib/academics";
import { enqueue, subscribeSync, latestStatus, removeFromQueue } from "../lib/offline/sync";
import { makeScoreMutation, resolveConflict, type OutboxItem } from "../lib/offline/engine";

interface SheetComponent { id: string; code: string; name: string; max_score: number; weight_pct: number }

const refFor = (sheetId: string, enrollmentId: string) =>
  `assessment=${sheetId};enrollment=${enrollmentId}`;

export default function MarksPage() {
  const [ctx, setCtx] = useState<Awaited<ReturnType<typeof activeContext>> | null>(null);
  const [streams, setStreams] = useState<any[]>([]);
  const [streamId, setStreamId] = useState("");
  const [subjects, setSubjects] = useState<any[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [components, setComponents] = useState<SheetComponent[]>([]);
  const [componentId, setComponentId] = useState("");
  const [roster, setRoster] = useState<any[]>([]);
  const [scores, setScores] = useState<Record<string, string>>({});
  const [sheet, setSheet] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [online, setOnline] = useState(true);
  const [, forceTick] = useState(0);
  const debounceRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const baseVersionRef = useRef<number | null>(null);

  useEffect(() => subscribeSync(() => forceTick((t) => t + 1)), []);
  useEffect(() => {
    const f = () => setOnline(navigator.onLine);
    window.addEventListener("online", f);
    window.addEventListener("offline", f);
    return () => { window.removeEventListener("online", f); window.removeEventListener("offline", f); };
  }, []);

  const statusByRef = useMemo(() => latestStatus(), [scores, online, sheet]); // re-render on queue updates

  useEffect(() => {
    activeContext().then(async (c) => {
      setCtx(c);
      if (c.year) setStreams(await streamsFor(c.year.id));
    }).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!streamId) return;
    const stream = streams.find((s) => s.id === streamId);
    Promise.all([rosterFor(streamId), stream ? subjectsForGrade(stream.grade.id) : Promise.resolve([])])
      .then(([r, subs]) => {
        setRoster(r);
        setSubjects(subs);
        setSubjectId(subs[0]?.id ?? "");
      })
      .catch((e: any) => setError(e.message));
  }, [streamId, streams]);

  useEffect(() => {
    if (!ctx?.term || !streamId || !subjectId) return;
    api(`/assessments/sheets?term_id=${ctx.term.id}&class_stream_id=${streamId}&subject_id=${subjectId}`)
      .then((r) => {
        setComponents(r.components);
        setComponentId(r.components[0]?.id ?? "");
      })
      .catch((e: any) => { setComponents([]); setError(e.message); });
  }, [ctx, streamId, subjectId]);

  useEffect(() => {
    if (!ctx?.term || !streamId || !subjectId || !componentId) return;
    api(`/assessments/sheets?term_id=${ctx.term.id}&class_stream_id=${streamId}&subject_id=${subjectId}&component_id=${componentId}`)
      .then((r) => {
        setSheet(r.sheet);
        baseVersionRef.current = r.sheet?.version ?? null;
        const m: Record<string, string> = {};
        for (const s of r.scores) if (s.raw_score !== null) m[s.enrollment_id] = String(s.raw_score);
        setScores(m);
      })
      .catch((e: any) => setError(e.message));
  }, [ctx, streamId, subjectId, componentId]);

  const queueChange = (enrollmentId: string, value: string) => {
    setScores((prev) => ({ ...prev, [enrollmentId]: value }));
    if (!sheet || sheet.status !== "DRAFT") return;
    const ref = refFor(sheet.id, enrollmentId);
    clearTimeout(debounceRef.current[ref]);
    debounceRef.current[ref] = setTimeout(() => {
      const raw = value === "" ? null : Number(value);
      if (raw !== null && (isNaN(raw) || raw < 0)) return;
      void enqueue(makeScoreMutation(sheet.id, enrollmentId, raw, baseVersionRef.current));
    }, 600);
  };

  const submit = async () => {
    if (!sheet) return;
    setBusy(true); setError(null); setNotice(null);
    try {
      await api("/assessments/sheets/submit", { method: "POST", body: { sheet_id: sheet.id } });
      setNotice("Sheet submitted — now read-only. Corrections go through the override workflow.");
      setSheet({ ...sheet, status: "SUBMITTED" });
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Submit failed.");
    } finally { setBusy(false); }
  };

  const conflicts = Object.values(statusByRef).filter(
    (i) => i.status === "CONFLICT" && i.entity_ref.startsWith(`assessment=${sheet?.id};`));

  const handleConflict = async (item: OutboxItem, choice: "KEEP_MINE" | "TAKE_SERVER") => {
    const serverVersion = item.result?.details?.server_version ?? null;
    const next = resolveConflict(item, choice, serverVersion);
    await removeFromQueue(item.client_mutation_id);
    if (choice === "TAKE_SERVER") {
      const enrollmentId = item.payload.enrollment_id as string;
      const sv = item.result?.details?.server_value;
      setScores((prev) => ({ ...prev, [enrollmentId]: sv === null || sv === undefined ? "" : String(sv) }));
      if (serverVersion !== null) baseVersionRef.current = serverVersion;
    } else if (next) {
      if (serverVersion !== null) baseVersionRef.current = serverVersion;
      void enqueue(next);
    }
  };

  if (!ctx) return <Loading label="Loading academic context…" />;
  const editable = !!sheet && sheet.status === "DRAFT";

  return (
    <>
      <PageHeader title="Marks entry"
        subtitle={`${ctx.year?.name ?? "—"} · ${ctx.term?.name ?? "—"} · works offline — entries queue locally and sync when back online`} />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}
      {!online && (
        <div className="mb-4 rounded-md border border-slate-300 bg-slate-100 px-4 py-2 text-sm text-slate-700">
          You are offline. Scores are saved on this device and will sync automatically when the connection returns.
        </div>
      )}

      <Panel title="Select sheet">
        <div className="grid gap-3 px-4 py-3 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Class">
            <select className="input" value={streamId} onChange={(e) => setStreamId(e.target.value)}>
              <option value="">Select…</option>
              {streams.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
          <Field label="Subject">
            <select className="input" value={subjectId} onChange={(e) => setSubjectId(e.target.value)} disabled={!streamId}>
              {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
          <Field label="Component">
            <select className="input" value={componentId} onChange={(e) => setComponentId(e.target.value)} disabled={components.length === 0}>
              {components.map((c) => (
                <option key={c.id} value={c.id}>{c.name} ({c.weight_pct}%)</option>
              ))}
            </select>
          </Field>
          <div className="flex items-end gap-2">
            <button className="btn-secondary" onClick={submit} disabled={!editable || busy || !online}
              title={!online ? "Submit requires a connection — your entries stay queued offline" : undefined}>
              Submit sheet
            </button>
          </div>
        </div>
        {sheet && (
          <p className="px-4 pb-3 text-xs text-slate-500 flex items-center gap-2">
            Sheet status: <Badge value={sheet.status} /> · version {sheet.version}
            {!editable && " · read-only: use the correction workflow for changes"}
          </p>
        )}
      </Panel>

      {conflicts.length > 0 && (
        <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-800 mb-2">
            {conflicts.length} conflict(s) need attention — the sheet changed on the server since you synced.
          </p>
          {conflicts.map((c) => {
            const enrollmentId = c.payload.enrollment_id as string;
            const student = roster.find((r) => r.enrollment.id === enrollmentId);
            return (
              <div key={c.client_mutation_id} className="flex flex-wrap items-center gap-3 py-1.5 text-sm text-amber-900">
                <span className="font-medium">{student?.full_name ?? enrollmentId.slice(0, 8)}</span>
                <span>yours: {String(c.payload.raw_score ?? "—")}</span>
                <span>server: {String(c.result?.details?.server_value ?? "—")}</span>
                <button className="btn-secondary !py-1" onClick={() => handleConflict(c, "KEEP_MINE")}>Keep mine</button>
                <button className="btn-secondary !py-1" onClick={() => handleConflict(c, "TAKE_SERVER")}>Take server</button>
              </div>
            );
          })}
        </div>
      )}

      {sheet && (
        <div className="mt-4">
          <Panel title={`Scores — max ${components.find((c) => c.id === componentId)?.max_score ?? 100}`}>
            {roster.length === 0 ? (
              <p className="px-4 py-4 text-sm text-slate-500">No active enrollments in this class.</p>
            ) : (
              <table className="tbl">
                <thead>
                  <tr><th>Code</th><th>Name</th><th style={{ width: 120 }}>Score</th><th style={{ width: 110 }}>Sync</th></tr>
                </thead>
                <tbody>
                  {roster.map((r) => {
                    const ref = refFor(sheet.id, r.enrollment.id);
                    const item = statusByRef.get(ref);
                    return (
                      <tr key={r.id}>
                        <td className="font-mono text-xs">{r.admission_code}</td>
                        <td>{r.full_name}</td>
                        <td>
                          <input
                            type="number" min={0}
                            max={components.find((c) => c.id === componentId)?.max_score ?? 100}
                            className="input !py-1"
                            disabled={!editable}
                            value={scores[r.enrollment.id] ?? ""}
                            onChange={(e) => queueChange(r.enrollment.id, e.target.value)}
                          />
                        </td>
                        <td>
                          {!item || item.status === "SYNCED" ? (
                            <span className="text-xs text-emerald-600">✓ synced</span>
                          ) : item.status === "PENDING" ? (
                            <span className="text-xs text-amber-600">pending…</span>
                          ) : item.status === "CONFLICT" ? (
                            <span className="text-xs text-red-600">conflict</span>
                          ) : (
                            <span className="text-xs text-red-600" title={item.result?.message}>
                              failed
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </Panel>
        </div>
      )}
    </>
  );
}
