# Manual E2E checklist (browser journeys)

Automated browser tests live in `backend/tests/e2e/` (Playwright). Where a
browser cannot be installed (restricted sandboxes), run this checklist
manually against the dev servers:

```bash
cd backend && DATABASE_URL=sqlite:///./dev.db ../.venv/bin/python scripts/seed.py --reset
SMS_STORAGE_DIR=./storage DATABASE_URL=sqlite:///./dev.db \
  ../.venv/bin/uvicorn app.main:app --port 8000
cd frontend && npm run dev -- -p 3000
```

| # | Journey | Steps | Expected |
|---|---------|-------|----------|
| J1 | Enrollment | admin → New admission wizard → create student → guardian → enroll | Student ACTIVE, visible in registry, guardian linked |
| J2 | Mark entry | teacher → Marks entry → pick assigned class → enter scores → submit | Rows show ✓ synced; sheet SUBMITTED; edits blocked (423) |
| J3 | Grade correction | teacher requests correction → head approves | Score updated; audit shows original→new + reason |
| J4 | Report card | head → Reports → generate → finalize → publish (blocked if BLOCKED) | PDF downloads; parent sees published only |
| J5 | Payment | bursar → Finance → initiate MoMo → POST signed webhook | Ledger credit + receipt; duplicate webhook no-op |
| J6 | CSV import | admin → Imports → upload template data → preview → resolve match → confirm | Atomic commit; history entry; linked guardian |
| J7 | Offline marks | teacher → Marks entry → DevTools → Network → Offline → edit scores → reconnect | Badge: Offline → Syncing → Synced; scores persist |
| J8 | Permission boundary | teacherB tries teacherA's class roster | Uniform 404; nothing leaks |
| J9 | Offline sync conflict | edit sheet on 2 devices; sync both | Conflict panel with Keep mine / Take server |

Sync-state UI requirements (REQ-OFF-02): the SyncBadge must show
**Synced / Syncing n… / n conflict(s) / n failed** and never lose an entry
(verify with DevTools → Application → IndexedDB → `sms-offline/outbox`).
