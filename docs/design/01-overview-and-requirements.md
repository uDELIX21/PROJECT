# 01 · Executive Summary, Assumptions, Ambiguities & Requirements Matrix

**Status:** Draft for approval · **Covers:** deliverable items 1–4

---

## 1. Executive Summary

This artifact defines the architecture for a production-grade School Management
Information System (SMS) for a Ghanaian private/missionary school (~700 students,
~20 class streams, Crèche → JHS 3). The system covers five tightly-coupled pillars:

1. **Academics** — academic years/terms, enrollment lifecycle, NaCCA-aligned versioned
   curriculum, configurable assessment & grading engine (separate qualitative model for
   early childhood), attendance, locked mark submission, configurable PDF report cards.
2. **Finance** — an append-only double-sided **ledger** (charges, payments, allocations,
   waivers, adjustments, refunds), configurable fee structures per grade, receipt
   immutability, mobile-money payment flow with verified idempotent webhooks, and
   configurable **financial clearance** gating for reports/exams.
3. **People & Operations** — students, parents/guardians (explicit relationships,
   multiple children per guardian, confirmed phone-match linking), teachers &
   assignments, appraisals, discipline, pickup authorization.
4. **Data & Communication** — transaction-safe CSV/XLSX imports with preview and
   duplicate detection; templated SMS/in-app notifications via a provider abstraction
   (Arkesel, Hubtel); +233 phone normalization.
5. **Trust** — RBAC with resource-level scoping enforced server-side, comprehensive
   immutable audit logging, offline teacher data entry via IndexedDB/PWA with
   conflict-aware sync, backups/DR, observability, and Ghana-context privacy practice.

**Stack:** Next.js/React/TypeScript/Tailwind PWA frontend · Python 3.12/FastAPI backend ·
PostgreSQL 16 · Redis · S3-compatible file storage · WeasyPrint PDF. All business rules
that vary between schools (fees, grading scales, assessment weights, clearance thresholds,
curriculum versions, school identity) are **database-configurable**, never hard-coded.

**Scale posture:** designed for 10× the initial load (7,000 students) on the same
architecture; stateless API tier and per-school partition-friendly schema allow growth
without rewrites.

**Delivery posture:** ten phases (§14 roadmap). This document set completes Phases 0–2.
Phase 3 (core implementation) starts only upon approval.

---

## 2. Scope

### In scope (v1)

Everything listed in the requirements matrix below (§3) with priority **M** or **S**,
delivered across Phases 3–10.

### Explicitly out of scope (v1) — can be added later

| Item | Reason |
|---|---|
| Official BECE registration/results integration | No official API/rules exist to integrate; school-entered records only, clearly labelled (spec §9). |
| Full double-entry general ledger / accounting (staff payroll, expense accounting) | v1 ledger is student-fee-centric; designed so it can extend. |
| Timetabling / lesson scheduling | Not in spec; curriculum engine supports coverage tracking inputs later. |
| Library, transport route management, hostel management | Not in spec. |
| Native mobile apps | PWA covers mobile browsers; API is app-ready. |
| Multi-school SaaS tenancy (billing, cross-school analytics) | Schema is tenancy-ready (`school_id` everywhere) but deployment is single-school. |
| E-learning content delivery / homework media | Not in spec. |

---

## 3. Requirements Matrix

Legend — **Priority:** `M` must-have for v1 · `S` should-have for v1 · `C` configurable requirement.
**Phase** refers to implementation phase (§14). Source = spec section of the master prompt.

### 3.1 School profile & structure

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-PROF-01 | Model 14 grades: Crèche, Nursery 1–2, KG 1–2, Basic 1–6, JHS 1–3, grouped into bands Early Childhood / Primary / JHS | §1 | M | 3 |
| REQ-PROF-02 | Distinguish **Grade** (academic level) from **ClassStream** (e.g., Basic 4 vs Basic 4A) | §1 | M | 3 |
| REQ-PROF-03 | Support multiple streams per grade; streams exist per academic year | §1 | M | 3 |
| REQ-PROF-04 | Capacity planning target: 700+ students, 20+ classes, 30+ teachers, 1,000+ guardian links | §38 | M | all |

