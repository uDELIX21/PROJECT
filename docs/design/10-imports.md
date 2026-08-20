# 10 · Bulk Import Architecture (CSV/XLSX)

**Status:** Draft for approval · **Covers:** deliverable item 18

## 1. Pipeline (REQ-IMP-04)

```
Upload → Parse → Validate → Preview → Confirm → Import → Report
  │        │        │          │         │         │        └─ counts, error file download
  │        │        │          │         │         └─ single DB transaction (BR-I01)
  │        │        │          │         └─ admin accepts preview; unresolved ERROR rows block commit
  │        │        │          └─ row grid: ok / error / warning / duplicate / parent-match-candidate
  │        │        └─ field rules, enums, dates, phone normalization, duplicates (BR-I02)
  │        └─ csv (stdlib) / xlsx (openpyxl read-only streaming); encoding sniff (utf-8/latin-1)
  └─ multipart upload → stored_files (purpose=IMPORT_FILE), ImportJob row created
```

Job stages map to `import_jobs.stage` (§04); every transition audited with actor.

## 2. Templates (REQ-IMP-02)

Downloadable CSV **and** XLSX samples with header row + 2 example rows + comments sheet:

| Import | Columns (v1) |
|---|---|
| **Students** | admission_code (optional), surname, other_names, gender, date_of_birth, class (stream name e.g. `Basic 4A`), status, guardian_name, guardian_relationship, guardian_phone, guardian_email, guardian_address, ghana_digital_address, opening_balance_ghs |
| **Teachers** | staff_code, surname, other_names, gender, phone, email, job_title, qualification, hired_on, primary_class, assigned_subjects (`;`-separated subject codes) |
| **Parents** | name, relationship_to, student_admission_code OR student_name, phone, phone2, email, occupation, residential_address, ghana_digital_address, latitude, longitude, preferred_channel, contact_window |

Templates are generated from a single schema definition (drift-proof: validation and template share one source).

## 3. Validation & error reporting (REQ-IMP-03)

- **Field level:** required, enums (`gender F/M`), date formats (`YYYY-MM-DD` primary; `DD/MM/YYYY` accepted), phone → E.164 `+233…` normalization (reject non-Ghana with clear message), amounts → pesewas (2-dp string parse, reject negatives).
- **Row level:** unknown class name ⇒ suggest nearest (`Did you mean Basic 4A?`); duplicate students (admission code exact OR fuzzy name+DOB ≥ threshold) flagged `DUPLICATE` with existing record link and action: skip / create-anyway / link-existing.
- **Cross-row:** duplicate admission codes within file; conflicting guardian links for one student.
- Every issue: `{row, field, severity, message, guidance, raw_row}` → preview grid + downloadable error report (CSV) after the run.

## 4. Parent matching (REQ-PAR-04, Agent Rule 8 — never auto-link)

1. Normalize phones; look up existing guardians.
2. Candidate scoring: exact phone match after normalization = **high**; phone + surname match = **very high**; name-only fuzzy = **low (not shown by default)**.
3. Candidates surface in preview as `MATCH_CANDIDATE` rows with confidence and both records side-by-side.
4. Admin resolves each: **Link** (creates `parent_student_relationships` with `source=IMPORT_SUGGESTION`, `confirmed_by=admin`) · **New guardian** · **Skip row**.
5. Every link decision is logged (ImportJob + audit). Multiple children per guardian fully supported (spec §15–16).

## 5. Transactional commit & rollback (REQ-IMP-03, BR-I01)

- Commit runs inside **one transaction**; per-entity-type insertion order: guardians → students → relationships → enrollments → opening-balance ledger entries → teacher users/assignments.
- Constraint/business failure ⇒ full rollback, job `ROLLED_BACK`, nothing persisted (spec: "Do not partially corrupt the database").
- Opening balances → `OPENING_BALANCE` debits with `idempotency_key=import:{job_id}:{row}` (AM9, BR-F12).
- Opt-in **staged mode** (admin checkbox): valid rows commit, errors skipped — implemented with savepoints and an explicit warning that the result is partial; off by default.

## 6. Concurrency & limits

- One active job per kind per school (lock row); files ≤ 10 MB / 20k rows in v1 (limits surfaced in UI).
- Imports refuse closed years/terms (BR-I04); target year/term is a confirmed job option.

## 7. History & observability

- `import_jobs` history list (actor, counts, duration, report download); old files retained per retention setting (default 1 year) then purged from storage (metadata kept).
- Metrics: job duration, error-rate trend → admin status page (§13 doc).
