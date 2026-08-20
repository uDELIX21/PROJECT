# 12 · Audit, Security & Data Privacy Architecture

**Status:** Draft for approval · **Covers:** deliverable items 20–21

---

## 1. Audit architecture (REQ-AUD-01..03)

### 1.1 What is audited (mandatory set, BR-U06)

| Domain | Actions recorded |
|---|---|
| Academic | grade/score override (original→new), sheet submit/lock/unlock, term close/reopen, report finalize/publish/republish-override, scheme & grading-scale changes |
| Financial | every ledger posting (via document refs), payment void/reversal/refund, receipt void, waivers/adjustments, clearance override, billing run, fee structure changes |
| People | student biodata change, status transition, enrollment/withdrawal, promotion batch apply, parent link create/confirm/remove, pickup authorization changes, user create/lock/deactivate, role grant/revoke, password changes/resets |
| System | settings changes (key, old, new), import commit/rollback, template changes, provider config changes |

### 1.2 Record shape & integrity

- `audit_log` row: actor, action, entity type+id, previous/new JSONB, reason (required where workflow defines one), IP + user agent, timestamp (§04/3.4).
- **Immutability:** application DB role has INSERT-only grants on `audit_log`; no UPDATE/DELETE. Optional hash-chain (`row_hash = H(prev_hash || row)`) enabled in production for tamper-evidence; chain verified by a scheduled integrity job whose result shows on the admin health page.
- **Writes happen in the same service-layer transaction** as the business change (audit cannot lag behind or be skipped by a code path — enforced by requiring all sensitive mutations to go through audited service methods; lint/test verifies).

### 1.3 Access

- `VIEW_AUDIT` (Super Admin, Head; Bursar finance-scoped view). Read-only API + UI with filters (actor, action, entity, date range) and diff viewer.
- Audit UI is ordinary-user-invisible (RBAC); audit rows excluded from all other API responses (REQ-AUD-03).
- Retention: 7 years default (school setting), then export-to-cold-storage + delete; deletion itself logged via a signed retention job record.

---

## 2. Security architecture (REQ-SEC-01..02)

### 2.1 Application controls

| Control | Implementation |
|---|---|
| Password storage | Argon2id (§06) |
| Sessions/CSRF | HttpOnly Secure SameSite=Lax cookies + CSRF double-submit; session revocation |
| Authorization | RBAC + resource scopes server-side only (BR-U04, Agent Rule 6) |
| Input validation | Pydantic models everywhere; strict enums; length limits; no mass-assignment (explicit field maps) |
| SQL injection | SQLAlchemy ORM/parameterized only; no string-built SQL; DB user least-privilege |
| XSS | React escaping by default; server-rendered PDF/HTML templates escape all data; rich-text avoided (plain-text remarks only in v1) |
| Headers | CSP (strict, no `unsafe-eval`), HSTS, X-Content-Type-Options, X-Frame-Options DENY (app is not embeddable), Referrer-Policy, Permissions-Policy |
| Rate limiting | Redis buckets: login, resets, webhooks (per provider IP allowlist too), broadcast sends, generic API (§06) |
| File uploads | allowlist: jpeg/png/webp (photos/logos/signatures), pdf, csv, xlsx; magic-byte sniffing (extension alone rejected); size caps (photos 5 MB, imports 10 MB); stored outside webroot with signed URLs; filenames sanitized; images stripped of EXIF GPS on upload |
| Secrets | env vars only (`.env` never committed); DB stores only env-var **names** for provider credentials; `/settings` API never returns secret values (REQ-SEC-02); `.env.example` documented |
| Dependencies | `pip-audit` + `npm audit` in CI; lockfiles committed; dependabot-style weekly PRs |
| Transport | HTTPS-only in prod (HSTS + redirect); dev uses http://localhost only |

### 2.2 API hardening
- Uniform 404 for out-of-scope resources (prevents ID probing — REQ-PRV-02; IDs are UUIDv7 anyway).
- No user enumeration: login/reset responses identical for unknown identifiers; lockout is per-account internal only.
- Webhook endpoints: HMAC verification, replay window (5 min timestamp check), source logging.
- Error handling: internal exceptions → generic code + `request_id`; full detail only in server logs (BR-U07, REQ-ERR-01).

### 2.3 Infrastructure
- Single VPS baseline (§13): host firewall (only 80/443/SSH), fail2ban on SSH, non-root containers, Postgres binds loopback (or private network), Redis loopback only, unattended security updates.
- DB roles: `sms_app` (no DDL in prod, no DELETE on ledger/audit), `sms_migrator` (DDL during deploy), `sms_readonly` (reporting/backup).

---

## 3. Data privacy (REQ-PRV-01..02; spec §36)

**Framework context:** Ghana's Data Protection Act, 2012 (Act 843) — the school is data controller; the system implements the technical side: lawfulness-by-role, minimization, access control, retention. No policy claims beyond what the school adopts.

| Principle | Implementation |
|---|---|
| Minimization | Fields collected are those the school operates (spec §14 lists); optional fields stay optional; medical notes are a restricted sub-section (VIEW_STUDENT + explicit flag) |
| Access control | Relationship-scoped parent access; assignment-scoped teacher access; student self-only; discipline & appraisal confidentiality (REQ-DIS-01, REQ-APR-01) |
| No ID-based access | Resource ownership checks on every detail endpoint; 404 for out-of-scope (REQ-PRV-02) |
| Photos | Uploads access-controlled; parent/child photos never served publicly; signed short-lived URLs |
| Retention | Graduate/withdrawn student records retained per school policy setting; PII export + restrict-processing actions available to Super Admin (supports school responding to data-subject requests) |
| Seed data | 100% fictional, watermarked (Agent Rule 12; REQ-SEED-02) |
| Logs | PII scrubbing in structured logs (phone/email masked) |
