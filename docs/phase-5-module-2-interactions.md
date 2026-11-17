# Phase 5 — Module 2 Interactive Learning Implementation

**Course:** INFT 255 — System Analysis & Design
**Scope:** Module 2 only — SDLC, Methodology Selection, and Unified Process
**Status:** Implemented and structurally tested for review. Durable progress, assessment modes, and course-wide functionality remain future scope.

## Implemented Module 2 simulations

The existing standalone file `inft255-learning-environment.html` now carries 12 Systems Lab activities: six approved Module 1 activities and the six Module 2 simulations below. Each Module 2 activity uses actual source-supported course conditions and requires a classification/decision before giving explanation feedback.

| Lab activity | Learner action | Meaningful feedback focus |
|---|---|---|
| **SDLC deliverable route** | map feasibility/plan, interviews/proposal, build-buy/interface, and training/support to the phase with primary responsibility | phase questions, deliverables, and gradual refinement |
| **Method-selection simulation** | select a defensible starting method for stable, changing/short-deadline, high-risk, and safety-critical conditions | criteria-based fit; no method is presented as universally best |
| **Prototype lifecycle decision** | distinguish throwaway from evolutionary prototype and identify expectation management | requirement learning versus production-quality/evolution intent |
| **Spiral risk-loop planner** | connect usability/integration uncertainty to prototype/benchmark action, then plan the loop | risk-driven resolution, not feature-first activity |
| **V-Model traceability matcher** | pair requirements/design levels with acceptance/system/integration/unit testing | verification/validation planning and test traceability |
| **Unified Process workflow view** | identify UP phases and explain overlapping workflow intensity | iterative/incremental, use-case-driven, architecture-centred delivery |

### Delivery and accessibility

- The activities are selectable from the Systems Lab sidebar and use native radio/select form controls, keyboard operation, reset buttons, per-row feedback, and an `aria-live` feedback summary.
- The lab remains fully embedded in the standalone HTML file. It has no external runtime dependency.
- “Simulation” is used carefully: the methodology activity demonstrates evidence-based method selection under fixed conditions; it does not claim to predict a real project outcome or automatically select an objectively correct methodology for every project.

## Actual checks performed

1. The full HTML was parsed successfully using Python `HTMLParser`.
2. The extracted JavaScript passed `node --check`.
3. The Systems Lab data inventory was checked and confirmed exactly these 12 activity IDs: `boundary`, `ipo`, `analysis`, `constraints`, `classify`, `roles`, `sdlc`, `methodfit`, `prototype`, `spiral`, `vmodel`, `up`.
4. `git diff --check` completed with no whitespace errors.

These checks do not claim manual browser/device testing or learning-effectiveness validation.

## Not implemented / not claimed

Module 2 content completion state, progress persistence, simulation score history, assessment-bank ingestion, timed assessment, subjective answer reveal, XP, levels, badges, streaks, mastery, revision milestone, daily-challenge scoring, export/import, and the final resource library remain unimplemented. The external resource links are optional only and need connectivity.

## Review gate

Approve or request changes to the Module 2 simulations before Module 3 content is created. The phased protocol remains active: the complete assessment bank, gamification, dashboard evidence, local progress, export/import, and final course integration will be produced only in their corresponding later reviewed phases.