### 3.2 Technology stack

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-TECH-01 | Next.js + React + TypeScript + Tailwind, responsive PWA | §2 | M | 3,7 |
| REQ-TECH-02 | Python + FastAPI backend (no deviation) | §2 | M | 3 |
| REQ-TECH-03 | PostgreSQL with SQLAlchemy ORM + migrations | §2 | M | 3 |
| REQ-TECH-04 | File storage abstraction (logos, photos, report cards, receipts, imports); no large BLOBs in DB rows | §2 | M | 3 |
| REQ-TECH-05 | CSV + XLSX parsing for imports | §2 | M | 8 |
| REQ-TECH-06 | Server-side PDF generation | §2 | M | 4 |
| REQ-TECH-07 | Auth: hashing, secure sessions/tokens, reset, recovery, rate limiting, secure cookies | §2 | M | 3 |

### 3.3 Domain model & academic calendar

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-DOM-01 | Implement all entities listed in spec §3 (≥43); additions allowed with justification | §3 | M | 3–6 |
| REQ-CAL-01 | AcademicYear is a first-class entity with 3 terms; active year/term flags | §4 | M | 3 |
| REQ-CAL-02 | Historical, active, and future academic years coexist | §4 | M | 3 |
| REQ-CAL-03 | All academic/financial/attendance/assessment/report records reference year+term | §4 | M | 3,4,5 |
| REQ-CAL-04 | Term closure; reopening only by authorized administrator (audited) | §4 | M | 3 |
| REQ-CAL-05 | Historical records immutable after finalization except controlled, audited overrides | §4 | M | 4,5 |

### 3.4 Student lifecycle & promotion

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-STU-01 | Student lifecycle states: applicant → admitted → enrolled → active → promoted → graduated; plus withdrawn, transferred, repeated, suspended/inactive | §5 | M | 3 |
| REQ-STU-02 | Formal **Enrollment** records per year/class (not mutation of a `class` field) | §5 | M | 3 |
| REQ-STU-03 | End-of-year promotion workflow: bulk promote, individual overrides, repeaters, withdrawn, transferred, graduation | §5 | M | 3 |
| REQ-STU-04 | Promotion maps e.g. 2026/27 Basic 4A → 2027/28 Basic 5A with per-student decisions | §5 | M | 3 |
| REQ-STU-05 | Student profile: student ID/code, full name, gender, DOB, class, status, academic history, guardians | §14 | M | 3 |

### 3.5 Curriculum engine

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-CUR-01 | Configurable, versioned curriculum engine; no hard-coded structures | §6 | M | 4 |
| REQ-CUR-02 | Hierarchy: CurriculumVersion → Grade → Subject → Strand → Sub-Strand → Content Standard → Indicator → Core Competency | §6 | M | 4 |
| REQ-CUR-03 | Core competencies incl. Critical Thinking, Creativity, Communication, Collaboration, Digital Literacy, Problem Solving | §6 | M | 4 |
| REQ-CUR-04 | Curriculum versioning preserves historical assessment references | §6 | M | 4 |

### 3.6 Assessment & grading

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-ECD-01 | Early childhood uses qualitative developmental assessment, not numeric model | §7 | M | 4 |
| REQ-ECD-02 | Configurable domains (gross/fine motor, language, cognitive, social, emotional, self-care, creativity, observation) | §7 | M | 4 |
| REQ-ECD-03 | Configurable ratings (default Emerging/Developing/Achieved) | §7 | M | 4 |
| REQ-ECD-04 | Daily activity/observation logs | §7 | S | 4 |
| REQ-ASM-01 | Configurable assessment schemes by year/term/grade/(subject); no hard-coded 50/50 or 30/70 | §8 | M,C | 4 |
| REQ-ASM-02 | Pipeline: raw → weight → weighted → final score → grade → remark | §8 | M | 4 |
| REQ-ASM-03 | Configurable assessment components | §8 | M | 4 |
| REQ-BEC-01 | Separate: School Exam Result / BECE Mock / BECE Prediction / Official BECE Result; never present predictions as official; no invented official rules | §9 | M | 4 |
| REQ-GRD-01 | Configurable grading scales (range → grade → remark) per school/year/band | §10 | M,C | 4 |
| REQ-GRD-02 | Post-submission grade changes require authorized correction workflow (original preserved, reason/user/time recorded) | §10, §11 | M | 4 |
| REQ-MRK-01 | Teachers enter marks only for assigned subjects/classes | §11 | M | 4 |
| REQ-MRK-02 | Mark workflow Draft → Submitted → Locked; no silent edits after submit | §11 | M | 4 |
| REQ-ATT-01 | Attendance statuses: Present, Absent, Late, Excused, Left Early | §12 | M | 4 |
| REQ-ATT-02 | Daily/weekly/monthly/term summaries, percentages, class stats, roll-call compliance | §12 | M | 4 |
| REQ-ATT-03 | Teachers manage attendance only for assigned classes | §12 | M | 4 |

