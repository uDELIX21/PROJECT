# Phase 9 — Final Integration Review

**Course:** INFT 255 — System Analysis & Design
**Scope:** Reconcile approved Modules 1–7, assessments, resources, learner evidence, and Case Studio in the single standalone HTML application.
**Status:** Historical integration record. The integration changes were implemented and smoke tested; subsequent final QA/refinement is recorded in `docs/phase-10-final-qa.md`.

## 1. Integration work completed

### 1.1 Guided Study now spans the full course path

The former Module 1-only Learn view is now a dynamic **seven-module Guided Study** path:

| Module | Integrated guided instruction | Linked action |
|---|---|---|
| M1 | systems purpose/boundary/IPO/control/feedback; analysis versus design | M1 Systems Lab and topic practice |
| M2 | SDLC gradual refinement, methodology trade-offs, UP workflows | M2 lab and topic practice |
| M3 | feasibility, economic/schedule assumptions, risk response | M3 lab and topic practice |
| M4 | testable requirements, DFD rules/balancing, ERD relationship data | M4 lab and topic practice |
| M5 | OO responsibilities, use cases, relationships, components | M5 lab and topic practice |
| M6 | layers, deployment, interaction/workflow/state models, cross-model validation | M6 lab and topic practice |
| M7 | concept bridge, case planning, assumptions, final package consistency | M7 lab and topic practice |

Every module view includes a source label, objective, three concise guided explanations, key terms, an original text/HTML visual with accessible text alternative, and a functional retrieval flashcard. Guided-reading clicks are intentionally not mastery/XP evidence. Each view routes learners to the relevant interactive Systems Lab and topic assessment.

### 1.2 Case Studio portfolio is now locally coherent

The Portfolio screen now supports:

- an editable case/project name;
- one local artefact note per M1–M7 module;
- source-integrity/assumption reminder;
- note save/clear feedback and module note-status inventory; and
- inclusion of portfolio notes in the existing local progress export/import record.

Portfolio notes do not award XP or mastery and are not represented as verified stakeholder evidence.

### 1.3 Navigation and persistence reconciliation

- Header breadcrumb changes by destination and shows the current Guided Study module.
- Dashboard refreshes when opened, so local evidence state is not presented as static text.
- Guided-study, resource-library, dashboard, Systems Lab, Assessment Studio, and Portfolio routes now connect rather than acting as isolated representative screens.
- The local progress-state schema now contains a normalised `portfolio` object, preserving case name and bounded module-note text on import/export.

## 2. Coherent one-file product inventory

`inft255-learning-environment.html` now contains, without a required backend or runtime stylesheet/script dependency:

| Product area | Integrated evidence |
|---|---|
| Guided instruction | seven Guided Study modules, source labels, visuals, key terms, flashcards, actions |
| Technical practice | 44 keyboard-accessible Systems Lab activities across M1–M7, including calculators, planners, UML/model clinics, repair and final challenge work |
| Assessment | canonical 100 MCQs / 20 subjective prompts; topic, mixed, untimed, timed, and subjective-reveal workflows |
| Feedback | source-linked objective explanations; row-level lab reasons; subjective model guide/marking guide only on reveal |
| Resources | 17 searchable topic/type-filtered offline catalogue records, verified video metadata, standards/academic resources, unverified search suggestions, local practical routes |
| Learner evidence | localStorage progress, dashboard, XP, levels, evidence badges, daily challenge/streak, mastery/recommendations |
| Continuity | versioned local JSON export/import, evidence normalisation/recalculation, locally saved Case Studio notes |
| Accessibility foundations | semantic form controls, visible focus style, skip link, live regions, text alternatives for authored visuals, reduced-motion CSS |

## 3. Actual integration checks performed

1. Parsed the full HTML document with Python `HTMLParser`.
2. Extracted the inline JavaScript and passed it through `node --check`.
3. Re-ran the existing JSDOM assessment/resource smoke test after integration:
   - topic feedback;
   - timed answer-locking/post-submit explanation review;
   - subjective guide hidden/reveal behaviour;
   - searchable library and local practical route.
4. Re-ran JSDOM local-progress and import tests:
   - assessment/lab/daily evidence saved locally;
   - dashboard updates and import controls;
   - imported evidence normalised and tampered XP ignored/recalculated.
5. Added JSDOM integration smoke test:
   - exactly seven Guided Study modules;
   - Module 4 content renders;
   - retrieval flashcard toggles;
   - guided action routes to the correct M4 lab; and
   - Case Studio note persists in localStorage.
6. Ran `git diff --check` with no whitespace errors.

## 4. Deliberate non-claims and gaps to resolve in QA

Integration is not final QA. The following must be inspected and, where necessary, refined before completion is claimed:

- manual browser/device/responsive verification of all screens and long resource/assessment/module navigation;
- keyboard-only and screen-reader-focused accessibility review of dynamic render/update paths;
- full external-link health check in a live browser, including access-dependent scholarly records and unverified search suggestions;
- item-by-item academic moderation/readability review in the rendered app, especially source wording, calculations, and timed/subjective messages;
- global learner-note/bookmark/search experience: the app has Case Studio notes and resource search, but no broader bookmark/global-search facility yet;
- import/export edge cases with real downloaded files and larger learner histories;
- visual-design consistency pass across dense dashboard/assessment/resource/portfolio screens; and
- realistic learner-flow testing from first use through final challenge.

## 5. Approval gate

Approve or request changes to final integration. Approval authorises **Phase 10 dedicated QA**, including functional, academic, responsive, accessibility, external-link, persistence-edge, and visual-design review/refinement. No final completion claim should be made until those tests and any necessary corrections are complete.
