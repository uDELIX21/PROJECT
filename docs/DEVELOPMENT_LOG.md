# Development Log — System Analysis & Design Learning Environment

## Project status

- **Current phase:** Phase 10 — Final QA and refinement complete
- **Phase status:** The approved standalone M1–M7 environment has completed core functional, content, persistence, rendered-resource, accessibility-semantic, and responsive-code QA. See `docs/phase-10-final-qa.md` for actual checks, refinements, and the transparent real-browser/external-access limits.
- **Repository branch:** `arena/3ef97488-project`
- **Record date:** 17 November 2026 (UTC)

## Phase 1 decisions

1. The six uploaded PDFs were treated as the primary course materials. Their text was extracted page-by-page and key diagram-heavy pages were rendered and inspected; no application interface or learning feature has been built in this phase.
2. The 41-page comprehensive notes are the only supplied item that sets out a full Week 1–13 sequence, formal assessment map, project portfolio, and final assessment expectations. They will be the proposed primary syllabus backbone unless the lecturer or user provides a superseding outline.
3. The five weekly lecture PDFs are retained as supporting lecturer-provided sources. Their coverage overlaps with the comprehensive notes but provides useful emphasis and visuals, especially for SDLC methodologies and introductory UML.
4. Future learner-facing content will distinguish **lecturer material**, **supplementary academic explanation**, **standards/legal context**, and **applied example**. Supplementary material will not be presented as if it were lecturer-set examinable content.
5. Several lecture-slide simplifications or inconsistencies must be corrected transparently in later content instead of being repeated as facts. Details are recorded in `docs/phase-1-source-content-report.md`.
6. The final one-file/offline delivery constraint is acknowledged but intentionally deferred. No application architecture, visual system, curriculum build, or code has been started before approval of the next phase.

## Phase 1 evidence produced

- `docs/phase-1-source-content-report.md` — source inventory, course-content inventory, assessment evidence, academic research catalogue, verification record, content risks, and Phase 2 gate.

## User-approved scope decisions

On 17 November 2026, the user approved the following:

1. **Course identity:** use `INFT 255` in the product title.
2. **Syllabus authority:** treat the 2026/2027 comprehensive notes as authoritative where they are richer than the five weekly slides.
3. **Scope:** cover the full Week 1–13 course.
4. **Academic policy:** no official course outline, rubric, past paper, or answer key is available. Future assessment feedback must therefore be transparently author-created and source-mapped, not described as lecturer-approved.

## Phase 2 decisions

1. The course is structured as eight connected modules across the approved Week 1–13 progression, with orientation, guided study, Case Studio, Model Lab, and revision/exam-practice modes.
2. Each module culminates in an artefact that is reused later: a system map; lifecycle rationale; feasibility/schedule/risk plan; SRS/DFD/ERD package; use-case/class/component models; architecture/deployment/behavioural models; then an integrated SAD package.
3. The provided course-project cases will be offered as selectable Case Studio contexts. The UENR Online Course Registration & Results System is the default worked case because the primary source supplies the richest supporting examples.
4. Later assessment production will use a quality-first blueprint with traceability, cognitive-level balance, explanations, misconception feedback, and explicitly non-official model guides.
5. Phase 3 will be limited to visual identity, responsive layout rules, navigation, dashboard, and representative screens. No complete app build starts until it is reviewed.

## Phase 2 evidence produced

- `docs/phase-2-curriculum-learning-architecture.md` — detailed full-course blueprint, learning outcomes, prerequisites, lesson architecture, activities, artefacts, assessment plan, resource mapping, traceability rules, and Phase 3 gate.

## Phase 3 decisions

1. The approved visual identity is **Blueprint Studio**: a diagram-centred, restrained, offline-safe interface using blueprint navy, teal action states, warm neutral surfaces, and original inline vector motifs rather than stock imagery or gradients.
2. The information architecture makes the learner’s next action and demonstrated evidence central: Dashboard, Learn, Model Lab, Practice, Exams, Resources, and Portfolio.
3. All visual states must pair colour with text/icon/shape; diagrams require a text description and keyboard-accessible alternative; the final implementation must respect reduced motion and readable mobile layouts.
4. Gamification is designed around demonstrated practice, repairs, and verified artefact steps — not page views. The scoring engine itself is deferred.
5. A standalone visual prototype deliberately implements only representative interactions (theme, navigation, flashcard, DFD repair feedback, and a practice feedback state). It must not be represented as the final learning application.