### 3.7 Report cards

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-RPT-01 | Downloadable/printable PDF report cards | §13 | M | 4 |
| REQ-RPT-02 | Separate template families: Early Childhood / Primary / JHS | §13 | M | 4 |
| REQ-RPT-03 | Report content: logo/crest, name, motto, student info, year/term, scores, grades, remarks, NaCCA indicators where appropriate, core competencies, attendance, teacher & head remarks, signatures, promotion status | §13 | M | 4 |
| REQ-RPT-04 | Configurable report templates | §13 | M,C | 4 |
| REQ-RPT-05 | Report availability respects financial clearance policy | §22, §45 | M | 4,5 |

### 3.8 Parents, guardians, pickup

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-PAR-01 | Guardian profile: name, relationship, phone, email, occupation, residential address, Ghana Digital Address, optional lat/lng, comms preferences, contact windows | §14 | M | 3 |
| REQ-PAR-02 | Ghana Digital Address and GPS coordinates are distinct fields | §14 | M | 3 |
| REQ-PAR-03 | One parent account ↔ multiple students via explicit relationship records | §15 | M | 3 |
| REQ-PAR-04 | Import suggests parent links by phone match with confidence; admin confirms; linking logged; never auto-link | §16, §51.8 | M | 8 |
| REQ-PKU-01 | Authorized pickup persons (esp. early childhood): name, relationship, phone, photo/ID ref, status, expiry; creator/modifier recorded | §17 | M | 6 |

### 3.9 Finance

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-FIN-01 | Ledger-oriented finance; balance **derived** from transactions, never a mutable `student.balance` | §18 | M | 5 |
| REQ-FIN-02 | Entities: FeeStructure, FeeCharge, Payment, PaymentAllocation, Adjustment, Waiver, Refund, Credit, Debit, Receipt | §18 | M | 5 |
| REQ-FIN-03 | Initial fee values (EC GH¢300–350, B1–3 GH¢400, B4–6 GH¢500, JHS GH¢600) stored as **configuration**, not code | §19 | M,C | 5 |
| REQ-FIN-04 | Configurable charge types: tuition, feeding, ICT/lab, PTA levy, transport, exam fees, others | §19 | M | 5 |
| REQ-FIN-05 | Discounts, scholarships, waivers, adjustments, payment plans | §19 | M | 5 |
| REQ-FIN-06 | Transaction fields: ID, student, year, term, amount, datetime, type, method, provider, provider ref, status, user, receipt no. | §20 | M | 5 |
| REQ-FIN-07 | Support opening debts, term charges, partial/overpayments, credits, refunds, waivers, adjustments | §20 | M | 5 |
| REQ-FIN-08 | No silent deletion of financial transactions; reversal/void mechanisms | §20 | M | 5 |
| REQ-PAY-01 | Methods: MTN MoMo, Telecel Cash, AT Money, cash, configurable others; stub adapters initially | §21 | M | 5 |
| REQ-PAY-02 | Workflow: initiated → pending → provider ref → webhook → verification → idempotency → confirmed → ledger → receipt → notification | §21 | M | 5 |
| REQ-PAY-03 | Duplicate webhooks never create duplicate ledger entries | §21 | M | 5 |
| REQ-PAY-04 | Failed/reversed/refunded/pending payments represented separately | §21 | M | 5 |
| REQ-CLR-01 | Configurable clearance policies (report access, exam clearance) with states CLEAR/BLOCKED/WAIVED/PAYMENT_PLAN/PENDING_RECONCILIATION/MANUAL_OVERRIDE; audited overrides | §22 | M | 5 |
| REQ-RCP-01 | Receipts for cash and confirmed e-payments with required fields incl. balance | §23 | M | 5 |
| REQ-RCP-02 | Receipts immutable after issue except controlled void/reversal | §23 | M | 5 |

