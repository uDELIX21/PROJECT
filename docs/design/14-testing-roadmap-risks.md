# 14 · Testing Strategy, Implementation Roadmap & Risks

**Status:** Draft for approval · **Covers:** deliverable items 24–26

---

## 1. Testing strategy (REQ-TST-01, REQ-JRN-01)

### 1.1 Stack & pyramid

| Layer | Tools | Scope | Gate |
|---|---|---|---|
| Unit | pytest + hypothesis | score pipeline, balance math, phone normalization, clearance evaluator, lifecycle transitions, allocation FIFO | coverage ≥ 85% on domain services |
| Integration | pytest + httpx + real Postgres (testcontainers) | API endpoints incl. RBAC/scope matrices, migrations, ledger transactions, import pipeline, webhook flows | all green; each BR- rule mapped to ≥1 test |
| E2E | Playwright | the 9 critical journeys (§1.3) on seeded staging build | journey scripts in CI nightly |
| Security | pytest (authz fuzz), OWASP ZAP baseline scan | permission matrix exhaustive sweep: every endpoint × every role × in/out-of-scope resources; ID-probing attempts must 404 | zero unauthorized access |
| Offline | Playwright offline context + unit | journey J9 + replay idempotency property tests | no silent loss (assert server==client intent) |
| Payment | pytest (stub provider) | journey J5 matrix: success/fail/duplicate/delayed/reversal/refund/receipt-void | ledger invariants hold in every case |
| Import | pytest | valid/invalid/duplicate/malformed files, rollback atomicity, parent-match confirmation paths | BR-I rules enforced |
| PDF | pytest (weasyprint smoke + golden-file structural asserts) | 3 template families render with snapshots & seeded data; clearance gating | no blank/corrupt PDFs |

### 1.2 Data policy
Tests run on synthetic fixtures (same generator as seed, small scale); **never** real personal data (Agent Rule 12).

### 1.3 Critical journeys as first-class test suites (spec §45)

| # | Journey | Key assertions |
|---|---|---|
| J1 | Enrollment | create student → link guardian → enroll → appears in roster & billing basis |
| J2 | Mark entry | teacher login → only assigned class → draft → submit → locked for others |
| J3 | Grade correction | request → admin approve → override row + audit + original preserved |
| J4 | Report card | finalize → PDF → clearance BLOCKED denies publish → waiver → publish → parent sees |
| J5 | Payment | initiate → stub webhook (dup replay) → ledger + receipt + SMS; failure/reversal paths |
| J6 | CSV import | template → preview errors/dupes/matches → confirm → atomic commit → report |
| J7 | Import failure | malformed file → no partial DB state (`ROLLED_BACK`) |
| J8 | Permission boundary | Teacher A ↔ Teacher B class: 403/404 on every attempt |
| J9 | Offline marks | offline entry → reconnect → sync → conflict variant → confirmation |

### 1.4 Acceptance definition
A feature is "done" only when: unit+integration tests exist and pass, RBAC sweep covers it, error messages match REQ-ERR-01 cases, and audit hooks fire (where applicable). No feature is claimed operational without passing tests (Agent Rule 18).

---

## 2. Implementation roadmap (Phases 3–10)

Estimates assume ~2 experienced engineers; durations are working-week ranges. Each phase ends with its tests green on staging before the next begins.

