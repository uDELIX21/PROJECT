/** Unit tests for the pure sync-engine logic. */
import { describe, expect, it } from "vitest";
import {
  classifyResult, latestByRef, makeAttendanceMutation, makeScoreMutation,
  markTransportFailed, pruneSynced, resolveConflict, summarize,
  type ApiMutationResult,
} from "./engine";

describe("mutation builders", () => {
  it("builds score mutations with refs and versions", () => {
    const m = makeScoreMutation("a1", "e1", 75, 3);
    expect(m.entity_type).toBe("ASSESSMENT_SCORE");
    expect(m.entity_ref).toBe("assessment=a1;enrollment=e1");
    expect(m.base_version).toBe(3);
    expect(m.status).toBe("PENDING");
    expect(m.payload.raw_score).toBe(75);
  });

  it("builds attendance mutations", () => {
    const m = makeAttendanceMutation("s1", "t1", "2026-09-21", "e1", "LATE", null, "bus");
    expect(m.entity_type).toBe("ATTENDANCE_RECORD");
    expect(m.payload.status).toBe("LATE");
  });
});

describe("classifyResult", () => {
  const base = makeScoreMutation("a", "e", 50, 1);

  it("APPLIED → SYNCED", () => {
    const api: ApiMutationResult = { client_mutation_id: base.client_mutation_id,
      status: "APPLIED", result: { server_version: 4 }, replayed: false };
    expect(classifyResult(base, api).status).toBe("SYNCED");
  });

  it("CONFLICT keeps the server details for the resolver", () => {
    const api: ApiMutationResult = { client_mutation_id: base.client_mutation_id,
      status: "CONFLICT", result: { code: "VERSION_CONFLICT",
        details: { server_version: 7, server_value: 60 } }, replayed: false };
    const out = classifyResult(base, api);
    expect(out.status).toBe("CONFLICT");
    expect(out.result?.details?.server_value).toBe(60);
  });

  it("REJECTED → FAILED with the server reason", () => {
    const api: ApiMutationResult = { client_mutation_id: base.client_mutation_id,
      status: "REJECTED", result: { code: "MARKS_LOCKED", message: "locked" }, replayed: false };
    const out = classifyResult(base, api);
    expect(out.status).toBe("FAILED");
    expect(out.result?.code).toBe("MARKS_LOCKED");
  });
});

describe("conflict resolution", () => {
  const conflicted = { ...makeScoreMutation("a", "e", 99, 1), status: "CONFLICT" as const };

  it("KEEP_MINE requeues against the server version", () => {
    const next = resolveConflict(conflicted, "KEEP_MINE", 9);
    expect(next?.status).toBe("PENDING");
    expect(next?.base_version).toBe(9);
  });

  it("TAKE_SERVER drops the mutation", () => {
    expect(resolveConflict(conflicted, "TAKE_SERVER", 9)).toBeNull();
  });
});

describe("queue bookkeeping", () => {
  it("summarizes states", () => {
    const items = [
      { ...makeScoreMutation("a", "1", 1, null), status: "PENDING" as const },
      { ...makeScoreMutation("a", "2", 2, null), status: "SYNCED" as const },
      { ...makeScoreMutation("a", "3", 3, null), status: "FAILED" as const },
      { ...makeScoreMutation("a", "4", 4, null), status: "CONFLICT" as const },
    ];
    expect(summarize(items)).toEqual({ pending: 1, synced: 1, failed: 1, conflict: 1 });
  });

  it("latestByRef keeps the newest mutation per entity", () => {
    const older = { ...makeScoreMutation("a", "1", 1, null), updated_at: 100 };
    const newer = { ...older, client_mutation_id: "other", payload: { raw_score: 9 }, updated_at: 200 };
    const m = latestByRef([older, newer]);
    expect(m.get("assessment=a;enrollment=1")?.payload.raw_score).toBe(9);
  });

  it("pruneSynced caps history but keeps active items", () => {
    const active = [{ ...makeScoreMutation("a", "x", 1, null), status: "CONFLICT" as const }];
    const synced = Array.from({ length: 300 }, (_, i) => ({
      ...makeScoreMutation("a", `s${i}`, 1, null), status: "SYNCED" as const, updated_at: i }));
    const out = pruneSynced([...active, ...synced], 200);
    expect(out.filter((i) => i.status === "SYNCED")).toHaveLength(200);
    expect(out.some((i) => i.status === "CONFLICT")).toBe(true);
  });

  it("transport failure marks retryable FAILED", () => {
    const item = makeScoreMutation("a", "e", 5, null);
    const out = markTransportFailed(item, "offline");
    expect(out.status).toBe("FAILED");
    expect(out.result?.code).toBe("TRANSPORT");
  });
});
