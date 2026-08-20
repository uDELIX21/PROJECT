"use client";

/** Early childhood: developmental ratings + observation log (qualitative only, BR-M07). */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, Loading, PageHeader, Panel } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { activeContext, rosterFor, streamsFor } from "../lib/academics";

const RATINGS = ["EMERGING", "DEVELOPING", "ACHIEVED"];

export default function EcdPage() {
  const [ctx, setCtx] = useState<Awaited<ReturnType<typeof activeContext>> | null>(null);
  const [streams, setStreams] = useState<any[]>([]);
  const [streamId, setStreamId] = useState("");
  const [roster, setRoster] = useState<any[]>([]);
  const [studentIdx, setStudentIdx] = useState(0);
  const [domains, setDomains] = useState<any[]>([]);
  const [ratings, setRatings] = useState<Record<string, string>>({});
  const [observations, setObservations] = useState<any[]>([]);
  const [newObs, setNewObs] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    activeContext().then(async (c) => {
      setCtx(c);
      if (c.year) {
        const all = await streamsFor(c.year.id);
        setStreams(all.filter((s) => s.grade.band === "EARLY_CHILDHOOD"));
      }
      setDomains((await api("/ecd/domains")).items);
    }).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!streamId) return;
    rosterFor(streamId).then((r) => { setRoster(r); setStudentIdx(0); }).catch((e) => setError(e.message));
  }, [streamId]);

  const child = roster[studentIdx];
  const enrollmentId = child?.enrollment?.id;

  useEffect(() => {
    if (!ctx?.term || !enrollmentId) return;
    api(`/ecd/ratings?enrollment_id=${enrollmentId}&term_id=${ctx.term.id}`)
      .then((r) => {
        const m: Record<string, string> = {};
        for (const i of r.items) if (i.domain_id) m[i.domain_id] = i.rating;
        setRatings(m);
      })
      .catch(() => setRatings({}));
    api(`/ecd/observations?enrollment_id=${enrollmentId}`)
      .then((r) => setObservations(r.items))
      .catch(() => setObservations([]));
  }, [ctx, enrollmentId]);

  const saveRatings = async () => {
    if (!ctx?.term || !enrollmentId) return;
    setError(null); setNotice(null);
    try {
      await api("/ecd/ratings", {
        method: "PUT",
        body: {
          enrollment_id: enrollmentId, term_id: ctx.term.id,
          ratings: Object.entries(ratings)
            .filter(([, v]) => v)
            .map(([domain_id, rating]) => ({ domain_id, rating })),
        },
      });
      setNotice("Developmental ratings saved.");
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Save failed.");
    }
  };

  const addObservation = async () => {
    if (!enrollmentId || !newObs.trim()) return;
    setError(null); setNotice(null);
    try {
      await api("/ecd/observations", {
        method: "POST", body: { enrollment_id: enrollmentId, body: newObs.trim() },
      });
      setNewObs("");
      const r = await api(`/ecd/observations?enrollment_id=${enrollmentId}`);
      setObservations(r.items);
      setNotice("Observation logged.");
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Save failed.");
    }
  };

  if (!ctx) return <Loading />;

  return (
    <>
      <PageHeader title="Early childhood"
        subtitle="Qualitative developmental assessment — no numeric marks for Crèche/Nursery/KG (BR-M07)" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}

      <Panel title="Select class & child">
        <div className="grid gap-3 px-4 py-3 sm:grid-cols-2">
          <Field label="ECD class">
            <select className="input" value={streamId} onChange={(e) => setStreamId(e.target.value)}>
              <option value="">Select…</option>
              {streams.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
          <Field label="Child">
            <select className="input" value={studentIdx} onChange={(e) => setStudentIdx(Number(e.target.value))} disabled={roster.length === 0}>
              {roster.map((r, i) => <option key={r.id} value={i}>{r.full_name}</option>)}
            </select>
          </Field>
        </div>
      </Panel>

      {child && (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <Panel title="Developmental ratings" right={
            <button className="btn-primary !py-1.5" onClick={saveRatings}>Save ratings</button>
          }>
            <table className="tbl">
              <thead><tr><th>Domain</th><th>Rating</th></tr></thead>
              <tbody>
                {domains.map((d) => (
                  <tr key={d.id}>
                    <td>{d.name}</td>
                    <td>
                      <select className="input !py-1 !w-40" value={ratings[d.id] ?? ""}
                        onChange={(e) => setRatings({ ...ratings, [d.id]: e.target.value })}>
                        <option value="">—</option>
                        {RATINGS.map((r) => <option key={r} value={r}>{r}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Observation log">
            <div className="flex gap-2 px-4 py-3 border-b border-slate-100">
              <input className="input" placeholder="Today's observation…"
                value={newObs} onChange={(e) => setNewObs(e.target.value)} />
              <button className="btn-primary" onClick={addObservation}>Add</button>
            </div>
            {observations.length === 0 ? (
              <p className="px-4 py-4 text-sm text-slate-500">No observations yet.</p>
            ) : (
              <ul className="px-4 py-3 space-y-2">
                {observations.map((o) => (
                  <li key={o.id} className="text-sm">
                    <span className="text-xs text-slate-400 mr-2">{o.logged_on}</span>
                    {o.body}
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>
      )}
    </>
  );
}
