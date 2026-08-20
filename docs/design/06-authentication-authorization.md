# 06 · Authentication Architecture & RBAC/Permission Matrix

**Status:** Draft for approval · **Covers:** deliverable items 10–11

## 1. Authentication architecture

### 1.1 Mechanism choice
Browser-first **server-side sessions** (stored in `sessions` table, Redis cache for hot lookups):
- Revocable instantly (deactivation, password change) — important for a school with shared devices.
- No token handling in client JS beyond a cookie; CSRF protected.
- Same mechanism serves PWA fetches (same-origin). A future native app can add a token grant without redesign (session → opaque bearer mapping).

### 1.2 Credential security
| Item | Rule |
|---|---|
| Hashing | **Argon2id** (memory 64 MB, t=3, p=4); legacy bcrypt auto-upgraded on next login. |
| Password policy | min 10 chars; check against top-100k list; history of last 5 hashes blocks reuse. |
| Lockout | 5 failures → 15-min lock per account (`users.locked_until`); IP also bucket-limited (10/min). Counter reset on success. |
| Sessions | 12 h idle timeout (configurable); absolute 7 days; `Secure`, `HttpOnly`, `SameSite=Lax` cookie; session id stored hashed server-side. |
| CSRF | Double-submit: per-session CSRF token required in `X-CSRF-Token` on all state-changing requests (SameSite=Lax is not sufficient alone with our fetch usage). |
| Rate limits | login 5/min/IP+account; reset requests 3/hour/account; generic API 300/min/user (Redis buckets). |

### 1.3 Password reset & account recovery (REQ-TECH-07)
1. `reset-request`: user provides username/email/phone → if matched, single-use token (1 h expiry, hashed at rest) delivered via SMS (primary, Ghana context) and/or email; response is uniform (no account enumeration).
2. `reset-confirm`: token + new password → rotate password, revoke all sessions, audit.
3. **Assisted recovery:** for users without reachable contact (common), an admin with `MANAGE_USERS` issues a one-time recovery code in person; use is audited.

### 1.4 Login flow
```
POST /auth/login {username, password}
  → verify argon2 → check lock/status → create session row
  → Set-Cookie sms_session=…; HttpOnly; Secure; SameSite=Lax; Path=/
  → response: {user, roles, permissions, active_year/term}
```

## 2. RBAC model

- Tables: `roles`, `permissions`, `role_permissions`, `user_roles` (§04).
- **Permission catalog is fixed in code** (authorization checks reference constants); roles are DB-configurable mappings onto the catalog. Six system roles are seeded; custom roles can be created by Super Admin.
- Enforcement is **two-layer**:
  1. **Permission gate** — route requires a permission code (fail closed, BR-U04).
  2. **Resource scope** — service predicates restrict visible/mutable rows (assignment-based for teachers, relationship-based for parents, self for students). Frontend hiding is cosmetic only (Agent Rule 6).

## 3. Permission catalog (REQ-RBAC-02)

| Code | Meaning |
|---|---|
| VIEW_STUDENT / EDIT_STUDENT | Student registry read/write |
| VIEW_PARENT / EDIT_PARENT | Guardian registry read/write |
| VIEW_TEACHER / EDIT_TEACHER | Teacher registry read/write |
| MANAGE_ASSIGNMENTS | Teacher↔class/subject assignments |
| MANAGE_CLASSES | Grades, streams, rosters |
| MANAGE_ENROLLMENT | Enroll, withdraw, promotion batches |
| MANAGE_CURRICULUM | Curriculum versions & tree |
| ENTER_MARKS | Draft/save scores & attendance sheets (assignment-scoped) |
| SUBMIT_MARKS | Submit mark sheets |
| OVERRIDE_MARKS | Approve score corrections / unlock sheets |
| MANAGE_ATTENDANCE | Attendance config & cross-class summaries |
| VIEW_REPORT / MANAGE_REPORTS | Report cards view / generate-finalize-publish & templates |
| VIEW_GRADES_CONFIG | Read grading scales & schemes |
| MANAGE_GRADES_CONFIG | Edit grading scales & schemes |
| VIEW_FINANCE | Charges, balances, ledger, receipts read |
| MANAGE_FEES | Fee structures, billing runs, plans |
| CREATE_PAYMENT | Initiate/record payments |
| VOID_PAYMENT | Reverse/refund payments, void receipts |
| GRANT_WAIVER | Waivers/discounts/scholarships/adjustments |
| MANAGE_CLEARANCE | Clearance policies & overrides |
| IMPORT_DATA | Bulk imports |
| SEND_COMMUNICATION | Broadcasts, SMS |
| APPRAISE_TEACHER | Create/submit appraisals |
| VIEW_DISCIPLINE / MANAGE_DISCIPLINE | Discipline read/write |
| MANAGE_PICKUP | Pickup authorizations |
| MANAGE_USERS | User accounts & role grants |
| MANAGE_SETTINGS | School settings, terms open/close |
| VIEW_AUDIT | Audit log access |
| MANAGE_IMPORT_TEMPLATES | (bundled under IMPORT_DATA in v1) |

