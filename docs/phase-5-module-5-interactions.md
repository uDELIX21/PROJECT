# Phase 5 — Module 5 Interactive Learning Implementation

**Course:** INFT 255 — System Analysis & Design
**Scope:** Module 5 — Object Orientation and UML Functional / Structural Models
**Status:** Implemented and structurally tested for review.

## Implemented Module 5 UML model labs

`inft255-learning-environment.html` now contains **29** source-backed Systems Lab activities across Modules 1–5. Module 5 implements the nine interactions specified in its approved content package.

| Activity | Learner action | Implemented feedback / accuracy safeguard |
|---|---|---|
| **OO vocabulary sorter** | classify class, object/instance, attribute/state, operation/method, and message | distinguishes an object’s offered operation from a request message |
| **UML question-to-view planner** | select use-case, logical/class, component, deployment, or scenario view for a stakeholder question | reinforces that UML is a language and each view answers a different question |
| **Relationship and multiplicity clinic** | choose dependency, association, composition, generalisation, and stated multiplicity | corrects solid-association/dashed-dependency confusion and requires lifecycle rationale for composition |
| **Use-case boundary builder** | identify external actors, goal-level naming, `«include»`, and `«extend»` | contains an original accessible mini diagram with text alternative; explains direction and required versus conditional behaviour |
| **Use-case description debugger** | identify trigger, precondition, alternate/exception path, postcondition, and NFR traceability note | turns diagram overview into reviewable scenario detail |
| **CRC responsibility role-play** | assign information, relationship facts, service coordination, and diagnose an unowned message | rejects automatic noun-to-class conversion and arbitrary responsibility assignment |
| **Class/object consistency validator** | compare multiplicity, an object snapshot, message ownership, and relationship-specific data | contains an original accessible class/object visual and bridges to the prior ERD |
| **Component-interface matcher** | match required/provided `IRegistration` and `IPayment` interfaces and correct a component/node confusion | contains an original accessible component-interface visual and keeps logical component/deployment claims separate |
| **FR-to-component trace challenge** | trace payment confirmation from FR-05 through use case, responsibility/operation, and component interface | contains an original accessible traceability chain and flags an orphan requirement as a gap to repair |

### Interaction behaviour

- Every activity uses native radio/select controls, so it supports keyboard operation without drag-only interaction.
- **Check reasoning** returns row-level explanation plus an `aria-live` summary; incorrect selection receives the applicable concept/rule, not an unexplained mark.
- **Reset** clears the activity without presenting a page-click score as learning evidence.
- The mini visuals are authored text/HTML explanations, not copied slide/publisher diagrams.

## Actual structural checks performed

1. Python `HTMLParser` parsed the complete standalone HTML document successfully.
2. Extracted inline JavaScript passed `node --check`.
3. A lab inventory test confirmed exactly 29 IDs: 20 earlier Module 1–4 activities plus the nine Module 5 IDs: `oovocab`, `umlviews`, `relationships`, `usecase`, `ucdescription`, `crc`, `classobject`, `component`, and `traceability`.
4. The structural test confirmed all four accessible Module 5 visual renderer functions and the Modules 1–5 / 29-activity Systems Lab labelling.
5. `git diff --check` completed without whitespace errors.

No automated browser run, manual mobile/device test, freeform diagram test, accessibility audit, or learner-effectiveness study is claimed. The activities are validated for structure/syntax only in this phase.

## Still not implemented

The final comprehensive application remains incomplete: no persistent model artefacts, full assessment-session engine, timed/mixed assessments, subjective reveal interface in the app, question-bank scoring, durable progress/mastery/XP/badges/streaks, dashboard analytics, complete resource library, notes/bookmarks/search, export/import, or final academic/accessibility/responsive/visual QA. Only theme preference uses local storage at this stage.

## Review gate

Approve or request changes to Module 5 interactions before Module 6 architecture, deployment, and behavioural-modelling content is developed. The implementation continues to use one standalone, offline-first HTML file without a required backend.
