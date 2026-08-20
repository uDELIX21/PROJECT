# 09 · Offline Synchronization & Low-Bandwidth Architecture

**Status:** Draft for approval · **Covers:** deliverable item 16 (+ spec §33 low bandwidth)

---

## 1. Design goals & rules

- Teacher marks & attendance entry must survive connectivity loss **without data loss** (REQ-OFF-01..03).
- **LocalStorage is not used for data** — only non-sensitive UI prefs (Agent Rule 10). All offline data lives in **IndexedDB**; Service Worker handles caching & background sync.
- Every queued mutation gets an explicit terminal UI state: **Synced / Pending / Failed / Conflict** (REQ-OFF-02).

## 2. Client architecture (Next.js PWA)

```
UI (React Server Components for reads; client islands for entry)
 ├─ offline-store (IndexedDB via Dexie.js)
 │    ├─ drafts        {sheetId, scores…, version, updatedAt}     // working copy
 │    ├─ outbox        {mutationId(UUID), op, payload, status, attempts, lastError}
 │    ├─ rosterCache   {classStreamId, students[]}                // names for offline entry
 │    └─ syncMeta      {lastSyncAt, per-sheet server versions}
 ├─ sync-engine (TS service)
 │    ├─ enqueue(mut) → outbox ; broadcast state → UI badge
 │    ├─ flush(): while online: POST /api/v1/sync/mutations (batch ≤ 20)
 │    └─ retry: exponential backoff (2s→4s→…→5min cap), jitter; network events re-trigger
 └─ Service Worker (Workbox)
      ├─ precache: app shell (JS/CSS/fonts) — entry pages fully usable offline
      ├─ runtime: GET API lists → stale-while-revalidate + IndexedDB mirror
      └─ background sync: 'sync-outbox' tag fires on reconnect
```

- **PWA manifest:** installable, `display: standalone`, offline fallback page; bundle budget: entry route < 170 KB gz JS (REQ-LOW-02).
- Online/offline detection: `navigator.onLine` + heartbeat probe (`/healthz`) — never trust only browser events.

## 3. Server-side sync contract

`POST /api/v1/sync/mutations` — batch endpoint, per mutation:

```json
{ "client_mutation_id": "uuid", "entity_type": "ASSESSMENT_SCORE",
  "entity_ref": "assessment=<id>;enrollment=<id>", "base_version": 7,
  "payload": { "raw_score": 82, "is_absent": false } }
```

Per-mutation processing (all in `sync_mutations` ledger, REQ-OFF-03):
1. **Idempotency:** `client_mutation_id` unique → replay returns stored result (no double apply).
2. **Authorization:** same guards as the direct API (assignment scope, term active, sheet not LOCKED) — rejected mutations return status `REJECTED` with error code; client shows **Sync failed** with reason (never retried automatically for 4xx).
3. **Conflict detection:** `base_version` vs current row `version` (optimistic concurrency on `assessments`/`assessment_scores`/`attendance_records`). Mismatch ⇒ `CONFLICT` with server's current value; client prompts the teacher: *keep mine / take server / merge per field*. No silent overwrite (REQ-OFF-02).
4. Success ⇒ row applied, `version+1`, response `APPLIED`; client marks Synced + updates `syncMeta`.

## 4. Scope & limits (v1)

| Write-capable offline | Read-cached offline | Not offline (v1) |
|---|---|---|
| Mark sheet scores, absence flags | Rosters, scheme/component config, own class lists, curriculum tree | Finance, imports, settings, report generation |
| Attendance sheets | Recent attendance history | Appraisals/discipline writes |

Offline drafts are keyed per sheet so two devices for the same teacher reconcile via the same outbox rules (last-write per field with conflict prompt).

## 5. Low-bandwidth measures (REQ-LOW-01..02, cross-cutting)

- Cursor pagination everywhere; list payloads are flat summaries (detail on demand).
- `fields=` sparse responses + gzip/brotli; ETags on config endpoints (`/meta/bootstrap`, schemes, templates) cached by SW.
- Images: server-side compression on upload (photos resized ≤ 512px WebP); logos/signatures served pre-sized.
- Route-level code splitting; no heavyweight chart libs (inline SVG sparklines).
- Background prefetch of next-term rosters only when `navigator.connection.effectiveType` ≥ '3g'.
- Long jobs (report batches, billing runs, imports) are async with polling/progress — no 60 s+ requests.

## 6. Testing posture (feeds §14 test plan)

- Unit: sync-engine state machine, backoff, batching.
- Integration (Playwright): airplane-mode injection → enter marks → reconnect → assert server rows + UI state; duplicate replay; concurrent-edit conflict; locked-sheet rejection.
- Property tests: mutation replay idempotency (1000 random ops).
