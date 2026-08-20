# System Design & Requirements Artifact

**Project:** Enterprise-Grade School Management Information System (SMS)
**Client context:** Ghanaian private/missionary school · ~700+ students · ~20 classes · Crèche → JHS 3
**Document status:** `DRAFT — SUBMITTED FOR APPROVAL` (Phase 0–2 deliverable)
**Date:** 2026-08-20
**Branch:** `arena/01a01d2b-project`

> ⚠️ Per the project mandate (spec §50, §52), **no implementation code has been written**.
> This artifact covers Phase 0 (Requirements Analysis), Phase 1 (Domain Design) and
> Phase 2 (Database & Architecture). Implementation begins only after this artifact is
> reviewed and approved.

---

## Document Index

| # | Document | Covers spec deliverable items |
|---|----------|------------------------------|
| 1 | [01-overview-and-requirements.md](./01-overview-and-requirements.md) | 1. Executive summary · 2. Assumptions · 3. Requirements matrix · 4. Identified ambiguities |
| 2 | [02-business-rules.md](./02-business-rules.md) | 5. Resolved business rules |
| 3 | [03-domain-model.md](./03-domain-model.md) | 6. Domain model (entities, relationships, lifecycles, state transitions) |
| 4 | [04-database-schema.md](./04-database-schema.md) | 7. ERD · 8. Database schema proposal · migrations · seed strategy |
| 5 | [05-api-architecture.md](./05-api-architecture.md) | 9. API architecture |
| 6 | [06-authentication-authorization.md](./06-authentication-authorization.md) | 10. Authentication architecture · 11. RBAC/permission matrix |
| 7 | [07-academic-engine.md](./07-academic-engine.md) | 12. Curriculum architecture · 13. Assessment architecture (incl. report cards, attendance, BECE separation) |
| 8 | [08-financial-engine.md](./08-financial-engine.md) | 14. Financial ledger architecture · 15. Payment architecture |
| 9 | [09-offline-and-low-bandwidth.md](./09-offline-and-low-bandwidth.md) | 16. Offline synchronization architecture |
| 10 | [10-imports.md](./10-imports.md) | 18. Import architecture |
| 11 | [11-communications-notifications.md](./11-communications-notifications.md) | 19. Notification architecture |
| 12 | [12-audit-security-privacy.md](./12-audit-security-privacy.md) | 20. Audit architecture · 21. Security architecture (+ data privacy) |
| 13 | [13-backup-dr-deployment-observability.md](./13-backup-dr-deployment-observability.md) | 22. Backup/DR strategy · 23. Deployment architecture · observability |
| 14 | [14-testing-roadmap-risks.md](./14-testing-roadmap-risks.md) | 24. Testing strategy · 25. Implementation roadmap · 26. Risks & mitigations |

---

## Technology Decisions (summary)

| Decision | Choice | Rationale / deviation? |
|---|---|---|
| Frontend | **Next.js 15 (App Router) + React 19 + TypeScript + Tailwind CSS**, PWA | As specified. No deviation. |
| Backend | **Python 3.12 + FastAPI + Pydantic v2** | Preferred stack. **No deviation** — no compelling reason to move to Node. |
| ORM / migrations | **SQLAlchemy 2.x + Alembic** | As specified. |
| Database | **PostgreSQL 16** | As specified. |
| Money handling | Integer **pesewas** (`BIGINT`, 1 GHS = 100 pesewas) | Avoid floating-point drift in the ledger. |
| PDF generation | **WeasyPrint** (HTML/Jinja2 → PDF), server-side | Reliable, template-driven, CSS-configurable layouts for 3 template families. |
| File storage | Storage abstraction (local disk in dev; **S3-compatible** object store in prod) | Per spec §2 — no large binaries in relational columns. |
| CSV/XLSX | Python `csv` stdlib + `openpyxl` (streaming) | Low memory footprint for large imports. |
| Cache / queues / rate limiting | **Redis** | Sessions revocation list, rate-limit buckets, background job queue (simple `arq`/RQ workers). |
| Auth | **Server-side sessions** in HttpOnly Secure cookies + CSRF double-submit; Argon2id hashing | Revocable, simple for a browser-first app; see §06. |
| IDs | **UUIDv7** primary keys; human-friendly display codes generated separately | Unenumerable (privacy §36), time-sortable. |

---

## Decisions Requested From the School / Project Sponsor

These are the open decision points called out in
[01-overview-and-requirements.md § Ambiguities](./01-overview-and-requirements.md#5-identified-ambiguities).
None of them block design approval — each has a safe **default resolution** — but approval of the
defaults (or an alternative) is requested:

| # | Decision point | Default proposed |
|---|---|---|
| D1 | Tenancy: single-school deployment vs multi-school SaaS | Single-school deployment; schema keeps `school_id` on all tables so multi-school is possible later without migration rewrites. |
| D2 | Report cards: print class position/rank & class size? | Configurable per school setting; **default ON** (common Ghanaian private-school practice) but can be switched off. |
| D3 | School identity for seed data | Use a clearly-fictional school: **“Hope Star Academy (Demo)”**, fictional motto, GA-prefix Ghana Digital Address samples. |
| D4 | Currency & rounding | GHS, pesewa precision; final scores rounded half-up to 1 decimal (configurable). |
| D5 | Hosting | Single-VPS Docker Compose deployment behind nginx + Let's Encrypt; managed Postgres optional. |
| D6 | Payment providers | MTN MoMo / Telecel Cash / AT Money via **stub adapters** initially; aggregator (e.g., Hubtel/Arkesel/paystack-style) to be chosen at integration time. |
| D7 | SMS provider | Arkesel **and** Hubtel adapters behind one interface; start in sandbox/test mode. |
| D8 | Language | English only (Ghana official language); no Twi/Fante UI translation in v1. |
| D9 | BECE official results | System records only what the school enters, explicitly labelled; **no official BECE calculation rules are implemented**. |
| D10 | Users/staff count for licensing & infra sizing | 700 students, ~20 streams, ~30 teachers, ~1,000 guardian links assumed for capacity planning. |

---

## Approval Checklist

- [ ] Requirements matrix (§01) covers the school's needs
- [ ] Ambiguity resolutions / assumptions (§01–02) are acceptable
- [ ] Domain model & lifecycles (§03) match school practice
- [ ] Database schema & ERD (§04) approved
- [ ] API + auth + RBAC matrix (§05–06) approved
- [ ] Academic engine design (§07) approved
- [ ] Financial engine design (§08) approved
- [ ] Offline, import, communication designs (§09–11) approved
- [ ] Security/audit/DR/deployment (§12–13) approved
- [ ] Roadmap & estimates (§14) approved → **authorization to begin Phase 3**

**Reply with approval (optionally referencing decision IDs D1–D10) to start Phase 3 implementation.**
