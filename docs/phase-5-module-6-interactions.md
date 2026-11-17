# Phase 5 — Module 6 Interactive Learning Implementation

**Course:** INFT 255 — System Analysis & Design
**Scope:** Module 6 — Architecture, Deployment, Behavioural Models, and Cross-Model Validation
**Status:** Implemented and structurally tested for review.

## Implemented Module 6 architecture and behavioural model labs

`inft255-learning-environment.html` now has **38** source-backed Systems Lab activities across Modules 1–6. Module 6 implements all nine model-lab specifications approved in its content package.

| Activity | Learner action | Implemented feedback / safeguard |
|---|---|---|
| **Layering and coupling clinic** | place presentation, domain/application, data-management, and physical concerns; repair direct UI-to-database coupling | explains logical layer boundaries and avoids conflating a layer with a server |
| **Deployment mapper** | distinguish node, artifact, logical component/interface, communication path, and missing assumptions | uses an original accessible mini deployment visual; the example is explicitly simulated |
| **Sequence scenario builder** | order UI/service/prerequisite/payment/enrolment collaboration and locate receiver responsibilities | preserves FR-05 ordering and identifies unowned message gaps |
| **Interaction-fragment selector** | choose `alt`, `opt`, `loop`, `par`, and `ref` from semantics | teaches interaction meaning rather than symbol recognition |
| **Sequence-to-communication converter** | preserve normal-path order/guard through numbered messages | uses an original accessible conversion visual and explains that links do not remove ordering |
| **Activity workflow clinic** | repair responsibility swimlanes, guards, alternatives, and genuine fork/join concurrency | distinguishes workflow from an object lifecycle |
| **State-machine decision lab** | model the Enrollment object’s Pending/Confirmed/Rejected/Cancelled lifecycle | uses an original accessible state visual; clarifies event, guard, action, and state transition |
| **Cross-model consistency inspector** | trace FR-05 through use case, message/operation, interface, and deployment path | flags orphan links and ordering contradictions for reasoned repair |
| **Payment-path design challenge** | select a constraint-aware next step for failure, recovery, interface, deployment, and naming cases | requires coherent evidence across models rather than decorative modelling |

### Interaction design

- All activities use native select controls and keyboard-accessible buttons; there is no drag-only route.
- **Check reasoning** supplies an explanation for every row and reports an `aria-live` completion summary.
- **Reset** allows an immediate retry; the activities do not award progress/XPs merely for opening/clicking.
- Module 6 adds eight original HTML/text visuals with text alternatives. None reuse course-slide/publisher graphics.

## Actual checks performed

1. Parsed complete HTML with Python `HTMLParser`.
2. Checked extracted inline JavaScript with `node --check`.
3. Confirmed the 38-lab inventory: the 29 existing Module 1–5 labs plus `layers`, `deployment`, `sequence`, `fragments`, `communication`, `activity`, `state`, `crossmodel`, and `designchallenge`.
4. Confirmed the eight new Module 6 visual-renderer functions and the updated Modules 1–6 / 38-activity visible labels.
5. Ran `git diff --check` with no whitespace errors.

The implementation has structural/syntax validation only. No automated browser run, manual device/responsive accessibility audit, freeform-diagram validation, or learner-effectiveness study is claimed.

## Still not implemented

The final application is not complete. It has no durable model/portfolio artifacts; course-wide question-bank session engine; topic/mixed/timed exams; subjective answer/model-guide reveal UI within app assessments; scoring/persistence; XP/levels/badges/streaks/mastery; dashboard analytics; search/bookmarks/notes; full resource library; import/export; or final academic, link, accessibility, responsive, and visual QA. Theme preference remains the only local-storage feature.

## Review gate

Approve or request changes to Module 6 interactions before Module 7 revision, examination-practice, and capstone-integration content is developed. The work continues in the one standalone offline-first HTML application without a mandatory backend.
