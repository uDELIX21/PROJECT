# Phase 6 — Assessment Workflow Implementation

**Course:** INFT 255 — System Analysis & Design
**Scope:** Canonical objective/subjective assessment delivery in the offline standalone application
**Status:** Implemented and tested for review.

## Implemented canonical assessment data

`inft255-learning-environment.html` now embeds immutable, local canonical assessment data normalised from the approved Phase 6 selection:

- **100 unique MCQs** across Modules 1–7.
- **20 unique subjective prompts** with author-created model answers and marking guides.
- Every MCQ includes module/topic, cognitive label, four choices, correct key, explanation, and source locator.
- Every subjective prompt includes topic, title, prompt, model answer, marking guide, and non-official source note.

The included MCQ distribution is: 16 remembering, 24 understanding, 28 applying, 21 analysing, and 11 evaluating. The data is embedded in the single HTML file, so core prompts and feedback do not need a network connection.

## Implemented Assessment Studio workflows

| Workflow | Learner path | Feedback / integrity behaviour |
|---|---|---|
| **Topic practice — untimed** | choose an M1–M7 topic and 5 or 10 questions | immediate submitted-answer explanation, correct response, source pointer, and module/topic review pointer |
| **Mixed practice — untimed** | choose 5 or 10 questions sampled from the canonical bank | immediate source-mapped explanation after each submitted response |
| **Timed exam simulation — mixed** | choose 5 or 10 questions and a 1–120 minute authored duration | visible countdown, answer locking, submit/end action, automatic submission at zero, and full answer/explanation review only after session end |
| **Subjective practice studio** | choose topic/question, draft a response, request a non-scored draft cue | author-created model answer and marking guide are not inserted into the page until the learner explicitly selects reveal |

### Timed-mode safeguards

- The timer begins only after the timed session’s end time has been established.
- Timed answers are locked one at a time, with no correct/incorrect feedback before the session is submitted or time expires.
- Session summary shows submitted, correct, and unanswered counts plus a reviewable explanation list.
- Timed results are labelled author-created/non-official. They do not claim an INFT 255 grade.

### Evidence safeguards

- The objective data and subjective guides are local; optional external resources are not needed for assessment operation.
- Explanation/reveal/page-open events do not award XP, mastery, completion, or badge credit.
- Assessment outcomes remain **session-only** in this phase. The application does not yet save scores, drafts, timer recovery state, or guide-reveal state to `localStorage`.
- Subjective guides remain hidden by default and reveal only on learner action. A short draft cue does not pretend to mark free text automatically.

## Actual checks performed

1. Parsed the complete HTML with Python `HTMLParser`.
2. Passed all extracted inline JavaScript through `node --check`.
3. Parsed the embedded canonical data and confirmed:
   - 100 unique MCQ IDs and 20 unique subjective IDs;
   - four choices and valid answer key for every MCQ;
   - explanation/source values for every MCQ;
   - prompt/model-guide values for every subjective item;
   - expected module and cognitive distribution.
4. Ran a JSDOM functional smoke test that verified:
   - a topic-practice session renders a question and shows explanation feedback after check;
   - a subjective guide is hidden initially and becomes visible only after explicit reveal;
   - timed mode enables duration, renders a timer, locks an answer without pre-submit feedback, and renders a post-submission summary/review.
5. Ran `git diff --check` with no whitespace errors.

No production browser/device/manual accessibility audit, learner study, psychometric validation, official moderation, or persistence/import/export test is claimed yet.

## Still not implemented

- Durable assessment attempts, score history, subjective drafts, timer recovery, mastery and remediation recommendations.
- XP/levels/badges/streaks/revision milestones/final challenge evidence.
- Dashboard analytics, learner notes/bookmarks/search, import/export.
- Complete topic-organised resource library and link-health UI.
- Final course-wide navigation, responsive/accessibility, academic accuracy, external-link, and visual-design QA.

## Review gate

Approve or request changes to the Phase 6 assessment workflows before Phase 7 begins: resource library expansion, dashboard/progress persistence, import/export, and evidence-based gamification design/implementation. The final course delivery remains an evolving single offline-first HTML file without a required backend.
