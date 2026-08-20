"use client";

/** Authorized pickup overview for early childhood (REQ-PKU-01). */
import React, { useEffect, useState } from "react";
import { ErrorBanner, Loading, PageHeader, Panel, Badge } from "../components/ui";
import { api, ApiClientError } from "../lib/api";
import { useSession } from "../lib/session";

export default function PickupPage() {
  const { me } = useSession();
  const [rows, setRows] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const reload = async () => {
    try { setRows((await api("/pickup/early-childhood")).items); }
    catch (e) { if (e instanceof ApiClientError && e.status !== 403) setError(e.message); }
  };

  useEffect(() => { if (me) reload(); /* eslint-disable-line */ }, [me]);

  const revoke = async (id: string) => {
    const reason = window.prompt("Reason for revoking this pickup authorization (audited):");
    if (!reason || reason.trim().length < 5) return;
    setError(null);
    try {
      await api(`/pickup/${id}/revoke`, { method: "POST", body: { reason: reason.trim() } });
      setNotice("Authorization revoked (audited).");
      reload();
    } catch (e) { setError(e instanceof ApiClientError ? e.message : "Failed."); }
  };

  if (!me) return <Loading />;

  return (
    <>
      <PageHeader title="Authorized pickup"
        subtitle="Early childhood — who may collect each child; creator and expiry tracked" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>}
      <p className="mb-3 text-xs text-slate-500">
        Add new authorizations from a student's profile page (Early childhood section).
      </p>

      {rows.length === 0 ? (
        <Panel><p className="px-4 py-6 text-sm text-slate-500">No early-childhood enrollments found.</p></Panel>
      ) : (
        <Panel title={`${rows.length} children`}>
          <table className="tbl">
            <thead><tr><th>Child</th><th>Authorized persons</th></tr></thead>
            <tbody>
              {rows.map((k) => (
                <tr key={k.student_id}>
                  <td className="whitespace-nowrap">{k.student_name}</td>
                  <td>
                    {k.authorizations.length === 0 ? (
                      <span className="text-xs text-slate-400">none recorded</span>
                    ) : (
                      <div className="space-y-1">
                        {k.authorizations.map((a: any) => (
                          <div key={a.id} className="flex items-center gap-2 text-sm">
                            <span>{a.person_name}</span>
                            <span className="font-mono text-xs text-slate-400">{a.phone}</span>
                            <Badge value={a.status} />
                            {a.status === "ACTIVE" && (
                              <button className="btn-secondary !py-0.5 !px-2 text-xs"
                                onClick={() => revoke(a.id)}>Revoke</button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}
    </>
  );
}
