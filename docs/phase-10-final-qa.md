# Phase 10 — Final QA and Refinement Record

**Course:** INFT 255 — System Analysis & Design
**Record date:** 17 November 2026 (UTC)
**Deliverable:** `inft255-learning-environment.html` — standalone offline-first HTML/CSS/JavaScript learning environment
**Status:** Core implementation QA completed. The app is ready for use as an author-created learning environment, with the external-access and real-device/assistive-technology limits stated below.

## 1. Scope reviewed

This phase reviewed the already approved, integrated Modules 1–7 rather than regenerating them. The review covered:

- source-labelled guided instruction, original text/HTML visuals, labs, questions, feedback, subjective guides, and capstone workflows;
- navigation, routing, search, saved actions, notes, resource filters, assessment review flags, dashboard evidence, and local persistence;
- import/export normalisation and invalid-import feedback;
- breakpoint rules, dense-card wrapping, action target sizes, focus flow, dynamic announcements, and semantic structure;
- the rendered resource catalogue’s external-link safety/disclosures; and
- the appearance/wording consistency of the assessment, search, resource, portfolio, dashboard, and narrow-screen states.

## 2. Refinements made during final QA

| Area | Refinement | Reason |
|---|---|---|
| Academic precision | Reworded M2-Q12’s verification/validation feedback. It now says that the course distinction treats reviews/inspections as verification and validation as evidence of intended-use fitness, often through execution or user evaluation; it explicitly notes that terminology can vary by standard. | Avoids presenting an oversimplified testing distinction as universal. |
| Assessment continuity | Replaced the obsolete assessment-side message “0 durable score in this phase” with “Local — durable evidence · no official score.” | The app does now store objective evidence locally, while still not claiming an official grade. |
| Mobile/narrow layout | Resource-card footers now wrap their actions; narrow search results stack actions under their text. | Prevents action collisions/overflow in dense cards on small screens. |
| Keyboard accessibility | Added visible `:focus-visible` treatment to inputs and textareas; opening the mobile drawer moves focus to its first destination; Escape closes it and restores focus to the menu button. | Makes dynamic navigation and form focus more predictable. |
| Toggle semantics | The theme control now exposes `aria-pressed` alongside its state-specific label. | Communicates the toggle state to assistive technology. |
| Touch ergonomics | Header icon controls and secondary actions use a 44 px minimum target. | Reduces compact-control precision demands without removing keyboard access. |

The prior integration accessibility corrections remain in place: the XP indicator uses valid progressbar semantics, and the evidence panel is not a nested complementary landmark.

## 3. Academic and content moderation record

### 3.1 Bank and source-integrity checks

A data audit of the embedded canonical banks verified:

- **100 MCQs**, with module distribution M1 15, M2 15, M3 18, M4 16, M5 17, M6 16, M7 3;
- **20 subjective prompts/model guides**, with no missing prompt, model, guide, or source field;
- **no duplicate MCQ IDs**, four options per MCQ, valid answer indices, and no duplicated option text within an item;
- the reviewed cognitive distribution: Remember 16, Understand 24, Apply 28, Analyse 21, Evaluate 11; and
- `official: false` on every objective item and subjective guide. The UI retains the corresponding non-official feedback disclosure.

The review retained the documented source boundary: C1 is the supplied full-course authority, supported by Week 1–5 lecturer decks; standards and publications provide labelled supplemental context only. Worked examples, the simulated registration/payment case, XP thresholds, and subjective model guides remain author-created and are not represented as lecturer-approved answers, institutional facts, or official marks.

### 3.2 Topic accuracy/coverage review

The final content pass checked that:

- M1 distinguishes purpose, boundary, IPO, control, feedback, constraints, and analysis-versus-design decisions without treating a single system classification as universal;
- M2 treats methodology as a contextual trade-off, preserves the SDLC/refinement distinction, presents Spiral as risk-driven and UP as overlapping workflows, and now gives standards-aware verification/validation wording;
- M3 exposes NPV/payback inputs, critical-path arithmetic, slack, and risk/issue/response distinctions rather than returning opaque conclusions;
- M4 keeps DFD data movement separate from UI/control-flow modelling, preserves balancing and black-hole rules, and uses an associative entity for relationship-specific Student–Course facts;
- M5 distinguishes class/object/attribute/operation/message, goal-level use cases, supported UML relationship claims, multiplicity, and required/provided interfaces;
- M6 keeps logical component/layer decisions separate from artifacts/nodes, and correctly differentiates sequence, communication, activity, and state-machine purposes while requiring cross-model consistency; and
- M7 requires assumptions to remain visible and connects requirements, model choices, constraints, validation, timeboxing, and final presentation rather than rewarding decorative diagrams.

No new fabricated course assertions, lecturer key claims, or unsupported real-institution claims were introduced in this phase.

## 4. Functional, persistence, and link QA

