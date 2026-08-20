"use client";

import React, { useEffect, useState } from "react";
import { Badge, ErrorBanner, Field, Loading, PageHeader, Panel } from "../components/ui";
import { api } from "../lib/api";
import { useSession } from "../lib/session";

interface YearRow { id: string; name: string; starts_on: string; ends_on: string; status: string }
interface TermRow { id: string; name: string; starts_on: string; ends_on: string; status: string }

export default function SettingsPage() {
  const { me, refresh } = useSession();
  const [school, setSchool] = useState<any>(null);
  const [years, setYears] = useState<YearRow[]>([]);
  const [terms, setTerms] = useState<TermRow[]>([]);
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [motto, setMotto] = useState("");
  const [digitalAddress, setDigitalAddress] = useState("");

  useEffect(() => {
    Promise.all([api("/school"), api("/settings/academic-years")])
      .then(([s, y]: any) => {
        setSchool(s); setName(s.name); setMotto(s.motto ?? ""); setDigitalAddress(s.ghana_digital_address ?? "");
        setYears(y.items);
        const active = y.items.find((r: YearRow) => r.status === "ACTIVE");
        setSelectedYear(active?.id ?? y.items[0]?.id ?? "");
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!selectedYear) return;
    api(`/settings/academic-years/${selectedYear}/terms`)
      .then((r: any) => setTerms(r.items))
      .catch((e) => setError(e.message));
  }, [selectedYear]);

  const saveSchool = async (e: React.FormEvent) => {
    e.preventDefault(); setError(null); setNotice(null);
    try {
      await api("/school", { method: "PATCH", body: {
        name, motto: motto || null, ghana_digital_address: digitalAddress || null } });
      setNotice("School profile saved (audited).");
      refresh();
    } catch (err: any) { setError(err.message); }
  };

  const termAction = async (termId: string, action: string, reason?: string) => {
    setError(null); setNotice(null);
    try {
      const body = reason ? { reason } : undefined;
      await api(`/settings/terms/${termId}/${action}`, { method: "POST", body });
      setNotice(`Term ${action} succeeded.`);
      const r: any = await api(`/settings/academic-years/${selectedYear}/terms`);
      setTerms(r.items);
      refresh();
    } catch (err: any) { setError(err.message); }
  };

  if (!school) return <Loading />;

  return (
    <>
      <PageHeader title="Settings" subtitle="School profile, academic calendar and terms" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {notice && (
        <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{notice}</div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="School profile">
          <form onSubmit={saveSchool} className="grid gap-4 px-4 py-4">
            <Field label="School name"><input className="input" value={name} onChange={(e) => setName(e.target.value)} required /></Field>
            <Field label="Motto"><input className="input" value={motto} onChange={(e) => setMotto(e.target.value)} /></Field>
            <Field label="Ghana Digital Address" hint="Not the same as GPS coordinates">
              <input className="input" value={digitalAddress} onChange={(e) => setDigitalAddress(e.target.value)} />
            </Field>
            <div><button className="btn-primary">Save profile</button></div>
          </form>
        </Panel>

        <Panel
          title="Academic years & terms"
          right={
            <select className="input !w-auto !py-1" value={selectedYear}
                    onChange={(e) => setSelectedYear(e.target.value)}>
              {years.map((y) => (
                <option key={y.id} value={y.id}>{y.name} ({y.status.toLowerCase()})</option>
              ))}
            </select>
          }
        >
          {terms.length === 0 ? (
            <p className="px-4 py-4 text-sm text-slate-500">No terms defined for this year.</p>
          ) : (
            <table className="tbl">
              <thead>
                <tr><th>Term</th><th>Dates</th><th>Status</th><th></th></tr>
              </thead>
              <tbody>
                {terms.map((t) => (
                  <tr key={t.id}>
                    <td className="font-medium">{t.name}</td>
                    <td className="text-xs text-slate-500 whitespace-nowrap">{t.starts_on} → {t.ends_on}</td>
                    <td><Badge value={t.status} /></td>
                    <td className="text-right space-x-1 whitespace-nowrap">
                      {t.status === "DRAFT" && (
                        <button className="btn-secondary !py-1" onClick={() => termAction(t.id, "activate")}>Activate</button>
                      )}
                      {t.status === "ACTIVE" && (
                        <button className="btn-secondary !py-1" onClick={() => termAction(t.id, "close")}>Close term</button>
                      )}
                      {t.status === "CLOSED" && (
                        <button className="btn-secondary !py-1" onClick={() => {
                          const reason = window.prompt("Reason for reopening this closed term? (audited)");
                          if (reason && reason.trim().length >= 5) termAction(t.id, "reopen", reason.trim());
                        }}>Reopen…</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="px-4 py-2 text-xs text-slate-400 border-t border-slate-100">
            Closing a term locks academic records for it; reopening requires a reason and is audited (BR-A02).
          </p>
        </Panel>
      </div>
    </>
  );
}
