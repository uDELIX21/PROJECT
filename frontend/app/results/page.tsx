"use client";

/** Computed results: class × subject → weighted totals, grades, positions. */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { activeContext, streamsFor, subjectsForGrade } from "../lib/academics";

export default function ResultsPage() {
  const [ctx, setCtx] = useState<Awaited<ReturnType<typeof activeContext>> | null>(null);
  const [streams, setStreams] = useState<any[]>([]);
  const [streamId, setStreamId] = useState("");
  const [subjects, setSubjects] = useState<any[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    activeContext().then(async (c) => {
      setCtx(c);
      if (c.year) setStreams(await streamsFor(c.year.id));
    }).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    const stream = streams.find((s) => s.id === streamId);
    if (!stream) return;
    subjectsForGrade(stream.grade.id).then((subs) => {
      setSubjects(subs);
      setSubjectId(subs[0]?.id ?? "");
    }).catch((e) => setError(e.message));
  }, [streamId, streams]);

  useEffect(() => {
    if (!ctx?.term || !streamId || !subjectId) return;
    setResult(null);
    api(`/assessments/results?term_id=${ctx.term.id}&class_stream_id=${streamId}&subject_id=${subjectId}`)
      .then(setResult)
      .catch((e) => {
        setResult(null);
        setError(e instanceof ApiClientError ? e.message : "Failed to load results.");
      });
  }, [ctx, streamId, subjectId]);

  if (!ctx) return <Loading />;

  return (
    <>
      <PageHeader title="Results" subtitle="Weighted scores, grades and positions from configured schemes" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      <Panel title="Select class & subject">
        <div className="grid gap-3 px-4 py-3 sm:grid-cols-2">
          <Field label="Class">
            <select className="input" value={streamId} onChange={(e) => setStreamId(e.target.value)}>
              <option value="">Select…</option>
              {streams.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
          <Field label="Subject">
            <select className="input" value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>
              {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
        </div>
      </Panel>

      {result && (
        <div className="mt-4">
          <Panel title={`Results — ${result.rows.length} students`}>
            <div className="overflow-x-auto">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>#</th><th>Code</th><th>Name</th>
                    {result.components.map((c: any) => (
                      <th key={c.code}>{c.name} ({c.weight_pct}%)</th>
                    ))}
                    <th>Final</th><th>Grade</th><th>Remark</th>
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((r: any) => (
                    <tr key={r.enrollment_id}>
                      <td>{r.position ?? "—"}</td>
                      <td className="font-mono text-xs">{r.admission_code}</td>
                      <td>{r.student_name}</td>
                      {result.components.map((c: any) => (
                        <td key={c.code}>{r.components?.[c.code] ?? "—"}</td>
                      ))}
                      <td className="font-semibold">{r.final_score ?? "—"}</td>
                      <td>{r.grade ?? "—"}</td>
                      <td className="text-slate-500">{r.remark ?? (r.complete ? "" : "incomplete")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      )}
    </>
  );
}
