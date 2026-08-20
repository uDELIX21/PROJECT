# 07 · Curriculum, Assessment, Attendance & Report Cards

**Status:** Draft for approval · **Covers:** deliverable items 12–13 (incl. BECE separation)

---

## 1. Curriculum architecture (REQ-CUR-01..04)

### 1.1 Structure (NaCCA-shaped, not NaCCA-hardcoded)

```
Curriculum ("NaCCA Basic School Curriculum")
  └─ CurriculumVersion ("2026.v1", PUBLISHED)
       └─ (Grade × Subject) scoping
            └─ Strand → Sub-Strand → Content Standard → Indicator
                                                  └↔ Core Competency (M:N)
```

- **Versioning rule (BR-C01/02):** publishing a version freezes it. Curriculum edits happen in a new `DRAFT` version (copy-forward tooling provided). Assessment/lesson references store concrete `indicator_id` → historical data always resolves to its original wording.
- **Data entry:** tree editor UI (drag/order, bulk paste) + structured CSV/JSON import (`/curriculum` endpoints). Nothing in application code assumes strand counts, codes, or subject lists (REQ-CUR-01).
- **Core competencies:** seeded catalog from spec §6 list; school may add. Ratings per enrollment per term are qualitative (`competency_ratings`), rendered on report cards (BR-C04).
- **Coverage tracking (lightweight, v1):** teachers may tag assessments/observation logs with indicators; dashboards show % of indicators touched per subject/class/term. No lesson-plan module in v1.

### 1.2 Version selection
Active version per (grade, subject) is a school setting entry; scheme/report rendering reads through it. Switching versions mid-year is allowed but audited; existing score records keep their original indicator links.

---

## 2. Assessment architecture (REQ-ASM-01..03, REQ-MRK-*)

### 2.1 Configurable scheme model

```
AssessmentScheme (academic_year × term × grade × subject?)   ← most specific wins
  ├─ component CLASS_SCORE   weight 50%  max 100   (Primary default config row)
  └─ component TERMINAL_EXAM weight 50%  max 100
JHS example config row: CLASS_SCORE 30% / TERMINAL_EXAM 70%
```

- Weights live in `assessment_components` rows — **never in code** (REQ-ASM-01). UI validates Σ=100; DB assertion backs it (BR-M01).
- A component can be filled by a **single direct entry** or by **multiple assessments** under it (e.g., 3 quizzes under CLASS_SCORE) aggregated by mean (aggregation mode configurable per component: `DIRECT | MEAN | BEST`).

### 2.2 Score pipeline (BR-M02)

```
raw scores (per assessment)
  → normalize: raw / max × 100
  → aggregate per component (mean/best/direct)
  → weighted: component_aggregate × weight_pct / 100
  → final_score = Σ weighted components            (0–100)
  → rounding per school setting (default: half-up, 1 dp)
  → grade + remark via GradeScale lookup (most specific scale)
```

- Deterministic pure function `compute_final(scheme, scores) → FinalResult` — unit-tested exhaustively (REQ-TST-01).
- Results are computed on demand and snapshotted into `report_cards.data_snapshot` at finalization (immutability, REQ-CAL-05).
- **Class positions:** optional; when enabled, computed per class stream per subject and overall (mean of subjects), with tie rule (same score ⇒ same position, next skipped). Configurable school setting D2.

### 2.3 Marks workflow & locking (REQ-MRK-02, BR-M03/04)

| State | Who | What |
|---|---|---|
| DRAFT | assigned teacher | free edits; offline-capable (§09) |
| SUBMITTED | teacher (`SUBMIT_MARKS`) | validated (range, completeness warnings acknowledged); read-only thereafter |
| LOCKED | head/admin or term closure | corrections only via override workflow |

**Correction workflow:** teacher POSTs correction request (original score, proposed score, reason) → head/admin with `OVERRIDE_MARKS` approves/rejects → on approval a `score_overrides` row + audit entry (actor, approver, reason, timestamps) and the new value applies; original preserved in audit + override row (Agent Rule: no silent modification).

### 2.4 Grading scales (REQ-GRD-01)

- `grade_scales` + bands fully configurable (ranges, codes, remarks, ranks). Scoping resolution order: (grade+year) → band+year → band → school default.
- **Seed defaults are configuration, not policy** (AM3): e.g., Primary default scale `A 80–100 Excellent … F 0–39 Fail` (illustrative, editable), JHS may use the same or a 9-point-style scale **if the school configures it** — the system imposes nothing.
- Post-submission scale edits do not rewrite finalized snapshots; non-finalized views recompute (documented behavior).

