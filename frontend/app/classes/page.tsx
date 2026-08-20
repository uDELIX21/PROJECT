"use client";

import React, { useEffect, useState } from "react";
import { EmptyState, ErrorBanner, Loading, PageHeader, Panel } from "../components/ui";
import { api } from "../lib/api";

interface Stream { id: string; name: string; section_label: string; capacity: number | null;
  grade: { code: string; name: string; band: string }; academic_year_id: string }
interface RosterItem { id: string; admission_code: string; full_name: string; gender: string; status: string }

export default function ClassesPage() {
  const [years, setYears] = useState<{ id: string; name: string; status: string }[]>([]);
  const [yearId, setYearId] = useState("");
  const [streams, setStreams] = useState<Stream[] | null>(null);
  const [roster, setRoster] = useState<{ stream: Stream; items: RosterItem[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<{ items: typeof years }>("/settings/academic-years")
      .then((r) => {
        setYears(r.items);
        const active = r.items.find((y) => y.status === "ACTIVE");
        setYearId(active?.id ?? r.items[0]?.id ?? "");
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!yearId) return;
    setStreams(null); setRoster(null);
    api<{ items: Stream[] }>(`/classes/streams?academic_year_id=${yearId}`)
      .then((r) => setStreams(r.items))
      .catch((e) => setError(e.message));
  }, [yearId]);

  const openRoster = async (s: Stream) => {
    setRoster(null);
    try {
      const r = await api(`/classes/streams/${s.id}/roster`);
      setRoster(r);
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <>
      <PageHeader
        title="Classes"
        subtitle="Streams per academic year — teachers see only their assigned classes (server-enforced)"
        actions={
          <select className="input !w-auto" value={yearId} onChange={(e) => setYearId(e.target.value)}>
            {years.map((y) => (
              <option key={y.id} value={y.id}>{y.name}{y.status === "ACTIVE" ? " (active)" : ""}</option>
            ))}
          </select>
        }
      />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}

      {streams === null ? (
        <Loading />
      ) : streams.length === 0 ? (
        <EmptyState title="No class streams for this year" />
      ) : (
        <Panel>
          <div className="overflow-x-auto">
            <table className="tbl">
              <thead>
                <tr><th>Class</th><th>Band</th><th>Section</th><th>Capacity</th><th></th></tr>
              </thead>
              <tbody>
                {streams.map((s) => (
                  <tr key={s.id}>
                    <td className="font-medium">{s.name}</td>
                    <td className="text-slate-500">{s.grade.band.replaceAll("_", " ")}</td>
                    <td>{s.section_label}</td>
                    <td>{s.capacity ?? "—"}</td>
                    <td className="text-right">
                      <button className="btn-secondary !py-1" onClick={() => openRoster(s)}>
                        Roster
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {roster && (
        <div className="mt-4">
          <Panel title={`Roster — ${roster.stream.name} (${roster.items.length} students)`}>
            {roster.items.length === 0 ? (
              <EmptyState title="No active enrollments in this class" />
            ) : (
              <div className="overflow-x-auto">
                <table className="tbl">
                  <thead>
                    <tr><th>Code</th><th>Name</th><th>Gender</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {roster.items.map((s) => (
                      <tr key={s.id}>
                        <td className="font-mono text-xs">{s.admission_code}</td>
                        <td>{s.full_name}</td>
                        <td>{s.gender}</td>
                        <td className="text-slate-500">{s.status.replaceAll("_", " ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>
      )}
    </>
  );
}