### 3.10 Imports

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-IMP-01 | CSV/XLSX import for students, teachers, parents with fields per spec §24 | §24 | M | 8 |
| REQ-IMP-02 | Downloadable sample templates | §24 | M | 8 |
| REQ-IMP-03 | Validation, preview, duplicate detection, row-level errors, correction guidance, transaction-safe import, history, rollback | §24, §25 | M | 8 |
| REQ-IMP-04 | Pipeline Upload→Parse→Validate→Preview→Confirm→Import→Report with success/failed/warning/duplicate reporting and ImportJob records | §25 | M | 8 |

### 3.11 Staff, appraisal, discipline

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-TCH-01 | Teacher records: personal, contact, subjects, classes, assignments, employment info | §26 | M | 3 |
| REQ-TCH-02 | Teacher access restricted by assignments (server-side) | §26 | M | 3,4 |
| REQ-APR-01 | Configurable appraisal forms; criteria, evaluator, period, scores, comments, overall rating, acknowledgement, history; evaluator authorization; confidentiality | §27 | M | 6 |
| REQ-DIS-01 | Discipline incidents: date/time, student, category, description, action, staff, parent notification, resolution, status; restricted access | §28 | M | 6 |

### 3.12 Communication

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-COM-01 | Bulk & automated messaging: payment confirmation, debt reminder, emergency broadcast, report availability, announcements | §29 | M | 6 |
| REQ-COM-02 | Phone normalization to +233XXXXXXXXX | §29 | M | 3,6 |
| REQ-COM-03 | Provider abstraction; Arkesel & Hubtel adapters; credentials never hard-coded | §29 | M | 6 |

### 3.13 Access control, audit, privacy

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-RBAC-01 | RBAC + resource-level authorization; roles: Super Admin, Headmaster, Bursar, Teacher, Parent, Student | §30 | M | 3 |
| REQ-RBAC-02 | Granular permissions incl. the 13 listed in spec §30; server-side enforcement mandatory | §30 | M | 3 |
| REQ-AUD-01 | Audit log: user, action, entity, ID, timestamp, previous/new value, reason, IP/device | §31 | M | 3 |
| REQ-AUD-02 | Audit coverage incl. grade changes, financial transactions, receipt voids, permission changes, student changes, parent linking, waivers, report finalization, overrides | §31 | M | 3–6 |
| REQ-AUD-03 | Audit logs protected from ordinary users | §31 | M | 3 |
| REQ-PRV-01 | Data minimization & access control; child/parent/teacher/financial data protected | §36 | M | all |
| REQ-PRV-02 | Student/parent data never accessible by knowing a student ID alone | §36 | M | 3 |

### 3.14 Offline & performance

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-OFF-01 | Teacher offline marks entry via IndexedDB + Service Worker/PWA + sync queue + conflict detection + retry; **not** LocalStorage-only | §32 | M | 7 |
| REQ-OFF-02 | UI sync states: synced / pending / failed / conflict; no silent data loss | §32 | M | 7 |
| REQ-OFF-03 | Server validation on sync; confirmation surfaced | §32 | M | 7 |
| REQ-LOW-01 | Pagination, caching, compressed assets, optimized payloads, lazy loading, image compression, background sync | §33 | M | all |
| REQ-LOW-02 | Usable on modest mobile devices & low bandwidth | §33 | M | all |

### 3.15 Settings, security, backups, dashboards, UI

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-SET-01 | Admin-configurable: school name/logo/motto/location/digital address/contacts, active year/term, grading schemes, fee structures, clearance rules, report templates, comms settings — stored in DB | §34 | M,C | 3–5 |
| REQ-SEC-01 | Production security baseline: hashing, authz, rate limiting, input validation, SQLi/XSS/CSRF protection, secure headers, secure uploads, secret management, HTTPS, DB access control, audit | §35 | M | all |
| REQ-SEC-02 | No passwords/secrets/tokens exposed to frontend | §35 | M | all |
| REQ-BKP-01 | Automated backups, retention, off-site storage, restoration procedure, periodic restore tests | §37 | M | 10 |
| REQ-DSH-01 | Role-specific dashboards: Super Admin/Headmaster, Bursar, Teacher, Parent, Student (content per spec §39) | §39 | M | 3–7 |
| REQ-UI-01 | Clean, professional, responsive, accessible UI; tables/filters/search/status/actions/confirmations/errors/empty & loading states; no decorative-card overload | §40 | M | all |

