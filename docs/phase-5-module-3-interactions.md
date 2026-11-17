# Phase 5 — Module 3 Interactive Learning Implementation

**Course:** INFT 255 — System Analysis & Design
**Scope:** Module 3 — Project Initiation, Feasibility, Scheduling, and Risk Management
**Status:** Implemented and structurally tested for review.

## Implemented Module 3 Systems Lab activities

`inft255-learning-environment.html` now contains 16 source-backed activities across Modules 1–3. Module 3 adds these four meaningful calculations/decision activities:

| Activity | Learner action | Implemented explanation/guardrail |
|---|---|---|
| **Feasibility triage** | classify evidence as technical, economic, or organisational feasibility | explains why the dimensions complement one another rather than collapse into a single go/no-go label |
| **Economic feasibility calculator** | enter initial cost, annual net cash inflow, and discount rate; calculate three-year present-value total, NPV, and simple payback | shows formula/result assumptions and explicitly says a positive NPV does not establish technical or organisational feasibility |
| **Critical-path challenge** | identify the longest path, slack, and changed duration under the course A–E dependency example | gives visible arithmetic and reinforces that critical path is the longest dependency path |
| **Risk-register prioritiser** | choose responses for connectivity, vendor, UI delay, and current-staffing cases | distinguishes risk from current issue; shows score/response reasoning and avoids treating transfer as elimination |

### Implementation notes

- The calculator uses only learner-entered values and the explicitly stated three-year assumption; it does not invent cash flows, a discount rate, or a recommendation.
- All controls are native keyboard-accessible form controls with reset, per-row response feedback, and `aria-live` result summary.
- This is an educational simulation, not financial advice or a production project-management calculator.

## Actual checks performed

1. Python `HTMLParser` parsed the full standalone document successfully.
2. The extracted JavaScript passed `node --check`.
3. A structural inventory check confirmed exactly 16 lab IDs: the 12 Module 1–2 activities plus `feasibility`, `economics`, `schedule`, and `risk`.
4. The same check confirmed the calculator handler and its NPV/payback explanation are present.
5. `git diff --check` completed without whitespace errors.

No manual multi-browser calculation test, learner study, or accessibility audit is claimed in this phase.

## Still not implemented

There is no persistence for input values/results, full assessment session, question bank ingestion, timed exam, subjective answer reveal UI, course-wide progress, XP/badges/streaks/mastery, dashboard analytics, resource-library expansion, export/import, or final QA. Those features remain in scope for their later approved phases.

## Review gate

Approve or request changes to Module 3 interactions before requirements/data/process modelling content is developed. The final application remains one evolving standalone HTML file; no backend is required for the activity implementations completed so far.