## 4. Role → permission matrix (initial seeding)

`●` granted · `◐` granted but **resource-scoped** (see §5) · `—` denied

| Permission | Super Admin | Headmaster | Bursar | Teacher | Parent | Student |
|---|---|---|---|---|---|---|
| VIEW_STUDENT | ● | ● | ◐ (finance views) | ◐ assigned classes | ◐ own children | ◐ self |
| EDIT_STUDENT | ● | ● | — | — | — | — |
| VIEW_PARENT / EDIT_PARENT | ●● | ●● | ◐/— | ◐/— assigned | ◐ self | — |
| VIEW_TEACHER / EDIT_TEACHER | ●● | ●● | — | ◐ self | — | — |
| MANAGE_ASSIGNMENTS / MANAGE_CLASSES | ●● | ●● | — | — | — | — |
| MANAGE_ENROLLMENT | ● | ● | — | — | — | — |
| MANAGE_CURRICULUM | ● | ● | — | ◐ read assigned subjects | — | — |
| ENTER_MARKS | ● | ● | — | ◐ assigned | — | — |
| SUBMIT_MARKS | ● | ● | — | ◐ assigned | — | — |
| OVERRIDE_MARKS | ● | ● | — | — (request only) | — | — |
| MANAGE_ATTENDANCE | ● | ● | — | ◐ assigned | — | — |
| VIEW_REPORT | ● | ● | ◐ (clearance context) | ◐ assigned class | ◐ own children (published) | ◐ self (published) |
| MANAGE_REPORTS | ● | ● | — | — | — | — |
| VIEW/MANAGE_GRADES_CONFIG | ●● | ●● | — | ◐ read | — | — |
| VIEW_FINANCE | ● | ● | ● | — | ◐ own children | ◐ self (if enabled) |
| MANAGE_FEES | ● | ● | ● | — | — | — |
| CREATE_PAYMENT | ● | ● | ● | — | — (pay link v2) | — |
| VOID_PAYMENT | ● | ● | — | — | — | — |
| GRANT_WAIVER | ● | ● | ◐ (propose; head approves) | — | — | — |
| MANAGE_CLEARANCE | ● | ● | ● | — | — | — |
| IMPORT_DATA | ● | ● | — | — | — | — |
| SEND_COMMUNICATION | ● | ● | ◐ (fee notices) | ◐ (assigned-class announcements) | — | — |
| APPRAISE_TEACHER | ● | ● | — | — | — | — |
| VIEW_DISCIPLINE / MANAGE_DISCIPLINE | ●● | ●● | — | ◐/◐ assigned students | ◐ own child (resolved summaries, configurable) | — |
| MANAGE_PICKUP | ● | ● | — | ◐ (EC form teachers view) | ◐ view own child's | — |
| MANAGE_USERS | ● | ◐ (non-admin accounts) | — | — | — | — |
| MANAGE_SETTINGS | ● | ◐ (not security-critical keys) | — | — | — | — |
| VIEW_AUDIT | ● | ● | ◐ (finance-scoped) | — | — | — |

**Notes**
- **Super Admin** additionally manages providers, backups console, and system health — and is the only role that can edit security-critical settings keys.
- **Bursar** cannot override marks or edit students; finance-only separation of duties.
- **Teacher** powers derive entirely from active `teacher_assignments`; removing an assignment removes access immediately (server-scoped).
- **Parent** permissions are meaningless without the relationship scope; API resolves children via `parent_student_relationships` each request.
- Role matrix itself is editable (except revoking the bootstrap Super Admin guard); all grants/revokes are audited (BR-U06).

## 5. Resource scoping rules (authorization layer detail)

| Actor | Rule |
|---|---|
| Teacher | Classes/subjects visible = `teacher_assignments` rows for the **active academic year** (or selected historical year if `VIEW_REPORT` scope allows read-only). Mark/attendance writes additionally require the term ACTIVE (BR-A03). |
| Parent | Students visible = linked children with active or historical relationship; finance = billed children (`is_billing_contact` or primary); reports = published only; discipline = resolved summaries if school setting enables. |
| Student | Only own records; fee visibility controlled by school setting (default: fees shown at summary level only). |
| Bursar | All students in finance context; no biodata edits; receipt/payment scope school-wide. |
| Everyone | Every query passes through repository scope predicates; direct-ID access to another tenant's/scope's row returns 404 (prevents ID probing, REQ-PRV-02). |

## 6. Session & token lifecycle events (audited)

login.success, login.failed, login.locked, logout, session.revoked, password.changed, password.reset_requested/used, recovery.code_issued/used, role.granted/revoked.
