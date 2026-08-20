"use client";

import Link from "next/link";
import React, { useCallback, useEffect, useState } from "react";
import { Badge, EmptyState, ErrorBanner, Loading, PageHeader, Panel } from "../components/ui";
import { api } from "../lib/api";
import { useSession } from "../lib/session";

interface StudentRow {
  id: string;
  admission_code: string;
  full_name: string;
  gender: string;
  date_of_birth: string;
  status: string;
}

const STATUSES = ["", "APPLICANT", "ADMITTED", "ENROLLED", "ACTIVE", "PROMOTED", "REPEATED",
  "WITHDRAWN", "TRANSFERRED", "SUSPENDED", "GRADUATED"];

export default function StudentsPage() {
  const { me } = useSession();
  const [rows, setRows] = useState<StudentRow[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
      if (q) params.set("q", q);
      if (status) params.set("status", status);
      const r = await api(`/students?${params}`);
      setRows(r.items);
      setTotal(r.total);
    } catch (e: any) {
      setError(e.message ?? "Failed to load students.");
    } finally {
      setLoading(false);
    }
  }, [q, status, offset]);

  useEffect(() => {
    if (me) load();
  }, [me, load]);

  return (
    <>
      <PageHeader
        title="Students"
        subtitle={total !== null ? `${total} record${total === 1 ? "" : "s"} (server-scoped to your role)` : undefined}
      />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      <Panel>
        <form
          className="flex flex-wrap items-end gap-3 px-4 py-3 border-b border-slate-200"
          onSubmit={(e) => {
            e.preventDefault();
            setOffset(0);
            load();
          }}
        >
          <div className="flex-1 min-w-48">
            <label className="label">Search</label>
            <input
              className="input"
              placeholder="Name or admission code…"
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setOffset(0);
              }}
            />
          </div>
          <div>
            <label className="label">Status</label>
            <select
              className="input"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setOffset(0);
              }}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s || "All statuses"}
                </option>
              ))}
            </select>
          </div>
          <button className="btn-primary" type="submit">Filter</button>
        </form>

        {loading ? (
          <Loading />
        ) : rows.length === 0 ? (
          <EmptyState title="No students match" hint="Adjust the search or filters." />
        ) : (
          <div className="overflow-x-auto">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Gender</th>
                  <th>DoB</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr key={s.id}>
                    <td className="font-mono text-xs whitespace-nowrap">{s.admission_code}</td>
                    <td className="whitespace-nowrap">
                      <Link href={`/students/${s.id}`} className="text-brand-700 hover:underline">
                        {s.full_name}
                      </Link>
                    </td>
                    <td>{s.gender}</td>
                    <td className="text-slate-500">{s.date_of_birth}</td>
                    <td><Badge value={s.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* pagination */}
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-slate-100 text-xs text-slate-500">
          <button
            className="btn-secondary !py-1"
            disabled={offset === 0 || loading}
            onClick={() => setOffset(Math.max(0, offset - limit))}
          >
            ← Prev
          </button>
          <span>
            {total === null ? "…" : `${offset + 1}–${Math.min(offset + limit, total)} of ${total}`}
          </span>
          <button
            className="btn-secondary !py-1"
            disabled={loading || total === null || offset + limit >= total}
            onClick={() => setOffset(offset + limit)}
          >
            Next →
          </button>
        </div>
      </Panel>
    </>
  );
}