### 4.1 Verified functional paths

The JSDOM QA suite exercised all principal local flows:

- seven routed screens, dynamic current-page state, focus-on-route behaviour, all seven Guided Study modules, flashcard/lab routes, Case Studio persistence, search/bookmark routing, resource filters, mobile-menu keyboard behaviour, and theme toggle state;
- all **44** Systems Lab activities: **42 scored selection activities** accepted their expected correct choices, and the economic calculator and 60-minute timebox emitted working/interpretation feedback;
- objective practice in topic/mixed/timed modes, delayed timed explanations, assessment flag-for-review summary, and hidden-on-request subjective guides;
- local objective/lab/daily evidence, dashboard updates, normalised JSON export/import, XP/badge recalculation, portfolio notes and bookmarks through backup/restore; and
- replacement acknowledgement plus invalid JSON/unsupported-backup import error messages.

### 4.2 Resource and external-link review

The dynamically rendered catalogue was audited rather than incorrectly looking for static anchors in the HTML source. It contains:

- **17** resource records: **14** external HTTPS destinations and **3** offline practical routes;
- an external card for every remote URL with `target="_blank"` and `rel="noopener noreferrer"`;
- a title, creator/institution/channel, module/topic, “pay attention to,” educational value, verification status, and access note on every card; and
- explicit labels for both course-bibliography search suggestions as unverified suggestions.

The 14 destinations use the recorded direct URLs for Ghana Legal Information Institute, NIST, IEEE, SEI, OMG, arXiv, YouTube, and the two disclosed Google search suggestions. Phase 7 recorded the original metadata/access verification on 17 November 2026. This final phase validates the catalogue structure and safe rendered link attributes; it does **not** claim that an external host, a paywalled record, a video, or a search result will be reachable from every learner network at every future time.

### 4.3 Accessibility and responsive review

- `axe-core` 4.10.2 reported **0 violations** in JSDOM with `color-contrast` disabled. JSDOM cannot reliably calculate rendered colour contrast, so that result is not a colour-contrast certification.
- Static semantic review confirmed one primary navigation landmark, labelled module/lab navigation regions, labelled visual alternatives, real form controls, a skip link, visible focus states, live regions for updates, progressbar values, reduced-motion CSS, and keyboard-equivalent interactions rather than drag-only tasks.
- Breakpoint review confirmed the main dense layouts collapse at 1030 px, the drawer/nav/library/lab states adapt at 760 px, and search, resource, terms, assessment, and model layouts collapse to a single column at 480 px. `minmax(0, …)` is used in wide grid content to reduce overflow risk.
- The runtime environment available for this review did not include a graphical browser/device emulator. Therefore, the recorded responsive review is a code-level/breakpoint and JSDOM interaction review, not a claim of empirical screen-reader, device, or rendered-colour testing. A live static preview was started for real-browser inspection.

## 5. Exact automated checks run

All following checks passed against the final HTML after the Phase 10 refinements:

1. Python `HTMLParser` parse of the full document.
2. Inline-script extraction followed by `node --check`.
3. Canonical-content data audit: 100/20 totals, IDs, options, answer bounds, source/model/guide completeness, official-status boundary, and cognitive/module distributions.
4. Existing JSDOM assessment/resource smoke test.
5. Existing JSDOM progress and import/recalculation tests.
6. Existing JSDOM Guided Study/Case Studio integration test.
7. JSDOM global search/bookmark test.
8. JSDOM export/import test, including portfolio note, bookmark, and derived-XP recomputation.
9. JSDOM timed assessment review-flag test.
10. JSDOM comprehensive routing test for all screens, all 44 lab render paths, seven guided modules, all resource filters, mobile-menu Escape/focus, theme pressed state, and page focus.
11. JSDOM all-labs interaction test for the 42 scored activities plus the calculator and timebox workflows.
12. JSDOM rendered-resource audit for 17 cards, 14 HTTPS/safe external links, three local routes, and mandatory disclosure metadata.
13. JSDOM persistence-error test for import acknowledgement and malformed/unsupported backup feedback.
14. `axe-core` semantic run (0 violations, contrast rule excluded as documented).
15. Resource-data URL inventory and `git diff --check`.

## 6. Completion boundary and operational limits

The standalone product is complete for the approved instructional scope: it works offline for core instruction, labs, assessments, search, bookmarks, notes, evidence, and backup/restore. It is intentionally **not** an institutional LMS, a secure gradebook, a free-response auto-marker, a professional unrestricted diagram editor, legal advice, or a source of verified stakeholder evidence.

Before formal course deployment, a course owner should still make a real-browser/device and assistive-technology pass in the intended environment, validate the current availability/licensing of optional external links, and replace author-created model guidance if an official lecturer rubric or answer key is later supplied. Those are deployment validation activities, not claims that the offline core is missing.
