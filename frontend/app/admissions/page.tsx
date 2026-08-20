"use client";

/** Admission wizard (journey J1): create student → create guardian → link → enroll. */
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { ErrorBanner, Field, PageHeader, Panel } from "../components/ui";
import { api } from "../lib/api";
import { useSession } from "../lib/session";

const STEPS = ["Student", "Guardian", "Link & enroll"];

export default function AdmissionsPage() {
  const { me } = useSession();
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // step 1 form
  const [surname, setSurname] = useState("");
  const [otherNames, setOtherNames] = useState("");
  const [gender, setGender] = useState<"F" | "M">("F");
  const [dob, setDob] = useState("");
  const [studentId, setStudentId] = useState<string | null>(null);
  const [admissionCode, setAdmissionCode] = useState<string | null>(null);

  // step 2 form
  const [gName, setGName] = useState("");
  const [gPhone, setGPhone] = useState("");
  const [gRelation, setGRelation] = useState("MOTHER");
  const [gDigitalAddress, setGDigitalAddress] = useState("");
  const [guardianId, setGuardianId] = useState<string | null>(null);

  // step 3
  const [streams, setStreams] = useState<{ id: string; name: string }[]>([]);
  const [streamId, setStreamId] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    api<{ items: { id: string; name: string }[] }>("/classes/streams")
      .then((r) => setStreams(r.items))
      .catch(() => {});
  }, []);

  const createStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const r = await api("/students", {
        method: "POST",
        body: { surname, other_names: otherNames, gender, date_of_birth: dob, admit: true },
      });
      setStudentId(r.id);
      setAdmissionCode(r.admission_code);
      setStep(1);
    } catch (err: any) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  const createGuardian = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const r = await api("/parents", {
        method: "POST",
        body: {
          name: gName, phone: gPhone,
          ghana_digital_address: gDigitalAddress || undefined,
        },
      });
      setGuardianId(r.id);
      // link immediately (explicit, audited)
      await api(`/parents/${r.id}/links`, {
        method: "POST",
        body: { student_id: studentId, relationship_type: gRelation,
                is_primary_contact: true, is_billing_contact: true },
      });
      setStep(2);
    } catch (err: any) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  const enroll = async () => {
    if (!streamId) return;
    setBusy(true); setError(null);
    try {
      await api("/enrollments", {
        method: "POST",
        body: { student_id: studentId, class_stream_id: streamId },
      });
      setDone(true);
    } catch (err: any) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  return (
    <>
      <PageHeader title="New admission" subtitle="Create student → assign guardian → enroll into class" />
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}

      <ol className="mb-4 flex gap-4 text-xs font-medium">
        {STEPS.map((s, i) => (
          <li key={s} className={`flex items-center gap-1.5 ${i === step ? "text-brand-700" : i < step ? "text-emerald-600" : "text-slate-400"}`}>
            <span className={`inline-flex h-5 w-5 items-center justify-center rounded-full border text-[11px] ${i <= step ? "border-current" : ""}`}>
              {i < step ? "✓" : i + 1}
            </span>
            {s}
          </li>
        ))}
      </ol>

      {done ? (
        <Panel title="Admission complete">
          <div className="px-4 py-6 text-sm text-slate-700">
            <p>
              <strong>{admissionCode}</strong> has been admitted, linked to their guardian and
              enrolled. The enrollment is now the formal record for this academic year.
            </p>
            <div className="mt-4 flex gap-2">
              <Link href={`/students/${studentId}`} className="btn-primary">Open student record</Link>
              <button className="btn-secondary" onClick={() => window.location.reload()}>
                Admit another
              </button>
            </div>
          </div>
        </Panel>
      ) : step === 0 ? (
        <Panel title="1 · Student biodata">
          <form onSubmit={createStudent} className="grid gap-4 px-4 py-4 sm:grid-cols-2">
            <Field label="Surname"><input className="input" value={surname} onChange={(e) => setSurname(e.target.value)} required /></Field>
            <Field label="Other names"><input className="input" value={otherNames} onChange={(e) => setOtherNames(e.target.value)} required /></Field>
            <Field label="Gender">
              <select className="input" value={gender} onChange={(e) => setGender(e.target.value as "F" | "M")}>
                <option value="F">Female</option><option value="M">Male</option>
              </select>
            </Field>
            <Field label="Date of birth"><input type="date" className="input" value={dob} onChange={(e) => setDob(e.target.value)} required /></Field>
            <div className="sm:col-span-2">
              <button className="btn-primary" disabled={busy}>{busy ? "Saving…" : "Create & admit"}</button>
            </div>
          </form>
        </Panel>
      ) : step === 1 ? (
        <Panel title={`2 · Parent/guardian for ${admissionCode}`}>
          <form onSubmit={createGuardian} className="grid gap-4 px-4 py-4 sm:grid-cols-2">
            <Field label="Full name"><input className="input" value={gName} onChange={(e) => setGName(e.target.value)} required /></Field>
            <Field label="Phone" hint="Any Ghanaian format; normalized to +233…">
              <input className="input" placeholder="0241234567" value={gPhone} onChange={(e) => setGPhone(e.target.value)} required />
            </Field>
            <Field label="Relationship">
              <select className="input" value={gRelation} onChange={(e) => setGRelation(e.target.value)}>
                {["MOTHER", "FATHER", "GUARDIAN", "GRANDPARENT", "OTHER"].map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </Field>
            <Field label="Ghana Digital Address (optional)" hint="Distinct from GPS coordinates">
              <input className="input" placeholder="GA-123-4567" value={gDigitalAddress} onChange={(e) => setGDigitalAddress(e.target.value)} />
            </Field>
            <div className="sm:col-span-2">
              <button className="btn-primary" disabled={busy}>{busy ? "Saving…" : "Create guardian & link"}</button>
            </div>
          </form>
        </Panel>
      ) : (
        <Panel title={`3 · Enroll ${admissionCode} into a class`}>
          <div className="grid gap-4 px-4 py-4 sm:grid-cols-2">
            <Field label="Class stream">
              <select className="input" value={streamId} onChange={(e) => setStreamId(e.target.value)}>
                <option value="">Select class…</option>
                {streams.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </Field>
            <div className="flex items-end">
              <button className="btn-primary" disabled={!streamId || busy} onClick={enroll}>
                {busy ? "Enrolling…" : "Enroll"}
              </button>
            </div>
          </div>
        </Panel>
      )}
    </>
  );
}