## Phase 3 evidence produced

- `docs/phase-3-visual-identity-ux.md` — design system, screen specifications, responsive rules, accessibility requirements, resource/gamification visual strategy, and Phase 4 gate.
- `inft255-learning-environment.html` — the evolving standalone offline HTML application shell, carrying the approved dashboard, lesson studio, lab, practice, resource, and portfolio visual direction forward into later phases.

## Phase 4 decisions

1. Module 1 is the first content package because it supplies the systems-thinking, boundary, constraint, analysis/design, and role concepts required in every later module.
2. Its explanations preserve lecturer terminology while making scope, value, classification, and systems-boundary reasoning explicit. An accuracy note prevents the supplied “machines are non-adaptive” example being taught as universal fact.
3. Module 1 assessment drafting begins with 16 non-repetitive MCQs and four subjective prompts. They have source locators, reasoning feedback/model guides, and cognitive-level labels, but are not official answers or app features.
4. The user explicitly selected **Keep the phased protocol** when asked whether to waive checkpoints for immediate Phase 6/8/9 delivery. Future question-bank, gamification, export/import, and final-app targets remain in scope and will be developed after review, not skipped to.

## Phase 4 evidence produced

- `docs/phase-4-module-1-content.md` — five source-labelled lessons, worked examples, misconceptions, Case Studio activity, future interaction specifications, 16 MCQ drafts, four subjective prompts/model guides, limitations, and Phase 5 gate.

## Phase 5 decisions

1. The Phase 3 prototype has been evolved into the single standalone application shell `inft255-learning-environment.html`; subsequent approved work will extend this file rather than create a competing app.
2. Six Module 1 systems-thinking activities are now functional through accessible radio/select controls and reasoned feedback: boundary, IPO/control/feedback, analysis/design, constraint impact, classifications, and project roles.
3. The interactive controls are deliberately keyboard-first rather than requiring drag-and-drop. This gives all learners an equivalent path and makes each categorisation rationale inspectable.
4. No XP, badges, streaks, mastery, portfolio state, final assessment score, or learner progress is claimed or awarded yet. Only the visual-theme preference is locally persisted.

## Phase 5 evidence produced

- `inft255-learning-environment.html` — standalone offline shell with the approved design system and six implemented Module 1 Systems Lab activities.
- `docs/phase-5-module-1-interactions.md` — interaction-to-syllabus mapping, actual test record, limitations, and review gate.

## Phase 4 — Module 2 decisions

1. Module 2 teaches methodology as a contextual, criteria-based choice rather than a list of fashionable labels.
2. The content preserves the course’s four-phase SDLC while distinguishing it from specific methods and the iterative Unified Process.
3. Accuracy notes prevent a literal “no feedback in waterfall” or “RAD means rapid coding” interpretation.
4. The reviewed Module 2 seed adds 18 MCQs and four subjective prompts. Across Modules 1–2 there are now 34 MCQ drafts and eight subjective drafts, but this is not yet a functional or course-complete question bank.

## Phase 4 — Module 2 evidence produced

- `docs/phase-4-module-2-content.md` — six source-labelled lessons, methodology Case Studio scaffold, seven future interaction specifications, 18 MCQ drafts, four subjective prompts/model guides, limitations, and Module 2 interaction gate.

## Phase 5 — Module 2 decisions

1. The standalone Systems Lab now contains the previously approved Module 1 activities plus six source-supported Module 2 simulations.
2. Method selection is implemented as a trade-off activity; the feedback explains the fit from stated conditions and deliberately avoids an unsupported universal “best method” claim.
3. Native keyboard-accessible controls and explanatory feedback remain the equivalent interaction path; no drag-only simulation is required.

