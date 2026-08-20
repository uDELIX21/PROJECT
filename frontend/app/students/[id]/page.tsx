"use client";

import { useParams } from "next/navigation";
import React, { useCallback, useEffect, useState } from "react";
import {
  Badge, ConfirmDialog, ErrorBanner, Field, Loading, PageHeader, Panel,
} from "../../components/ui";
import { api, ApiClientError } from "../../lib/api";
import { hasPerm, useSession } from "../../lib/session";

interface Student {
  id: string; admission_code: string; full_name: string; surname: string;
  other_names: string; gender: string; date_of_birth: string; status: string;
  nationality?: string; religion?: string; admitted_on?: string | null;
}
interface GuardianLink {
  id: string; relationship_type: string; is_primary_contact: boolean;
  parent: { id: string; name: string; phone: string; email?: string | null };
}
interface Enrollment {
  id: string; stream_name: string; status: string; is_repeat: boolean;
  started_on?: string; ended_on?: string;
}

const fmtGhs = (p: number) => `GH¢ ${(p / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

const STATUS_ACTIONS: Record<string, string[]> = {
  APPLICANT: ["ADMITTED", "WITHDRAWN"],
  ADMITTED: ["WITHDRAWN"],
  ENROLLED: ["ACTIVE", "WITHDRAWN", "TRANSFERRED", "SUSPENDED"],
  ACTIVE: ["WITHDRAWN", "TRANSFERRED", "SUSPENDED", "GRADUATED"],
  SUSPENDED: ["ACTIVE", "WITHDRAWN", "TRANSFERRED"],
  WITHDRAWN: ["APPLICANT"],
};

export default function StudentDetail() {
  const { id } = useParams<{ id: string }>();
  const { me } = useSession();
  const [student, setStudent] = useState<Student | null>(null);
  const [guardians, setGuardians] = useState<GuardianLink[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [finance, setFinance] = useState<{ balance_pesewas: number } | null>(null);
  const [streams, setStreams] = useState<{ id: string; name: string }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirm, setConfirm] = useState<{ status: string } | null>(null);
  const [enrollStream, setEnrollStream] = useState("");

  const load = useCallback(async () => {
    try {
      const [s, g, e] = await Promise.all([
        api<Student>(`/students/${id}`),
        api<{ items: GuardianLink[] }>(`/students/${id}/guardians`),
        api<{ items: Enrollment[] }>(`/students/${id}/enrollments`),
      ]);
      setStudent(s);
      setGuardians(g.items);
      setEnrollments(e.items);
      if (hasPerm(me, "MANAGE_ENROLLMENT")) {
        const st = await api<{ items: { id: string; name: string }[] }>("/classes/streams");
        setStreams(st.items);
      }
      if (hasPerm(me, "VIEW_FINANCE")) {
        api(`/fees/balances?student_id=${id}`)
          .then((r) => setFinance({ balance_pesewas: r.balance_pesewas }))
          .catch(() => setFinance(null));
      }
    } catch (e: any) {
      setError(e instanceof ApiClientError ? e.message : "Failed to load student.");
    } finally {
      setLoading(false);
    }
  }, [id, me]);

  useEffect(() => { if (me) load(); }, [me, load]);

  const changeStatus = async (status: string) => {
    try {
      await api(`/students/${id}/status`, { method: "POST", body: { status } });
      setNotice(`Status changed to ${status}.`);
      setConfirm(null);
      load();
    } catch (e: any) {
      setError(e.message); setConfirm(null);
    }
  };

  const enroll = async () => {
    if (!enrollStream) return;
    try {
      await api("/enrollments", {
        method: "POST",
        body: { student_id: id, class_stream_id: enrollStream },
      });
      setNotice("Enrollment created.");
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  if (loading) return <Loading />;
  if (!student) return <ErrorBanner message={error ?? "Student not found."} />;

  const actions = STATUS_ACTIONS[student.status] ?? [];

  return (
    <>
      <PageHeader
        title={student.full_name}
        subtitle={`${student.admission_code} · ${student.gender} · born ${student.date_of_birth}`}
        actions={<Badge value={student.status} />}
      />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && (
        <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">
          {notice}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Biodata">
          <dl className="px-4 py-3 text-sm space-y-1.5">
            <Row k="Admission code" v={student.admission_code} />
            <Row k="Nationality" v={student.nationality ?? "—"} />
            <Row k="Religion" v={student.religion || "—"} />
            <Row k="Admitted" v={student.admitted_on ?? "—"} />
            {finance && (
              <Row k="Fee balance" v={fmtGhs(finance.balance_pesewas)} />
            )}
          </dl>
          {hasPerm(me, "MANAGE_ENROLLMENT") && actions.length > 0 && (
            <div className="flex flex-wrap gap-2 border-t border-slate-100 px-4 py-3">
              {actions.map((a) => (
                <button key={a} className="btn-secondary" onClick={() => setConfirm({ status: a })}>
                  Mark {a.replaceAll("_", " ").toLowerCase()}
                </button>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Guardians">
          {guardians.length === 0 ? (
            <p className="px-4 py-4 text-sm text-slate-500">
              No guardians linked yet. Use the import flow or parent registry to link.
            </p>
          ) : (
            <table className="tbl">
              <thead>
                <tr><th>Name</th><th>Relationship</th><th>Phone</th></tr>
              </thead>
              <tbody>
                {guardians.map((g) => (
                  <tr key={g.id}>
                    <td>{g.parent.name}</td>
                    <td>
                      {g.relationship_type}
                      {g.is_primary_contact && <span className="ml-1 text-xs text-brand-700">(primary)</span>}
                    </td>
                    <td className="font-mono text-xs">{g.parent.phone}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        <Panel title="Enrollment history">
          {enrollments.length === 0 ? (
            <p className="px-4 py-4 text-sm text-slate-500">No enrollments recorded.</p>
          ) : (
            <table className="tbl">
              <thead>
                <tr><th>Class</th><th>Status</th><th>Started</th><th>Ended</th></tr>
              </thead>
              <tbody>
                {enrollments.map((e) => (
                  <tr key={e.id}>
                    <td>{e.stream_name}{e.is_repeat ? " (repeat)" : ""}</td>
                    <td><Badge value={e.status} /></td>
                    <td className="text-slate-500">{e.started_on ?? "—"}</td>
                    <td className="text-slate-500">{e.ended_on ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {hasPerm(me, "MANAGE_ENROLLMENT") &&
            ["ADMITTED", "ENROLLED", "ACTIVE", "PROMOTED", "REPEATED"].includes(student.status) && (
              <div className="flex flex-wrap items-end gap-2 border-t border-slate-100 px-4 py-3">
                <Field label="Enroll into class">
                  <select className="input" value={enrollStream} onChange={(e) => setEnrollStream(e.target.value)}>
                    <option value="">Select class…</option>
                    {streams.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </Field>
                <button className="btn-primary" disabled={!enrollStream} onClick={enroll}>
                  Enroll
                </button>
              </div>
            )}
        </Panel>
      </div>

      <ConfirmDialog
        open={!!confirm}
        title="Confirm status change"
        body={`Change ${student.full_name}'s status to ${confirm?.status}? This transition is validated and audited.`}
        onConfirm={() => confirm && changeStatus(confirm.status)}
        onCancel={() => setConfirm(null)}
      />
    </>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-500">{k}</dt>
      <dd className="font-medium text-slate-800 text-right">{v}</dd>
    </div>
  );
}
