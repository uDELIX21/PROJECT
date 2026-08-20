# 05 · API Architecture

**Status:** Draft for approval · **Covers:** deliverable item 9

## 1. Style & conventions

| Aspect | Decision |
|---|---|
| Style | REST over HTTPS, JSON. Base path `/api/v1`. Version bump only for breaking changes; additive changes are non-breaking. |
| Framework | FastAPI (async), Pydantic v2 request/response models — strict validation, OpenAPI docs auto-generated (docs endpoint disabled in prod for non-admins). |
| Idempotency | Clients may send `Idempotency-Key` on `POST` (payments, imports, sync mutations, receipt re-issue). Server stores key→response for 24 h and replays on retry. Offline sync uses `client_mutation_id` with the same semantics. |
| Errors | Single envelope (below). Codes are stable strings; HTTP status per table. No stack traces (BR-U07). |
| Pagination | Cursor-based default: `?cursor=<opaque>&limit=20` (max 100). Page-number mode tolerated on admin tables. Response meta: `{next_cursor, has_more, total?}`. |
| Filtering/sorting | `?status=ACTIVE&term_id=…&q=…` (q = name/code search), `sort=-created_at` (prefix `-` = desc), whitelist per endpoint. |
| Auditing | Mutating endpoints in sensitive domains write audit entries via service layer (§12). |
| Rate limiting | Redis token buckets per user+IP (§06); `429` with `Retry-After`. |

**Error envelope**

```json
{
  "error": {
    "code": "MARKS_TERM_CLOSED",
    "message": "Term 1 is closed; submit a correction request instead.",
    "details": [ {"field": "raw_score", "issue": "MAX_EXCEEDED", "max": 100} ],
    "request_id": "01958f3e-…"
  }
}
```

| Situation | HTTP | Example code |
|---|---|---|
| Validation failure | 422 | `VALIDATION_FAILED` |
| Unauthenticated | 401 | `AUTH_REQUIRED` |
| Forbidden (incl. resource scope) | 403 | `FORBIDDEN`, `NOT_ASSIGNED_CLASS` |
| Not found (or hidden by scope) | 404 | `NOT_FOUND` |
| Business rule violation | 409/422 | `TERM_CLOSED`, `WEIGHTS_SUM_INVALID`, `DUPLICATE_WEBHOOK` (200 no-op), `CLEARANCE_BLOCKED` |
| Locked state | 423 | `MARKS_LOCKED` |
| Provider failure | 502 | `PROVIDER_UNAVAILABLE` |
| Rate limit | 429 | `RATE_LIMITED` |

## 2. Endpoint catalog by domain (spec §42 groups)

> `⟨perm⟩` = required permission; `⟨scope⟩` = resource restriction enforced server-side.

### /auth
| Method & path | Purpose | Access |
|---|---|---|
| POST /auth/login | Login (username+password) → session cookie | public, rate-limited |
| POST /auth/logout | Revoke session | any session |
| GET /auth/me | Current user, roles, permissions, profile links | any session |
| POST /auth/password/change | Change own password (requires current) | any session |
| POST /auth/password/reset-request | Email/SMS reset token | public, rate-limited |
| POST /auth/password/reset-confirm | Consume token, set password | public (token) |
| POST /auth/account/recover | Guided recovery (admin-assisted flow issues token) | public, rate-limited |

### /users — `MANAGE_USERS`
GET list (filter role/status), GET one, POST create staff/parent/student logins, PATCH (status, profile), POST role assign/revoke (audited), POST unlock, POST reset-password-link.

### /students — `VIEW_STUDENT` / `EDIT_STUDENT`
GET list (filters: class, grade, status, gender, q; paginated) · GET `/{id}` full profile (enrollments, guardians, balances summary, clearance) · POST create (status APPLICANT/ADMITTED) · PATCH biodata (audited) · GET `/{id}/history` (enrollments + year-by-year results) · POST `/{id}/status` transition (lifecycle rules) · GET `/{id}/photo`, PUT photo (upload, compressed). *Scope: parents/students only self/children — enforced by scope, not permission alone.*

### /parents — `VIEW_PARENT` / `EDIT_PARENT`
GET list/search · GET one (children, contacts) · POST/PATCH · GET `/{id}/children` · POST `/{id}/links` (create relationship, audited) · DELETE link (soft, audited).

### /teachers — `VIEW_TEACHER` / `EDIT_TEACHER`
CRUD + GET `/{id}/assignments` · POST assignments (year/class/subject/role; validates conflicts).

### /classes — `VIEW_CLASS`
GET /grades · POST/PATCH grades (admin) · GET /streams?year= · POST/PATCH streams · GET `/{stream_id}/roster` · GET `/{stream_id}/assignments`.

### /subjects — `VIEW_SUBJECT`
CRUD subjects · GET/PUT grade-subject mapping.

### /enrollments — `EDIT_STUDENT`
GET list (year/class filters) · POST enroll (validates one-active-per-year) · POST `/{id}/withdraw|transfer` · **POST /enrollments/promotion** batch create (from→to year, mappings) · GET promotion preview (per-student suggestions) · POST apply (audited; per-student overrides in payload).

### /curriculum — `MANAGE_CURRICULUM`
GET curricula/versions · POST version (copy & edit) · POST publish · GET tree `?version=&grade=&subject=` (strands→…→indicators, paginated) · POST/PUT nodes (draft versions only) · GET/POST core competencies · POST bulk import (structured JSON/CSV).