## Phase 5 — Module 2 evidence produced

- `inft255-learning-environment.html` — expanded standalone application shell with 12 functional Module 1–2 Systems Lab activities.
- `docs/phase-5-module-2-interactions.md` — simulation mapping, actual structural checks, scope limits, and review gate.

## Phase 4 — Module 3 decisions

1. Module 3 connects the earlier business problem/constraints/method choice to quantitative feasibility, schedule dependency, scope, staffing, and continuous risk practice.
2. Economic and scheduling explanations require visible formula/work/assumption reasoning. The future application must not generate an NPV, critical path, or risk score without showing inputs and interpretation.
3. Risk content uses the transparent four-step cycle and treats probability × impact as a priority aid, not a precise forecast.
4. Module 3 adds 18 MCQ and four subjective drafts. Across Modules 1–3, the reviewed source-mapped seed is 52 MCQs and 12 subjective prompts; it is neither course-complete nor yet functional.

## Phase 4 — Module 3 evidence produced

- `docs/phase-4-module-3-content.md` — five source-labelled lessons, calculations/network/risk examples, planning Case Studio scaffold, seven future interactions, 18 MCQs, four subjective prompts/model guides, and Module 3 simulation gate.

## Phase 5 — Module 3 decisions

1. Module 3 adds the first numeric simulation: a transparent three-year NPV/payback calculator that uses only visible learner inputs and stated assumptions.
2. Scheduling and risk activities are explanatory decisions, not decorative diagrams: each shows the dependency, arithmetic, risk/issue distinction, or response rationale.
3. The Systems Lab now contains 16 Module 1–3 activities within the same offline standalone file.

## Phase 5 — Module 3 evidence produced

- `inft255-learning-environment.html` — expanded standalone application shell with 16 functional Module 1–3 lab activities, including economic, scheduling, and risk interactions.
- `docs/phase-5-module-3-interactions.md` — interaction mapping, test record, limits, and review gate.

## Phase 4 — Module 4 decisions

1. Module 4 builds the precise requirements/data/process foundation that later use-case, class, sequence, and deployment models must trace back to.
2. DFD and ERD are taught as complementary models: data movement/transformation versus stored data/relationships. They must not be confused with flowcharts or class diagrams.
3. Requirement quality is tied to measurability, source/assumption labelling, IDs, and traceability; no simulated stakeholder result may be represented as real evidence.
4. Module 4 adds 18 MCQ and four subjective drafts. The reviewed seed across Modules 1–4 is now 70 MCQs and 16 subjective prompts, still short of the final required bank and not functional yet.

## Phase 4 — Module 4 evidence produced

- `docs/phase-4-module-4-content.md` — six source-labelled lessons, requirements package scaffold, eight future model labs, 18 MCQs, four subjective prompts/model guides, limitations, and interaction gate.

## Phase 5 — Module 4 decisions

1. Module 4 adds four keyboard-accessible requirements/data/process model labs to the existing standalone Systems Lab.
2. The activities teach model rules and cross-model consistency with explanation feedback; they do not pretend to be an unrestricted professional diagramming tool.
3. The Systems Lab now contains 20 functional Module 1–4 activities in one offline HTML file.

## Phase 5 — Module 4 evidence produced

- `inft255-learning-environment.html` — expanded standalone application shell with 20 Module 1–4 lab activities.
- `docs/phase-5-module-4-interactions.md` — model-lab mapping, structural test record, limitations, and review gate.

## Phase 4 — Module 5 decisions

1. Module 5 carries the Module 4 SRS/DFD/ERD vocabulary forward into goal-based use cases, responsibilities, class structure, interfaces, and explicit traceability.
2. UML is framed as a modelling language rather than an SDLC. The package corrects the supplied slide’s association/dashed-line ambiguity and avoids an unqualified permanent UML diagram-count claim.
3. Use-case `«include»`/`«extend»`, ownership relationships, multiplicity, and requirement-to-operation traceability are treated as explanation-heavy misconception areas, not notation memorisation.
4. Module 5 adds 18 MCQ and four subjective drafts. Across Modules 1–5, the source-mapped seed is 88 MCQs and 20 subjective prompts. The subjective draft-count target has been reached; the MCQ target remains 12 questions short and neither bank is functional yet.

