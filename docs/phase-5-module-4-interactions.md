# Phase 5 — Module 4 Interactive Learning Implementation

**Course:** INFT 255 — System Analysis & Design
**Scope:** Module 4 — Requirements Engineering, DFD, and ERD
**Status:** Implemented and structurally tested for review.

## Implemented Module 4 model labs

The single standalone file `inft255-learning-environment.html` now contains 20 Module 1–4 Systems Lab activities. Module 4 adds four model-focused activities:

| Activity | Learner action | Feedback value |
|---|---|---|
| **Requirement-quality editor** | identify FR/NFR and improve vague or prematurely technical statements | explains measurability and analysis-versus-design distinction |
| **DFD element and error clinic** | label process/flow/store and diagnose black holes/direct-store flows | explains naming and transformation rules rather than only marking wrong |
| **Context-to-Level-0 balancer** | evaluate missing/extra external flows and a valid decomposition | explains parent/child boundary-flow consistency |
| **ERD cardinality and M:N resolver** | identify M:N, associative entity, FK, and 1:N relationship | explains where relationship-specific Semester/Grade facts belong |

All use native keyboard-accessible controls, reset functions, per-row feedback, and an `aria-live` summary. They use course-registration examples from the supplied lecturer material; no fabricated stakeholder data is presented.

## Actual checks performed

1. Parsed the full HTML with Python `HTMLParser`.
2. Passed the extracted inline JavaScript through `node --check`.
3. Confirmed 20 lab activity IDs exist, including `reqquality`, `dfd`, `balance`, and `erd` as the four Module 4 additions.
4. Ran `git diff --check` with no whitespace errors.

No manual browser/device test or automatic diagram-drawing test is claimed. The current activities are rule/decision model labs, not a full freeform DFD/ERD drawing tool.

## Not yet implemented

The app does not yet persist an SRS, draw diagrams freely, generate a traceability matrix, score topic/mixed assessments, run timed exams, reveal subjective marking guides in an assessment session, or supply course-wide learning progress/gamification/export/import. These remain in scope for later reviewed phases.

## Review gate

Approve or request changes to Module 4 interactions before OO/UML foundation content is developed. The final application remains an evolving single HTML file without a mandatory backend.