### /assessments — `ENTER_MARKS` / `SUBMIT_MARKS` / `OVERRIDE_MARKS`
GET /schemes?year&term&grade · PUT scheme (weights; validates sum) · GET components · GET sheets `?class&subject&term` *(scope: assignments)* · POST/PUT sheet draft scores *(offline sync target)* · POST `/{sheet}/submit` · POST `/{sheet}/lock` (admin/head) · POST corrections request (teacher, reason) · POST corrections `/{id}/approve|reject` (admin; applies ScoreOverride; audited) · GET results `?class&subject` computed table · GET /grade-scales CRUD.
Also: GET/PUT ECD `developmental-ratings` `observation-logs` (ECD scope), POST competency-ratings.

### /attendance — `ENTER_MARKS` (reuse attendance perm set: `MANAGE_ATTENDANCE`)
GET/PUT sheet `?class&date` *(scope: assignments)* · POST submit · GET summaries `?class|student&period=week|month|term` (percentages, stats) · GET compliance (roll-call report).

### /reports — `VIEW_REPORT` / `MANAGE_REPORTS`
GET templates · PUT template config · POST generate (student/term or bulk class) · GET `/{report}/pdf` *(scope: own child/self; clearance enforced at publish boundary)* · POST finalize · POST publish (clearance gate) · POST republish-override (audited) · GET bece-results CRUD w/ kind labels.

### /fees — `VIEW_FINANCE` / `MANAGE_FEES`
GET/PUT structures (year/grade/band) · GET items · POST billing-run (preview → apply; audited) · GET charges `?student|class&status` · POST manual charge · POST waiver/discount/scholarship (approval, reason; audited) · POST adjustment · GET/POST payment plans · GET balances (derived) · GET clearance states · PUT clearance policy · POST clearance override (audited).

### /payments — `CREATE_PAYMENT` / `VIEW_FINANCE`
POST initiate (method, amount, student, allocate hint) → provider adapter · GET `/{id}` status · POST cash-confirm (bursar; issues receipt immediately) · POST `/{id}/reverse|refund` (`VOID_PAYMENT`; audited) · GET allocations · PUT reallocate (audited).

### /payments/webhooks — provider callbacks
POST `/api/v1/payments/webhooks/{provider_code}` — signature verification → `WebhookEvent` persisted → idempotency check → apply (ledger+receipt+notification) → 200. Invalid signature: 200 recorded, no apply (avoid provider retries storms), alert raised. *(No auth cookie required; HMAC secret per provider config.)*

### /receipts — `VIEW_FINANCE`
GET `/{id}` · GET `/{id}/pdf` · POST `/{id}/void` (`VOID_PAYMENT`, reason; audited) · GET list (date range, method).

### /communications — `SEND_COMMUNICATION`
POST broadcast (audience: school/grade/class/guardians-of-debtors, channels) · GET notifications (own) · POST notifications/read · GET sms-log (status filters) · GET/PUT templates · POST retry-failed.

### /appraisals — `APPRAISE_TEACHER`
GET criteria · PUT criteria config · POST appraisal (evaluator, teacher, period) · PUT scores (draft) · POST submit · POST acknowledge (teacher self) · GET history. *Confidentiality: teacher sees only own after submit; evaluators see own targets; head/admin see all.*

### /discipline — `VIEW_DISCIPLINE` / `MANAGE_DISCIPLINE`
GET list (restricted roles) · POST incident · PATCH status/resolution · POST notify-parent (creates notification/SMS draft). 

### /imports — `IMPORT_DATA`
GET templates (CSV/XLSX download) · POST upload (multipart; stored) · POST `/{job}/parse` · GET `/{job}/preview` (rows, errors, warnings, duplicates, parent match candidates w/ confidence) · POST `/{job}/resolve-match` (confirm/skip parent links) · POST `/{job}/confirm` (atomic import) · GET `/{job}/report` · GET history.

### /settings — `MANAGE_SETTINGS`
GET/PUT school profile · GET/PUT settings keys · GET/PUT active year/term (audited) · POST term close/reopen (reason) · GET/PUT grading scales · GET providers (configs; secrets never returned).

### /audit — `VIEW_AUDIT` (Super Admin, Head)
GET log (filters: actor, action, entity, range; paginated) · GET `/{id}` diff view. **Read-only; no write/delete endpoints.**

### Platform
GET `/healthz` (liveness), `/healthz/ready` (DB, Redis, storage checks) · GET `/api/v1/meta/bootstrap` (frontend startup bundle: school profile, active year/term, current user perms — one request, small payload, cached) · POST `/api/v1/sync/mutations` (offline batch sync, §09).

## 3. Cross-cutting implementation notes

- **Dependency-injected guards:** `require(Permission.X, scope=...)` FastAPI dependencies — authorization is code-adjacent to each route (REQ-API-02, BR-U04).
- **Repository layer** appends `school_id` and scope predicates to every query; services never assemble SQL strings (SQLi posture, §12).
- **OpenAPI** published internally; prod hides interactive docs behind admin flag.
- **Payload discipline:** list endpoints return summary projections; heavy joins (full profile) only on detail endpoints; `fields=` sparse option for low bandwidth (REQ-LOW-01).