## Phase 4 — Module 5 evidence produced

- `docs/phase-4-module-5-content.md` — eight source-labelled lessons, accessible original diagrams, Case Studio package, nine planned model labs, 18 MCQs, four subjective prompts/model guides, source limitations, and a Phase 5 gate.

## Phase 5 — Module 5 decisions

1. Module 5 implements all nine approved model-lab specifications as accessible rule/decision, traceability, and visual-explanation activities.
2. The lab uses original text/HTML UML mini visuals with text alternatives for use-case, class/object, component-interface, and requirement traceability reasoning; it does not reproduce lecture/publisher diagrams.
3. The Systems Lab now contains 29 functional Module 1–5 activities within one offline standalone HTML file. Results remain session-only and do not yet constitute progress evidence.

## Phase 5 — Module 5 evidence produced

- `inft255-learning-environment.html` — expanded standalone application shell with 29 functional Module 1–5 lab activities, including nine OO/UML functional/structural model labs.
- `docs/phase-5-module-5-interactions.md` — complete interaction mapping, structural test record, scope limitations, and review gate.

## Phase 4 — Module 6 decisions

1. Module 6 makes the transition from logical OO/UML structure to design/deployment/runtime behaviour explicit: a valid system package needs linked, not isolated, models.
2. Deployment content distinguishes components, artifacts, and nodes; layered design distinguishes presentation, domain/application, data management, and physical concerns.
3. Sequence/communication, activity, and state-machine diagrams are taught by the question they answer, with cross-model checks used to surface missing operations, interfaces, data, paths, constraints, and contradictory ordering.
4. Module 6 adds 18 MCQ and four subjective drafts. The source-mapped draft seed is now 106 MCQs and 24 subjective prompts across Modules 1–6. It exceeds numerical targets but requires course-wide correctness/duplication/session review before becoming a final assessment bank.

## Phase 4 — Module 6 evidence produced

- `docs/phase-4-module-6-content.md` — six source-labelled lessons, original accessible visual explanations, design/behaviour Case Studio package, nine planned model labs, 18 MCQs, four subjective prompts/model guides, limitations, and a Phase 5 gate.

## Phase 5 — Module 6 decisions

1. Module 6 implements all nine approved architecture/behaviour model labs using keyboard-accessible decision activities, per-row explanations, and original text/HTML visuals with text alternatives.
2. The activities deliberately separate logical architecture/component reasoning from physical deployment, workflow from object lifecycle, and structural correctness from cross-model traceability.
3. The Systems Lab now contains 38 functional Module 1–6 activities in the evolving offline standalone HTML file. They remain session-only evidence and do not yet award progress or XP.

## Phase 5 — Module 6 evidence produced

- `inft255-learning-environment.html` — expanded standalone shell with 38 Module 1–6 lab activities, including nine architecture, deployment, behavioural-model, and validation labs.
- `docs/phase-5-module-6-interactions.md` — interaction mapping, structural test record, limitations, and review gate.

## Phase 4 — Module 7 decisions

1. Module 7 is the integration/capstone module: it revises near-neighbour concepts through the question each model answers, then uses a repair order and explicit cross-model validation instead of diagram memorisation.
2. Timed, untimed, topic-specific, mixed, subjective-reveal, and final-challenge requirements are specified for implementation, with an explicit non-official assessment/answer-key policy.
3. The final registration-and-payment challenge is labelled simulated and requires visible assumptions; it cannot be treated as evidence of real university policy or infrastructure.
4. Module 7 adds 18 MCQ and four subjective drafts. The reviewed source-mapped seed now contains 124 MCQs and 28 subjective prompts. It exceeds numerical targets but needs Phase 6 item-level review before it becomes a functional assessment bank.

## Phase 4 — Module 7 evidence produced

- `docs/phase-4-module-7-content.md` — five source-labelled revision/capstone lessons, final challenge, ten planned interactions, 18 MCQs, four subjective prompts/model guides, assessment integrity rules, limitations, and Phase 5 gate.