### 2.5 Early childhood assessment (REQ-ECD-01..04, BR-E)

- Bands EARLY_CHILDHOOD bypass numeric schemes entirely (guard in services + UI).
- **Domains** (configurable, seeded from spec §7): Gross Motor, Fine Motor, Language/Speech, Cognitive, Social, Emotional, Self-Care, Creativity, Teacher Observation.
- **Ratings:** Emerging / Developing / Achieved (configurable vocabulary).
- **Observation logs:** dated notes per child (append-only revision chain), feed the ECD report summary.

### 2.6 BECE separation (REQ-BEC-01, Agent Rules 1–2)

`bece_style_results.kind`:

| Kind | Meaning | Display rule |
|---|---|---|
| SCHOOL_EXAM | school's own JHS exams | normal |
| MOCK | school-run mock | labelled "School Mock — not official" |
| PREDICTION | school-generated prediction | labelled "School prediction — not an official BECE result" |
| OFFICIAL | manual transcription of official slip | labelled "Entered from official slip" (no computation) |

No 1–9 aggregation logic is implemented; grades/scores are exactly what staff enter. UI refuses to print prediction records without their label (template enforces).

---

## 3. Attendance (REQ-ATT-01..03, BR-T)

- **Sheet per class per day** (`attendance_sheets`): taken by assigned teacher/form teacher; statuses per spec §12.
- **Scope guard:** only teachers with an active assignment for the stream may take/edit its roll (server-enforced).
- **Summaries:** reusable query service computes daily/weekly/monthly/term aggregates:
  - per-student % (weights configurable, BR-T02), per-class stats, top-absence list;
  - **roll-call compliance:** expected school days (term calendar minus weekends/holidays from settings) vs submitted sheets per class/teacher → dashboard table (REQ-ATT-02).
- Offline entry supported (§09); sheet `version` column guards concurrent-edit conflicts.

---

## 4. Report card architecture (REQ-RPT-01..05, BR-R)

### 4.1 Pipeline

```
finalize term data (marks + attendance + ratings + remarks)
  → render HTML from ReportTemplate (Jinja2; band-specific base layout)
  → WeasyPrint → PDF → stored_files (S3/local) → report_cards.pdf_file_id
  → clearance check → publish → parent/student portal + downloadable link
```

### 4.2 Template families (3 base layouts, each configurable)

| Section | EC | Primary | JHS |
|---|---|---|---|
| Header: logo/crest, school name, motto, contacts, digital address | ● | ● | ● |
| Student info block (name, code, class, gender, year/term, position if enabled) | ● | ● | ● |
| Academic table (subject, class score, exam, total, grade, remark, position) | — | ● | ● |
| Developmental domains grid + observations summary | ● | — | — |
| Core competencies ratings | ● | ● | ● |
| NaCCA indicator summary (optional flag per template) | opt | opt | opt |
| Attendance block (days present/absent/late, %) | ● | ● | ● |
| Remarks: class teacher → head teacher (editable text, audited) | ● | ● | ● |
| Signature slots (uploaded images) + promotion status line | ● | ● | ● |

- `layout_config` JSONB controls section toggles, column labels, language of remarks headers, position display, pass-mark display — templates are school-editable without code changes (REQ-RPT-04).
- **Immutability:** `data_snapshot` frozen at finalization; regeneration after finalization requires audited override (BR-R03).
- **Clearance gating:** publish action consults `financial_clearances` for type `REPORT_CARD`; BLOCKED ⇒ 409 `CLEARANCE_BLOCKED` unless WAIVED/MANUAL_OVERRIDE (BR-R02). Exam clearance (type `EXAMINATION`) is consulted by the exam-entry UI and printable exam dockets (v1: state surfaced on teacher dashboard).

### 4.3 Distribution
- Parent portal lists published reports per child; PDF streaming endpoint scoped by relationship.
- Bulk generation per class is queued (background worker) with progress status — avoids long HTTP requests on low bandwidth (REQ-LOW-01).

### 4.4 Failure handling (REQ-ERR-01)
PDF failures return `PDF_GENERATION_FAILED` with retry action; partial class batches continue per-student and report failures individually.