| Phase | Deliverables | Exit criteria | Est. |
|---|---|---|---|
| **3 — Core** | Auth+sessions, users/roles/perms, school settings, years/terms, grades/streams, students, guardians+links, teachers+assignments, enrollments, promotion workflow, dashboards skeleton, CI/deploy baseline | J1, J8 pass; RBAC sweep clean; seeded dev env | 4–5 wk |
| **4 — Academic** | Curriculum engine+versioning, schemes/components, marks sheets & locking + correction flow, grading scales, attendance module, ECD ratings/observations, competency ratings, grade scales, report templates + PDF + finalization/publish (clearance hook stub) | J2, J3 pass; PDF golden tests; score-pipeline property tests | 5–6 wk |
| **5 — Financial** | Fee structures, billing runs, ledger, allocations, waivers/adjustments/plans, payments + stub providers + webhooks + receipts, clearance engine, bursar dashboard | J4 (gate), J5 pass; ledger invariant suite; reversal/void flows audited | 5–6 wk |
| **6 — Operations** | Appraisals, discipline, pickup authorizations, communications (templates, SMS adapters sandbox, broadcasts), notifications center | Journey tests + comms sandbox demo; confidentiality sweep | 3–4 wk |
| **7 — Offline/PWA** | Service worker, IndexedDB store, sync engine + conflict UI, offline badges, manifest/install, low-bandwidth budget audit | J9 pass; Lighthouse mobile PWA ≥ targets; bundle budget met | 3–4 wk |
| **8 — Imports & admin** | Templates, upload/parse/validate/preview, parent matching confirm flow, atomic commit + rollback, import history; school configuration polish | J6, J7 pass; 5k-row soak test | 3 wk |
| **9 — Hardening & test completion** | Full regression, security scan fixes, payment/offline/import edge suites, performance pass (indexes, EXPLAIN on roster/balance queries), accessibility pass | All §1 suites green; pen-test-style checklist closed | 2–3 wk |
| **10 — Deployment & handover** | Prod env config, runbooks (deploy/migrate/seed/backup/restore/troubleshoot), DR drill, operator training notes, go-live checklist | Staged restore drill succeeds; runbook review | 2 wk |

**Total:** ~27–33 weeks of engineering effort. Phases may overlap by ≤1 week where noted (e.g., P6 during P5's last week).

### Milestone demos for the school
End of P3 (core records + dashboards), P5 (full fee→receipt cycle on simulated MoMo), P7 (offline marks demo on a low-end phone), P10 (go-live rehearsal).

---

## 3. Risks & mitigations

| # | Risk | L×I | Mitigation |
|---|---|---|---|
| R1 | Low/unstable connectivity undermines daily use | H×H | offline-first for marks/attendance (§09), aggressive caching, small payloads, background sync; field-test on 3G early (P7 demo) |
| R2 | Data migration quality (opening balances, legacy records) corrupts finance trust | M×H | atomic imports, preview+confirm, staged-mode opt-in, pre-go-live reconciliation report signed off by bursar; dry-run on real CSV in staging |
| R3 | Payment provider integration delays | M×M | stub adapters exercise the full production path from day 1; provider choice deferred (D6) without blocking any module |
| R4 | Scope creep toward full accounting/HR | M×M | strict ledger scope (student fees); out-of-scope list approved up-front (§01); change requests logged separately |
| R5 | Grade/assessment policy ambiguity (official scales) | M×M | nothing hard-coded; school signs off on config rows during P4; BECE handled per Agent Rules 1–2 |
| R6 | Shared/low-end devices struggle with heavy UI | M×M | bundle budgets, route splitting, no chart libs, Playwright low-end emulation in CI |
| R7 | Weak password culture / shared accounts | H×M | lockouts, assisted recovery, session revocation; training: one account per person; audit exposes sharing patterns |
| R8 | SMS cost overrun via broadcasts | M×L | cost estimate + confirm dialog, throttling, dedupe, opt-out honored |
| R9 | Single-server failure | L×H | nightly+PITR backups off-site, documented RTO 4 h, optional managed-DB upgrade path |
| R10 | Privacy breach (child data) | L×H | scoped authorization swept in CI, 404-for-hidden, restricted fields, privacy training in handover |
| R11 | Curriculum data entry burden | M×L | bulk import + copy-forward versions; school may phase subjects across terms |
| R12 | Staff resistance to change | M×M | milestone demos, teacher champions, offline removes "network excuse", training materials in P10 |
| R13 | Timezone/date confusion (term dates vs UTC) | L×M | all business logic on Africa/Accra calendar dates; tests pin timezone |
| R14 | Requirement drift from this artifact | M×M | requirement IDs (REQ-*) referenced in PRs; ambiguity log updated via review rather than silent change (Agent Rule 14) |

---

## 4. Post-approval next actions (Phase 3 kickoff checklist)

1. Scaffold repo: `backend/` (FastAPI + SQLAlchemy + Alembic + pytest), `frontend/` (Next.js + Tailwind + PWA), `docker-compose.yml`, CI workflow.
2. Migrations 0001–000x implementing §04 schema core registry.
3. Seed catalog: permissions, roles+matrix, grades, terms for 2025/2026 & 2026/2027.
4. Auth vertical slice: login → session → `/auth/me` → RBAC guard demo endpoint.
5. Students/guardians/enrollments CRUD + J1 journey test.
6. Dashboards skeleton per role (tables-first, REQ-UI-01).