### 3.16 Architecture, API, DB, testing, operations

| ID | Requirement | Source | Pri | Phase |
|---|---|---|---|---|
| REQ-ARC-01 | Layered modular architecture: API → services → domain → repositories → PostgreSQL; provider abstractions (Payment/SMS/FileStorage) | §41 | M | 3 |
| REQ-API-01 | REST endpoints organized by domain (20 route groups per spec §42) | §42 | M | 3–6 |
| REQ-API-02 | AuthN/AuthZ, validation, pagination, filtering, sorting, consistent errors, proper HTTP codes | §42 | M | 3 |
| REQ-DB-01 | ERD, schema, PK/FK/indexes/unique/check constraints, migration & seed strategy | §43 | M | 2 (this artifact), 3 |
| REQ-TST-01 | Unit, integration, E2E, security, import, payment, offline test suites | §44 | M | 9 (+ each phase) |
| REQ-JRN-01 | All 9 critical journeys in spec §45 implemented as automated tests | §45 | M | 9 |
| REQ-SEED-01 | Realistic fictional seed: 700+ students, ~20 streams, 30 teachers, guardians w/ siblings & multiple guardians, balances, payment history, attendance, assessments | §46 | M | 3–9 |
| REQ-SEED-02 | Seed data clearly fictional; no real personal data | §46, §51.12 | M | all |
| REQ-ERR-01 | Graceful failures with meaningful messages for all listed cases; no stack traces to ordinary users | §47 | M | all |
| REQ-OBS-01 | Structured logs, error monitoring, health checks (app/db), API/webhook/sync monitoring, admin status view | §48 | M/S | 10 |
| REQ-CFG-01 | Nothing school/year/term-variable is hard-coded (fees, percentages, scales, identity, dates, thresholds, layouts, curriculum versions, providers) | §49 | M | all |

**Traceability total:** 96 requirement rows covering all 49 specification sections.
Each requirement is re-addressed in the relevant architecture document and will be
tracked through implementation & testing phases.

---

## 4. Assumptions

Working assumptions (validated defaults; flag during review if wrong):

| # | Assumption |
|---|---|
| A1 | The deployment serves **one school per installation**. Schema keeps `school_id` everywhere for future multi-school use. |
| A2 | Users access the system through modern evergreen browsers (Chrome/Edge/Firefox/Safari, incl. mobile). No IE support. |
| A3 | Primary day-to-day devices for teachers/bursar are low-to-mid Android phones and shared desktops; UI targets ~360px width upward, works on 2G/3G-class connections. |
| A4 | The school calendar has exactly **3 terms** per academic year (configurable term count in schema, but workflows assume 3). |
| A5 | Currency is **Ghana Cedi (GHS)** only; no FX handling. |
| A6 | Fees are charged **per term** (tuition quoted per term), consistent with the provided GH¢ values; annual and one-off charges also supported. |
| A7 | "Class teacher" (form teacher) is a teacher assignment attribute used for report remarks and roll-call ownership. |
| A8 | Guardians may have no email; SMS is the primary external channel; phone numbers are Ghanaian. |
| A9 | Official BECE results, when recorded, are **typed in by staff** from official slips; the system never computes them. |
| A10 | Staff (teachers/bursar/head) accounts are created by administrators (no self-signup). Parent accounts may be created by admins or via invitation link; student accounts (optional) are provisioned by admins. |
| A11 | One human may hold multiple roles is rare; still supported (roles are many-to-many on User). |
| A12 | The school accepts electronic payments via aggregators; direct telco APIs are out of v1 scope — adapters target aggregator-style APIs, starting as stubs. |
| A13 | Timezone: Africa/Accra (GMT, no DST) for all business dates; server stores UTC, renders in Africa/Accra. |
| A14 | Report cards and receipts are generated on demand and cached in file storage; regenerating a finalized report without override workflow is not allowed. |
| A15 | Seed/demo environment is clearly watermarked ("DEMO — fictional data"). |