## Phase 5 — Module 7 decisions

1. Module 7 implements six core revision/capstone interactions: concept discrimination, foundation repair, UML clinic, case-reading plan, dynamic 60-minute timebox planning, and final package challenge.
2. The timebox plan is a real learner-input calculation with review-time guidance, but is explicitly author-created practice support—not an official INFT 255 time rule.
3. Topic/mixed/timed assessment delivery and subjective response studio are deliberately deferred to Phase 6 because they depend on reviewed course-wide item/attempt/score/reveal logic.
4. The Systems Lab now contains 44 functional Module 1–7 activities in one standalone HTML file. They are session-only and do not yet award XP or durable completion credit.

## Phase 5 — Module 7 evidence produced

- `inft255-learning-environment.html` — expanded standalone shell with 44 Module 1–7 lab activities, including six core revision/capstone interactions and functional timebox feedback.
- `docs/phase-5-module-7-interactions.md` — activity mapping, structural test record, Phase 6 deferral rationale, and review gate.

## Phase 6 — assessment bank review decisions

1. The 124 MCQ / 28 subjective draft seed was reduced by explicit canonical selection rather than padded or silently deduplicated: 100 MCQs and 20 subjective items will seed the first scored workflow; 24 MCQs and eight subjective prompts remain traceable reserve/revision candidates.
2. The selected MCQ bank includes 16 remembering, 24 understanding, 28 applying, 21 analysing, and 11 evaluating items. It spans every approved Module 1–7 outcome cluster.
3. All selected answers/model guides remain author-created and non-official because no lecturer key/rubric/past paper exists. Subjective guides must be hidden by default.
4. Assessment delivery must be local/offline for core content/feedback and separate immutable item data from learner attempt/progress data.

## Phase 6 — evidence produced

- `docs/phase-6-assessment-bank-review.md` — review method, canonical 100/20 selection, cognitive/topic coverage, reserve inventory, app-data requirements, workflow requirements, source limitations, and approval gate.

## Phase 6 — assessment workflow decisions

1. The canonical 100 MCQs and 20 subjective prompts are now normalised as immutable inline data in the one-file app. Core prompts, feedback, and guides run offline.
2. Objective delivery has topic-specific untimed, mixed untimed, and timed mixed modes. Timed mode locks answers and delays all explanations until submission/expiry.
3. Subjective prompts provide a draft field and cue; model answer/marking guide data is withheld from the DOM until explicit learner reveal. No automatic free-text marking claim is made.
4. All assessment attempts/results remain session-only. No assessment click, reveal, or page view currently produces XP/mastery/completion evidence or durable storage.

## Phase 6 — implementation evidence produced

- `inft255-learning-environment.html` — expanded standalone shell with an offline Assessment Studio, canonical 100/20 data, topic/mixed/timed workflows, source-labelled MCQ feedback, and subjective reveal flow.
- `docs/phase-6-assessment-workflows.md` — workflow mapping, actual data/smoke-test record, safeguards, limitations, and review gate.

## Phase 7 — resource library decisions

1. The app now holds a searchable/filterable offline catalogue of 17 records: 12 verified external resources, two explicitly unverified course-bibliography search suggestions, and three local practical demonstrations.
2. Verified YouTube cards expose title, channel, direct URL, verified duration, topic, watch-for guidance, recommendation rationale, and verification/access limitation.
3. Resource cards preserve useful metadata offline if an external destination is unavailable. Search suggestions are clearly marked unverified and must not be treated as citations.

## Phase 7 — resource library evidence produced

- `inft255-learning-environment.html` — Resources screen replaced with a filterable topic/type/search library and local Systems Lab routes.
- `docs/phase-7-resource-library.md` — full catalog, verification/access disclosure, implementation checks, limitations, and review gate.

## Phase 7 — learner systems decisions

