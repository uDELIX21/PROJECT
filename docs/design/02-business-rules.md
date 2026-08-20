# 02 · Resolved Business Rules

**Status:** Draft for approval · **Covers:** deliverable item 5

Business rules adopted for implementation. Every rule is enforced **server-side**
(Agent Rule 6) and most produce **audit log entries** (§12 doc). Rule IDs are stable
and will be referenced by tests (`BR-…`).

---

## BR-A · Academic calendar

| ID | Rule |
|---|---|
| BR-A01 | Exactly one **active academic year** and one **active term** per school at any time (enforced by partial unique indexes). |
| BR-A02 | A term may be `DRAFT → ACTIVE → CLOSED`. Reopening a closed term requires `MANAGE_SETTINGS` + explicit reason; action is audited and sets `reopened_by/at`. |
| BR-A03 | While a term is `CLOSED`: marks, attendance, assessments, and report cards for that term are read-only. Corrections only via the override workflow (BR-M04). |
| BR-A04 | Financial ledger entries are append-only regardless of term state; corrections are reversing entries (BR-F08). |
| BR-A05 | Creating a new academic year does not alter any existing record; all records carry their own `academic_year_id`/`term_id`. |
| BR-A06 | Term date ranges must not overlap within a year; year ranges must not overlap across years. |

## BR-S · Students & enrollment

| ID | Rule |
|---|---|
| BR-S01 | Student status transitions follow the lifecycle diagram (§03). Illegal transitions are rejected (e.g., `GRADUATED → ACTIVE`). |
| BR-S02 | A student has exactly **one active enrollment** per academic year (partial unique index on `(student_id, academic_year_id)` where status is active). |
| BR-S03 | Enrollment records are never deleted; withdrawals set `status=WITHDRAWN` + `ended_at`. |
| BR-S04 | Admission/student codes are generated from a per-school sequence and never reused. |
| BR-S05 | Promotion produces next-year enrollments in one audited batch; each student gets an explicit decision: `PROMOTE / REPEAT / WITHDRAW / TRANSFER / GRADUATE`. Undecided students cannot be silently skipped — the batch stays `PENDING_DECISION` until resolved. |
| BR-S06 | `GRADUATE` is only offered for JHS 3 students; `REPEAT` keeps the student in a stream of the same grade next year. |
| BR-S07 | Changing a student's biodata (name, DOB, gender) is audited with previous/new values. |

## BR-C · Curriculum

| ID | Rule |
|---|---|
| BR-C01 | Curriculum content is immutable per **CurriculumVersion**. Updates create a new version; old versions remain readable. |
| BR-C02 | Assessment/lesson references point at concrete indicator rows (which carry their version), never at mutable "latest" pointers — history survives re-versioning. |
| BR-C03 | A subject may be attached to grades via `GradeSubject`; report cards list only subjects with recorded assessment data or explicit inclusion. |
| BR-C04 | Core competencies are rated qualitatively; they never contribute numeric weight to subject scores. |

## BR-M · Marks, assessment & grading

| ID | Rule |
|---|---|
| BR-M01 | Assessment scheme weights are configurable per (year, term, grade, optional subject); component weights for a scheme must sum to exactly 100%. |
| BR-M02 | Score pipeline is deterministic: `component_score = Σ(raw/max × component_weight)`; `final = Σ components`; then grade scale lookup. Rounding mode and precision are school settings (default: half-up, 1 decimal). |
| BR-M03 | Mark sheets have states `DRAFT → SUBMITTED → LOCKED`. Drafts are editable; after submission only the override workflow changes data. |
| BR-M04 | **Grade correction workflow:** teacher requests correction (reason required) → authorized admin reviews → approval applies new score; the **original value, new value, reason, approver, actor, timestamp** are persisted and audited. The original score is never overwritten without trace. |
| BR-M05 | Teachers can only enter/view marks for classes+subjects in their active `TeacherAssignment`s. |
| BR-M06 | Scores must be within `[0, component.max_score]`; out-of-range submissions are rejected with field-level errors. |
| BR-M07 | Early childhood students are excluded from numeric schemes; they receive developmental ratings (BR-E). |
| BR-M08 | A subject's final results become **finalized** when the term closes or an admin finalizes explicitly; report cards render only finalized data (or explicitly marked drafts). |
| BR-M09 | BECE-type records: `SCHOOL_EXAM`, `MOCK`, `PREDICTION`, `OFFICIAL` are separate record types; anything but `OFFICIAL` displays with a visible "school-generated / not official" label; `OFFICIAL` records are manual transcription only. |

## BR-E · Early childhood assessment

| ID | Rule |
|---|---|
| BR-E01 | Domains and rating scales are configuration (seeded defaults per spec §7); ratings are `Emerging / Developing / Achieved` by default. |
| BR-E02 | Observation logs are append-only notes with author + timestamp; edits create a new revision (previous retained). |
| BR-E03 | ECD report cards contain no numeric subject scores; they render domain ratings, observations summary, attendance, and qualitative remarks. |

## BR-T · Attendance

| ID | Rule |
|---|---|
| BR-T01 | One attendance sheet per class per school day; one record per enrolled student per sheet (unique constraint). |
| BR-T02 | Statuses: `PRESENT, ABSENT, LATE, EXCUSED, LEFT_EARLY`. Default weights for percentage: present/late/left-early = 1, absent/excused = 0 (excused reported separately). Weights configurable. |
| BR-T03 | Percentage = weighted present ÷ school days the student was enrolled within the period. Days before enrollment start / after withdrawal are excluded. |
| BR-T04 | Sheets are editable while the term is active; after closure only via override workflow. |
| BR-T05 | Roll-call compliance = sheets taken vs expected school days per class/teacher; surfaced on dashboards. |

