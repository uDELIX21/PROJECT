# PROJECT — School Management Information System (SMS)

Enterprise-grade SMS for a Ghanaian private/missionary school (~700 students, ~20 classes,
Crèche → JHS 3): academics, finance ledger, attendance, report cards, offline teacher entry,
imports, communications — all configurable, audited, and role-scoped.

## Current status

**Phase 10 (Deployment) complete — all 10 phases delivered.** The system is
implemented, tested, and documented end-to-end; ready for a deployment review.

- ✅ **Phase 3 — Core:** auth, RBAC + server-side scoping, registries, enrollments,
  promotion, calendar, audit log, PWA shell.
- ✅ **Phase 4 — Academic engine:** versioned curriculum, configurable assessment schemes,
  mark sheets + audited corrections, grading scales, attendance, ECD assessment, report
  cards (PDF, finalize/publish).
- ✅ **Phase 5 — Financial engine:** append-only ledger, fee structures as config rows,
  idempotent billing, simulated MoMo/Telecel/AT providers with HMAC-verified idempotent
  webhooks, FIFO allocations, immutable receipts, clearance gating publication.
- ✅ **Phase 6 — Operations:** appraisals, restricted discipline records, pickup
  authorizations, SMS provider abstraction (Arkesel/Hubtel + console stub), notifications.
- ✅ **Phase 7 — Offline/PWA:** IndexedDB outbox (never LocalStorage), service-worker
  caching, replay-safe `POST /sync/mutations`, optimistic-concurrency conflict resolution,
  synced/pending/failed/conflict UI states.
- ✅ **Phase 8 — Administration & Imports:** CSV/XLSX pipeline (templates, preview,
  confirmed parent matching — never auto-linked, atomic commit + rollback).
- ✅ **Phase 9 — Testing & hardening:** security sweep (20 endpoints × 5 roles +
  unauthenticated), payment edge suite, ledger invariants, property tests, 5,000-row
  import soak, index query-plan guards, Playwright E2E in CI. **156 backend + 11
  frontend tests passing.**
- ✅ **Phase 10 — Deployment:** production Compose topology (nginx TLS → Next + FastAPI →
  Postgres/Redis, loopback-only stores), `backend/.env.example` production values,
  Alembic migration procedure, seed procedure, **backup/restore scripts (Postgres prod +
  SQLite dev/CI) with checksums + retention (14 daily / 8 weekly / 12 monthly)**,
  quarterly **DR drill script**, troubleshooting table, rollback procedure. DR round-trip
  verified live: corrupted DB (720→0 students) restored to 720, integrity ok.

📐 Design artifact: **[docs/design/README.md](docs/design/README.md)**
🛠 Operations: **[docs/runbooks/deployment.md](docs/runbooks/deployment.md)** · [ops/](ops/)

## Quickstart (dev)

```bash
# backend
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements-dev.txt
cd backend
DATABASE_URL=sqlite:///./dev.db ../.venv/bin/python scripts/seed.py --reset   # full demo
SMS_STORAGE_DIR=./storage DATABASE_URL=sqlite:///./dev.db \
  ../.venv/bin/uvicorn app.main:app --reload --port 8000

# frontend (separate shell)
cd frontend && npm install && npm run dev -- -p 3000
# open http://localhost:3000  (API proxied via Next rewrites)
```

### Demo credentials (fictional data)

| Username | Role | Password (all users) |
|---|---|---|
| `admin` | Super Admin | `Demo#2026accra` |
| `head` | Headteacher | `Demo#2026accra` |
| `bursar` | Bursar | `Demo#2026accra` |
| `teacher1`…`teacher6` | Teacher | `Demo#2026accra` |
| `parent1`, `parent2` | Parent | `Demo#2026accra` |

### Feature notes

- **Imports (P8):** Admin → Imports → download template → upload → preview (errors,
  duplicates, **parent matches needing explicit confirmation**) → atomic confirm.
- **Offline (P7):** marks/attendance queue in IndexedDB offline; SyncBadge shows
  Synced/Syncing/conflicts/failures; conflicts resolve via keep-mine/take-server.
- **Payments (P5):** e-money providers are clearly-labelled stubs;
  `X-Webhook-Signature: HMAC-SHA256(body, $SMS_WEBHOOK_SECRET)` (dev secret
  `dev-webhook-secret`); duplicates/bad signatures never apply.
- **SMS (P6):** `comms.provider` school setting (`CONSOLE` dev stub, `ARKesel`/`HUBTEL`
  live adapters).

### Tests

```bash
cd backend && ../.venv/bin/python -m pytest        # 156 tests (+ browser E2E when available)
cd frontend && npm test                            # 11 vitest tests (sync engine)
```

## Stack

Next.js 16 / React 19 / TypeScript / Tailwind 4 (PWA, offline-capable) · Python 3.11+ /
FastAPI · SQLAlchemy 2 / Alembic · PostgreSQL 16 (SQLite in dev) · WeasyPrint/fpdf2 PDF ·
Docker Compose + nginx (deploy).