1. Learning evidence is now stored locally only after demonstrated objective correctness, improved scored model-lab outcomes, or a correctly completed daily challenge. Views, clicks, resets, subjective guide reveals, and repeated already-correct items do not independently earn XP/mastery.
2. The dynamic dashboard reports topic evidence, mastery/remaining work, performance, strengths/weaknesses, recommendations, level, badges, streak, daily challenge, and local backup/restore controls.
3. Import/export uses a versioned local JSON record. Imports normalise recognised IDs and recompute XP/badges rather than trusting an imported XP total.
4. Thresholds, XP, badge labels, and daily schedule are author-created learning design—not official course grading policy. Browser-local state is not secure institutional assessment data.

## Phase 7 — learner systems evidence produced

- `inft255-learning-environment.html` — expanded standalone shell with localStorage evidence/progress, dashboard, daily challenge/streak, mastery/recommendation system, evidence-based XP/levels/badges, and JSON export/import.
- `docs/phase-7-progress-dashboard-gamification.md` — evidence rules, dashboard/badge criteria, export/import behaviour, actual test record, limitations, and review gate.

## Phase 9 — integration decisions

1. Guided Study is no longer a Module 1-only representative screen: source-labelled M1–M7 instruction, original accessible visuals, key terms, retrieval flashcards, and routes to aligned Labs/assessments are integrated in the standalone app.
2. Case Studio now includes local/exportable per-module notes and an explicit assumption/source-integrity boundary; notes do not award progress or make a simulated fact real.
3. Navigation, breadcrumb, dashboard refresh, portfolio persistence, resource routes, labs, assessment workflows, and evidence systems are reconciled as one course experience.
4. Global bookmark/global-search and manual browser/device/assistive-technology/link/persistence-edge/visual review remain known QA items. Integration has been structurally and JSDOM smoke tested, not declared final complete.

## Phase 9 — evidence produced

- `inft255-learning-environment.html` — integrated one-file offline course experience with M1–M7 Guided Study and local Case Studio portfolio alongside previously approved systems.
- `docs/phase-9-integration-review.md` — integration inventory, actual smoke-test record, known gaps, limitations, and Phase 10 approval gate.

## Phase 10 — final QA and refinement decisions

1. The final pass retained the approved integrated implementation and refined it rather than replacing content or mechanics. It corrected an obsolete assessment-persistence message, standards-aware verification/validation wording in M2-Q12, narrow-card wrapping, dynamic mobile-menu focus/Escape behaviour, theme toggle semantics, visible form focus, and compact touch targets.
2. Content and data review reconfirmed the canonical 100 MCQs/20 subjective prompts, valid answer/model/guide/source data, reviewed cognitive balance, source labels, and the non-official-answer boundary. No fabricated lecturer approval, real stakeholder evidence, or institutional-grade claim was added.
3. Functional QA now includes all 44 lab render/interaction paths, navigation/focus/mobile menu, search/bookmarks, assessment flags, resource filters/rendered link safety, portfolio and backup/restore happy/error paths, local-evidence recalculation, and all earlier regression checks.
4. Accessibility-semantic QA has a clean axe-core JSDOM result with colour contrast intentionally excluded because JSDOM cannot render it accurately. Responsive QA inspected all defined breakpoint behaviour and added narrow-layout refinements; it is not falsely recorded as a real-device or screen-reader certification.
5. The core offline product is complete for the approved scope. Real deployment should still validate external resource availability/access and conduct a browser/device/assistive-technology pass in the target learner environment. These are stated operational validation limits, not claims that learner-facing core functionality is absent.

## Phase 10 — evidence produced

- `inft255-learning-environment.html` — final refined standalone learning environment, including accessibility/focus/touch-target, responsive-card, content-wording, and assessment-message corrections.
- `docs/phase-10-final-qa.md` — exact QA scope, actual results, refined areas, external-link disclosure, and completion boundary.

## Current completion state

- **Approved scope implementation:** Complete in the standalone HTML file.
- **Core automated/structural QA:** Passed; exact checks are recorded in `docs/phase-10-final-qa.md`.
- **Deployment validation still advisable:** Real-browser/device/assistive-technology inspection and contemporaneous optional external-link access validation in the eventual learner network.
