"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { PageHeader, Panel, EmptyState, Loading } from "./components/ui";
import { api, isAuthError } from "./lib/api";
import { hasPerm, useSession } from "./lib/session";

interface StudentRow {
  id: string;
  admission_code: string;
  full_name: string;
  gender: string;
  status: string;
}

export default function Dashboard() {
  const { me } = useSession();
  const [rows, setRows] = useState<StudentRow[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!me || !hasPerm(me, "VIEW_STUDENT")) return;
    api(`/students?limit=8`)
      .then((r) => {
        setRows(r.items);
        setTotal(r.total);
      })
      .catch((e) => {
        if (!isAuthError(e)) setError(e.message ?? "Failed to load students.");
      });
  }, [me]);

  if (!me) return null;

  return (
    <>
      <PageHeader
        title={`Welcome, ${me.user.display_name ?? me.user.username}`}
        subtitle={`${me.school.name} · ${me.active_year?.name ?? "—"}${
          me.active_term ? ` · ${me.active_term.name}` : ""
        }`}
      />

      <div className="space-y-4">
        <Panel
          title="Students"
          right={
            hasPerm(me, "VIEW_STUDENT") ? (
              <Link href="/students" className="text-xs text-brand-700 hover:underline">
                View all →
              </Link>
            ) : undefined
          }
        >
          {!hasPerm(me, "VIEW_STUDENT") ? (
            <EmptyState
              title="No student records available"
              hint="Your role does not include student visibility."
            />
          ) : rows === null ? (
            <Loading />
          ) : rows.length === 0 ? (
            <EmptyState title="No students yet" hint="Admit your first student to get started." />
          ) : (
            <table className="tbl">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Gender</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr key={s.id}>
                    <td className="font-mono text-xs">{s.admission_code}</td>
                    <td>
                      <Link href={`/students/${s.id}`} className="text-brand-700 hover:underline">
                        {s.full_name}
                      </Link>
                    </td>
                    <td>{s.gender}</td>
                    <td>{s.status.replaceAll("_", " ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {rows !== null && (
            <p className="px-4 py-2 text-xs text-slate-400 border-t border-slate-100">
              Showing {rows.length} of {total}
            </p>
          )}
        </Panel>

        <Panel title="Quick actions">
          <div className="flex flex-wrap gap-2 px-4 py-3">
            {hasPerm(me, "EDIT_STUDENT") && (
              <Link href="/admissions" className="btn-primary">New admission</Link>
            )}
            {hasPerm(me, "VIEW_STUDENT") && (
              <Link href="/students" className="btn-secondary">Student registry</Link>
            )}
            {hasPerm(me, "MANAGE_SETTINGS") && (
              <Link href="/settings" className="btn-secondary">School settings</Link>
            )}
          </div>
          <p className="px-4 pb-3 text-xs text-slate-400">
            Phase 3 scope: registry, enrollment & promotion. Assessment, finance and reports
            modules follow in Phases 4–5.
          </p>
        </Panel>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    </>
  );
}