---

## 5. Identified Ambiguities

Per Agent Rule 14, ambiguities are surfaced rather than silently guessed. Each has the
**resolution adopted in this design** (changeable at review).

| # | Ambiguity | Adopted resolution | Ref |
|---|---|---|---|
| AM1 | "Department" entity purpose undefined for a basic school | Model `Department` as optional grouping = school sections (Early Childhood / Primary / JHS); grades belong to a department. Not used for authorization by default. | REQ-DOM-01 |
| AM2 | Are fee amounts per term or per year? | Values from spec §19 treated as **per-term tuition**; fee items carry explicit `period` (per_term/per_year/one_off). | REQ-FIN-03 |
| AM3 | Which grading scale for Primary/JHS? | **No official scale is assumed.** Grading scales are fully configurable per band/year; seed ships with an example school-approved scale clearly labelled as configuration, not policy. | REQ-GRD-01 |
| AM4 | Class position/rank on reports — required? | Configurable school setting, default ON. | D2 |
| AM5 | Core competencies assessed numerically or qualitatively? | Qualitative ratings (configurable scale, default same Emerging/Developing/Achieved vocabulary) with comments; no numeric weighting. | REQ-CUR-03 |
| AM6 | NaCCA indicators on Primary/JHS report cards — how detailed? | Optional per template: show strand/indicator coverage or per-subject indicator attainment summary when the school records it; otherwise omitted. Configurable section. | REQ-RPT-03 |
| AM7 | Do students get login accounts? | Role exists and is supported, but student accounts are **optional per school setting** (default OFF for privacy; parents view children's data). | REQ-RBAC-01 |
| AM8 | "Financial clearance threshold" — % paid or absolute amount? | Policy supports both modes plus per-band overrides. | REQ-CLR-01 |
| AM9 | Opening debts from import — ledger treatment | Imported as dated `OPENING_BALANCE` ledger entries (debit), fully audited, dated as configured (e.g., first day of year). | REQ-FIN-07 |
| AM10 | Repeater enrollment semantics | New Enrollment row with `is_repeat=true` into the same grade; prior year's records untouched. | REQ-STU-03 |
| AM11 | Multiple active terms? | Exactly one active term at a time (enforced by partial unique index); term closure is explicit. | REQ-CAL-04 |
| AM12 | SMS consent/opt-out legal basis | Comms preferences + contact windows stored on guardian; broadcasts honor opt-out; school is data controller under Ghana's Data Protection Act, 2012 (Act 843) — documented in privacy note (§12 doc). | REQ-COM-01 |
| AM13 | Teacher appraisal evaluators — who? | Configurable evaluator roles; default: Headteacher + Super Admin; confidential (subject teacher sees only acknowledgement step). | REQ-APR-01 |
| AM14 | "Attendance: Left Early" vs half-day accounting | `LEFT_EARLY` counts as present-with-flag; percentage weights configurable (default: present=1, late=1, left_early=1, excused=0-but-noted, absent=0). | REQ-ATT-02 |
| AM15 | Webhook source for MoMo payments | v1 uses aggregator webhooks; stub provider simulates them locally. Signature scheme defined per provider config. | REQ-PAY-02 |
| AM16 | Is "Curriculum" school-authored or NaCCA-imported? | Both: structure is NaCCA-shaped; data entry via UI or structured import; versioning handles updates. No policy is invented — the tree is whatever the school loads. | REQ-CUR-01 |
| AM17 | Pickup authorization scope | Per-student authorizations (not per-class), expiry dates supported; photo storage optional and access-restricted. | REQ-PKU-01 |
| AM18 | Report card "availability" vs "generation" | Generation is staff-side; **publication** is a separate audited step gated by clearance; parents only see published reports. | REQ-RPT-05 |
| AM19 | Offline scope beyond marks? | v1 offline write scope = marks entry + attendance; other entities read-cached. Extensible. | REQ-OFF-01 |
| AM20 | Parent self-service payments? | v1: parent views invoices & pays via bursar or initiated payment links (stub provider); full self-checkout deferred. | REQ-PAY-01 |
