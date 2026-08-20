/** Shared lookups for the academic pages. */
import { api } from "./api";

export interface YearInfo { id: string; name: string; status: string }
export interface TermInfo { id: string; name: string; status: string; academic_year_id: string }
export interface StreamInfo { id: string; name: string; grade: { id: string; code: string; name: string; band: string }; academic_year_id: string }
export interface SubjectInfo { id: string; code: string; name: string }
export interface RosterItem { id: string; admission_code: string; full_name: string; gender: string; enrollment: { id: string } }

export async function activeContext() {
  const years = await api<{ items: YearInfo[] }>("/settings/academic-years");
  const year = years.items.find((y) => y.status === "ACTIVE") ?? years.items[0];
  const terms = year
    ? await api<{ items: TermInfo[] }>(`/settings/academic-years/${year.id}/terms`)
    : { items: [] as TermInfo[] };
  const term = terms.items.find((t) => t.status === "ACTIVE") ?? terms.items[0];
  return { years: years.items, year, terms: terms.items, term };
}

export async function streamsFor(yearId: string) {
  const r = await api<{ items: StreamInfo[] }>(`/classes/streams?academic_year_id=${yearId}`);
  return r.items;
}

export async function rosterFor(streamId: string) {
  const r = await api<{ items: RosterItem[] }>(`/classes/streams/${streamId}/roster`);
  return r.items;
}

export async function subjectsForGrade(gradeId: string) {
  const r = await api<{ items: SubjectInfo[] }>(`/classes/grades/${gradeId}/subjects`);
  return r.items;
}
