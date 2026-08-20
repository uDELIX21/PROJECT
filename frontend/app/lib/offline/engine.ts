/** Pure sync-engine logic (unit-tested, no browser APIs) — design §09.
 *
 * States per mutation: PENDING → SYNCED | FAILED | CONFLICT. Conflicts surface
 * the server value and resolve by explicit user choice; nothing is silently lost. */

export type MutationStatus = "PENDING" | "SYNCED" | "FAILED" | "CONFLICT";
export type EntityType = "ASSESSMENT_SCORE" | "ATTENDANCE_RECORD";

export interface OutboxItem {
  client_mutation_id: string;
  entity_type: EntityType;
  entity_ref: string;
  base_version: number | null;
  payload: Record<string, unknown>;
  status: MutationStatus;
  attempts: number;
  updated_at: number;
  result?: { code?: string; message?: string; details?: any };
}

export interface ApiMutationResult {
  client_mutation_id: string;
  status: "APPLIED" | "REJECTED" | "CONFLICT";
  result: { server_version?: number; server_value?: number | null; applied_value?: number | null;
            sheet_id?: string; code?: string; message?: string; details?: any };
  replayed: boolean;
}

let counter = 0;
export function newMutationId(): string {
  // crypto.randomUUID when available; deterministic fallback for tests
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  counter += 1;
  return `mut-${Date.now()}-${counter}`;
}

export function makeScoreMutation(assessmentId: string, enrollmentId: string,
                                  rawScore: number | null, baseVersion: number | null,
                                  isAbsent = false): OutboxItem {
  return {
    client_mutation_id: newMutationId(),
    entity_type: "ASSESSMENT_SCORE",
    entity_ref: `assessment=${assessmentId};enrollment=${enrollmentId}`,
    base_version: baseVersion,
    payload: { assessment_id: assessmentId, enrollment_id: enrollmentId,
               raw_score: rawScore, is_absent: isAbsent },
    status: "PENDING", attempts: 0, updated_at: Date.now(),
  };
}

export function makeAttendanceMutation(streamId: string, termId: string, sheetDate: string,
                                       enrollmentId: string, status: string,
                                       baseVersion: number | null, note?: string): OutboxItem {
  return {
    client_mutation_id: newMutationId(),
    entity_type: "ATTENDANCE_RECORD",
    entity_ref: `stream=${streamId};date=${sheetDate};enrollment=${enrollmentId}`,
    base_version: baseVersion,
    payload: { class_stream_id: streamId, term_id: termId, sheet_date: sheetDate,
               enrollment_id: enrollmentId, status, note },
    status: "PENDING", attempts: 0, updated_at: Date.now(),
  };
}

/** Apply the server's per-mutation verdict to the local queue item. */
export function classifyResult(item: OutboxItem, api: ApiMutationResult): OutboxItem {
  if (api.status === "APPLIED") {
    return { ...item, status: "SYNCED", attempts: item.attempts + 1,
             result: api.result, updated_at: Date.now() };
  }
  if (api.status === "CONFLICT") {
    return { ...item, status: "CONFLICT", attempts: item.attempts + 1,
             result: api.result, updated_at: Date.now() };
  }
  return { ...item, status: "FAILED", attempts: item.attempts + 1,
           result: api.result, updated_at: Date.now() };
}

/** Transport-level failure (offline / 5xx / network error). */
export function markTransportFailed(item: OutboxItem, message: string): OutboxItem {
  return { ...item, status: "FAILED", attempts: item.attempts + 1,
           result: { code: "TRANSPORT", message }, updated_at: Date.now() };
}

export type ConflictChoice = "KEEP_MINE" | "TAKE_SERVER";

/** Resolve a CONFLICT item. KEEP_MINE re-queues against the server's current
 *  version (the server re-validates); TAKE_SERVER drops the local value. */
export function resolveConflict(item: OutboxItem, choice: ConflictChoice,
                                serverVersion: number | null): OutboxItem | null {
  if (choice === "TAKE_SERVER") return null; // remove from queue; UI adopts server value
  return { ...item, status: "PENDING",
           base_version: serverVersion ?? item.base_version, updated_at: Date.now() };
}

export interface QueueSummary { pending: number; synced: number; failed: number; conflict: number }

export function summarize(items: OutboxItem[]): QueueSummary {
  const s: QueueSummary = { pending: 0, synced: 0, failed: 0, conflict: 0 };
  for (const i of items) {
    if (i.status === "PENDING") s.pending += 1;
    else if (i.status === "SYNCED") s.synced += 1;
    else if (i.status === "CONFLICT") s.conflict += 1;
    else s.failed += 1;
  }
  return s;
}

/** Latest mutation per entity_ref wins when building the UI state. */
export function latestByRef(items: OutboxItem[]): Map<string, OutboxItem> {
  const m = new Map<string, OutboxItem>();
  for (const i of items) {
    const cur = m.get(i.entity_ref);
    if (!cur || i.updated_at >= cur.updated_at) m.set(i.entity_ref, i);
  }
  return m;
}

/** Cap the retained SYNCED history so the store never grows unbounded. */
export function pruneSynced(items: OutboxItem[], keep = 200): OutboxItem[] {
  const active = items.filter((i) => i.status !== "SYNCED");
  const synced = items.filter((i) => i.status === "SYNCED")
    .sort((a, b) => b.updated_at - a.updated_at).slice(0, keep);
  return [...active, ...synced];
}