## BR-F · Finance & payments

| ID | Rule |
|---|---|
| BR-F01 | `student.balance` is **derived**: `Σ debits − Σ credits` over ledger entries, optionally scoped by year/term. No stored mutable balance field exists. |
| BR-F02 | Ledger entries are append-only and immutable. Errors are corrected by a **reversing entry** referencing the original (`reversed_entry_id`), with reason + actor; the original stays intact. |
| BR-F03 | Billing: charges are generated from the active FeeStructure per enrollment (billing run) or manually; each charge is a ledger DEBIT of category `CHARGE` linked to a `FeeCharge` row. |
| BR-F04 | Waivers/discounts/scholarships are recorded as charge reductions plus a ledger CREDIT of category `WAIVER/ADJUSTMENT`, each with approval metadata + reason. |
| BR-F05 | Payments allocate to charges oldest-due-first by default (FIFO); bursar may reallocate manually (audited). Unallocated remainder becomes a credit balance (overpayment). |
| BR-F06 | Refunds are explicit ledger CREDITs of category `REFUND` requiring authorization (`VOID_PAYMENT` permission) + reason. |
| BR-F07 | Receipts issue for cash payments immediately and for e-payments on confirmation. Receipt numbers come from a per-school monotonic sequence. |
| BR-F08 | Voiding a receipt creates a `VOID` receipt event referencing the original; the original PDF remains but is stamped VOID on re-render; never deleted. |
| BR-F09 | Payments pending confirmation do **not** affect balances and produce no receipt. |
| BR-F10 | Payment provider webhooks: verify signature/secret → deduplicate on `(provider, provider_reference)` → only then post ledger entry + receipt + notification. Unverified webhooks are stored but never applied. |
| BR-F11 | Clearance states are recomputed on ledger changes: `CLEAR / BLOCKED / WAIVED / PAYMENT_PLAN / PENDING_RECONCILIATION / MANUAL_OVERRIDE`. Manual overrides require reason + authorization + audit. |
| BR-F12 | Opening debts are ledger `OPENING_BALANCE` debits created by import or setup, each audited. |
| BR-F13 | All amounts are integer pesewas ≥ 0 on source documents; ledger entries carry sign via `entry_type` (DEBIT/CREDIT), amount always positive. |

## BR-R · Reports & publication

| ID | Rule |
|---|---|
| BR-R01 | Report cards render from finalized term data using the template configured for the student's band. |
| BR-R02 | Publication is gated by the term's clearance state for the student unless waived via policy (`WAIVED`/`MANUAL_OVERRIDE`). |
| BR-R03 | Published reports are immutable per term; regeneration after finalization requires the override workflow and is audited. |
| BR-R04 | Parents see only their linked children's reports; students only their own (when student accounts are enabled). |

## BR-P · Parents, guardians & pickup

| ID | Rule |
|---|---|
| BR-P01 | Parent↔student links are explicit relationship rows with type (mother/father/guardian/other), `is_primary_contact`, and effective dates. |
| BR-P02 | Import phone matching **suggests** links with confidence (exact normalized match = high); a human confirms each link; every created link records `source=IMPORT_SUGGESTION` + confirmer. |
| BR-P03 | Pickup authorizations carry `created_by`, `updated_by`, status and optional expiry; expired authorizations are treated as inactive automatically. |
| BR-P04 | Guardian PII (address, digital address, coordinates) is visible only to roles with `VIEW_PARENT` (staff) — never to other parents/students. |

## BR-U · Users, security & audit

| ID | Rule |
|---|---|
| BR-U01 | Passwords: Argon2id; minimum length 10; breached-list check optional; history of last 5 hashes prevents reuse. |
| BR-U02 | Login rate-limits: 5 failures per account per 5 min → 15-min soft lock; global IP limits apply (details §06). |
| BR-U03 | Session revocation on password change and on admin deactivation; sessions expire after 12 h idle (configurable). |
| BR-U04 | Every authorization check fails closed: missing/unknown permission ⇒ 403, never a silent grant. |
| BR-U05 | Audit log rows are insert-only; application DB role has no UPDATE/DELETE grant on `audit_log`. |
| BR-U06 | Sensitive actions (payment void, waiver, override, parent link confirmation, user role change, term reopen, import commit, pickup change, discipline write) always write an audit entry with reason where applicable. |
| BR-U07 | API responses never include stack traces or internal exception names for unauthenticated/non-admin users. |

## BR-I · Imports

| ID | Rule |
|---|---|
| BR-I01 | An import commits **atomically**: all rows succeed or none persist (single transaction; per-row savepoints for staged partial modes if opted-in by admin). |
| BR-I02 | Duplicate detection: students by (surname, other names, DOB) fuzzy + admission code; parents by normalized phone; teachers by email/phone. Duplicates are reported, optionally skipped, never silently merged. |
| BR-I03 | Import files are retained in file storage for audit; ImportJob records counts, parameters, and actor. |
| BR-I04 | Imports cannot target a closed academic year/term. |

## BR-N · Notifications

| ID | Rule |
|---|---|
| BR-N01 | Outbound SMS recipients are normalized to `+233XXXXXXXXX`; invalid numbers are logged and skipped (not fatal to the batch). |
| BR-N02 | Guardians with `opt_out=true` receive no bulk SMS (transactional receipts still configurable). |
| BR-N03 | Provider failures retry with backoff (3 attempts) then mark `FAILED` and surface in the admin comms view. |
