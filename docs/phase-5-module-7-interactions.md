# Phase 5 — Module 7 Interactive Learning Implementation

**Course:** INFT 255 — System Analysis & Design
**Scope:** Module 7 — Revision, Examination Practice, Final Challenge, and Capstone Integration
**Status:** Core revision/capstone interactions implemented and structurally tested for review.

## Approved Module 7 interactions implemented now

The standalone `inft255-learning-environment.html` now contains **44** Systems Lab activities across Modules 1–7. This phase implements the six Module 7 learning/model-clinic interactions that do not depend on the later course-wide assessment engine.

| Activity | Learner action | Implemented feedback / safeguard |
|---|---|---|
| **Concept bridge sorter** | discriminate DFD/flowchart, ERD/class, include/extend, sequence/communication, and activity/state questions | explains the model purpose and rejected near-neighbour concept |
| **Foundational repair triage** | repair vague requirements, DFD labels/balancing, ERD relationship data, and invented facts | works in analysis-to-design order and distinguishes assumption from evidence |
| **UML model-clinic inspector** | trace FR-05 through use-case, operation, component contract, deployment, and activity order | surfaces an orphan/mismatch with a concrete repair instead of accepting a single attractive diagram |
| **Case-reading planner** | extract supplied facts, constraints, unknowns, model order, and time implications from the simulated brief | labels unknowns as assumptions and avoids inventing policies/facts |
| **60-minute case timebox planner** | allocate reading/assumptions, linked models, rationale, and validation time | dynamically totals learner values; identifies over/under plan and insufficient review allowance without claiming an official exam rule |
| **Integrated SAD package challenge** | make scope, traceability, M:N, external-integration, risk, and naming decisions for the simulated case | reinforces that evidence/repair—not opening diagrams—will support future progress credit |

All activities use native select/number controls, keyboard-accessible actions, reset controls, row-level explanatory feedback, and an `aria-live` result region. Five original text/HTML mini visuals include text alternatives. They do not reproduce course slides or publisher graphics.

## Deliberately deferred to Phase 6

The four assessment-delivery interactions defined in Module 7—topic checkpoint, mixed revision set, timed exam simulation, and subjective response studio—require the course-wide reviewed item bank, attempt/score data model, timer/submission behaviour, and hidden model-answer reveal flow. They have **not** been represented as implemented in this Phase 5 work.

## Actual structural checks performed

1. Parsed the full standalone document with Python `HTMLParser`.
2. Passed the extracted inline JavaScript through `node --check`.
3. Confirmed exactly 44 lab activity IDs: 38 earlier Module 1–6 labs plus `conceptbridge`, `repairtriage`, `modelclinic`, `caseplan`, `timebox`, and `finalchallenge`.
4. Confirmed the Module 7 renderer functions, `checkTimebox` function, special timebox handler route, and Modules 1–7 / 44-activity lab labels.
5. Ran `git diff --check` with no whitespace errors.

No automated browser session, manual mobile/device test, accessibility audit, timing experiment, or learner-effectiveness study is claimed.

## Still not implemented

No functional course-wide assessment session, complete question-bank ingestion/review, timer, subjective answer entry/reveal, durable score history, XP/levels/badges/streaks/mastery, dashboard analytics, resource-library expansion, notes/bookmarks/search, local learning-state persistence, export/import, or final QA has been implemented. Only the theme preference is stored in local storage at this stage.

## Review gate

Approve or request changes to Module 7 core interactions before Phase 6 begins: course-wide question-bank review plus topic/mixed/timed assessment and subjective-answer workflow implementation. The application remains one offline-first standalone HTML file without a mandatory backend.
