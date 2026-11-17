# Phase 7 — Durable Progress, Dashboard, Import/Export, and Evidence-Based Gamification

**Course:** INFT 255 — System Analysis & Design
**Scope:** Browser-local learner evidence and course-progress experience in the standalone offline HTML application
**Status:** Implemented and smoke tested for review.

## 1. Local learning-record design

The application now maintains a browser-local record at:

```text
localStorage key: inft255-learning-state-v1
```

The state contains only learning evidence required for the app experience:

- question evidence by canonical MCQ ID: attempts, distinct-correct status, last attempt;
- scored Systems Lab evidence: best score, completion state, and last attempt;
- daily-challenge records by date;
- recent objective-session summary history; and
- derived badges and XP.

The immutable 100-MCQ / 20-subjective canonical content stays separate from learner evidence. Core learning/feedback remains offline. This is a personal learning record only, not an official INFT 255 grade, attendance record, or institutional profile.

### Import integrity behaviour

Import accepts only the app’s versioned `INFT255-learning-progress` JSON format. It normalises recognised canonical question/lab IDs and recomputes XP/badges from imported evidence rather than trusting an imported XP number. This reduces accidental/casual tampering effects, although an offline local record cannot be treated as secure institutional assessment data.

## 2. Evidence rules: no click-through credit

| Evidence | Durable record | XP rule | What does **not** earn credit |
|---|---|---|---|
| Correct canonical MCQ | first correct response for that question ID | 8 XP per distinct correct MCQ | opening Practice, choosing a wrong answer, repeating a question already correct, opening feedback |
| Scored Systems Lab improvement | best score for a completed select/radio model lab | 2 XP per newly improved correct row, plus 6 XP on first full completion | opening/resetting a lab, repeating the same/lower score, calculator/timebox use without a correctable score |
| Daily challenge | correct canonical challenge for the date | 12 XP for completing the day | viewing dashboard, selecting an option, page load, guide reveal |
| Badge | derived from named evidence criteria | 20 XP per evidence-derived badge | manual dashboard click or decorative page visit |

Model-guide reveal and subjective drafting are deliberately **not** completion/mastery evidence. The app does not claim automatic marking of free text.

## 3. Dashboard features

The Dashboard is now live and computed from local evidence. It presents:

1. **XP and level:** one level per 100 XP, with a role label from Evidence Explorer through Capstone Integrator.
2. **Completed and remaining topics:** every M1–M7 topic shows distinct-correct MCQ evidence, percentage, completed scored lab count, and evidence status.
3. **Topic mastery:** a topic is marked *Mastered evidence* only at 80% distinct-correct canonical MCQs plus the required number of fully completed scored labs (two for M1–M6; one for M7).
4. **Assessment performance:** distinct correct answers, total submissions, recorded-session accuracy, daily streak, and badges unlocked.
5. **Strengths and weaknesses:** ranked from submitted evidence; no strength is fabricated before evidence exists.
6. **Recommended next activity:** routes to the first unattempted or lowest-evidence topic’s practice set, and links the final challenge lab.
7. **Daily challenge:** deterministic date-based canonical question, answer checking, streak evidence, and explanation on an incorrect response.
8. **Backup / restore:** explicit export and an import-replacement acknowledgement before a JSON backup file is chosen.

## 4. Badges, milestones, streak, and final challenge

| Badge / milestone | Evidence-based unlock condition |
|---|---|
| **Evidence starter** | five distinct correct MCQs |
| **Foundation mapper** | at least 60% distinct-correct evidence in M1 and M2 plus one completed scored lab in each |
| **Planning analyst** | at least 60% distinct-correct evidence in M3 and M4 plus one completed scored lab in each |
| **UML modeller** | at least 60% distinct-correct evidence in M5 and M6 plus one completed scored lab in each |
| **Revision milestone** | at least 60% distinct-correct evidence across M1–M4 |
| **Final case challenger** | full completion of the M7 final challenge lab and at least 50% distinct-correct evidence in every M1–M7 module |
| **Daily streak** | consecutive UTC days with a correctly completed daily challenge; no streak is created by visiting the dashboard |

The badge/XP calculations are recalculated from evidence at load/import, so visual clicks cannot independently manufacture an unlock.

## 5. Export/import workflow

### Export

The learner chooses **Export local progress**. The browser downloads a JSON backup named with the current date. It contains the local learning record and no external-resource content or hidden system credentials.

### Import

The learner must check a visible acknowledgement that import replaces the current browser record, then choose a JSON backup. The app validates the format/version, retains recognised evidence entries, derives XP/badges again, saves the state locally, and reports success/failure on the dashboard.

The export/import experience is a local continuity tool. It is not account sync, cloud backup, or institutional data transfer.

## 6. Actual implementation and tests

Implemented in `inft255-learning-environment.html`:

- local evidence record, state normalisation, load/save, and derived XP/badge recalculation;
- assessment-session evidence recording;
- scored Systems Lab best-score recording;
- evidence-based dashboard, recommendations, mastery status, badges, daily challenge, and streak;
- local JSON export/import controls and validation;
- profile level label updates; and
- responsive dashboard layouts.

Actual checks performed:

1. Python `HTMLParser` parsed the complete HTML document.
2. Extracted inline JavaScript passed `node --check`.
3. Existing JSDOM assessment/resource smoke test still passed after integration.
4. JSDOM progress smoke test confirmed local assessment evidence, scored-lab evidence, daily challenge completion/streak UI, dashboard rendering, and import controls.
5. JSDOM import smoke test confirmed valid evidence import and verified that a tampered `xp: 99999` import is recalculated to the correct derived XP value.
6. `git diff --check` passed.

## 7. Limitations and work still required

- State is browser-local; there is no user account, server sync, device-to-device sync, encryption, or official record.
- Subjective drafts and model-guide reveal state are intentionally session-only; they are not yet part of export/import.
- Daily challenges use UTC day keys; no claim is made about a lecturer-defined daily schedule.
- Question difficulty, badge thresholds, and XP quantities are author-created learning design choices, not official course marks.
- Manual browser/device accessibility, link-health, academic moderation, responsive visual review, and final end-to-end QA remain pending.

## 8. Review gate

Approve or request changes to the Phase 7 learner systems before final integration and dedicated QA work. The application is substantially more complete, but it is not yet declared complete: final course-wide navigation/content review, persistence edge cases, external-link audit, accessibility/responsive testing, visual-design review, and final QA remain required.
