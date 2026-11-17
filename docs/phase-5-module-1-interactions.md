# Phase 5 — Module 1 Interactive Learning Implementation

**Course:** INFT 255 — System Analysis & Design
**Scope:** Module 1 only — Systems Thinking and the Role of SAD
**Status:** Implemented and tested for review; later modules, durable progress, gamification, assessment modes, and final integration remain out of scope for this phase.

---

## 1. Implemented delivery file

`inft255-learning-environment.html` is now the evolving standalone HTML application shell. It uses only embedded HTML, CSS, JavaScript, inline SVG, and optional normal external links in the resource records. It has no framework, build step, backend, remote font, image, stylesheet, or JavaScript runtime dependency.

The Phase 3 prototype was deliberately evolved into this file rather than rebuilt as a separate application. The final required standalone HTML will continue to grow from this single file in later approved phases.

---

## 2. Functional Module 1 interactions

All six interactions originate from the approved Module 1 content blueprint and require active classification or reasoning. Each has keyboard-operable radio/select controls, reset capability, explicit answer checking, row-level explanation, and an `aria-live` feedback summary.

| Interaction | Syllabus concept | Learner action | Implemented feedback / learning value |
|---|---|---|---|
| **System boundary explorer** | system boundary, environment, external actor/system | classify registration elements as inside the system or outside/environment | explains why processes/records are internal while Student, Bank, and external policy context are outside for the stated scope |
| **IPO, control, and feedback mapper** | input, process, output, control, feedback | assign each registration item to its system role | differentiates data entering, transformation, result, rule, and correction information |
| **Analysis versus design sorter** | what versus how | classify statements as analysis/requirement or design choice | explains functional/non-functional outcomes versus selected technical mechanisms |
| **Constraint impact matrix** | schedule, technology, legal/privacy, policy constraints | select the most direct implication of a stated constraint | connects limits to consequences without treating a constraint as a feature |
| **System classification cards** | origin, openness, TPS, human-machine system | select classifications for a registration service | explains that categories need justification and applies the Phase 1 accuracy note about adaptation |
| **Role hand-off scenario** | business/systems/infrastructure/change/project-manager roles | match a concern to the role most directly responsible | makes role responsibility and organisational value explicit |

### Representative lesson and practice interactions retained

- **Lesson flashcard:** keyboard/click reveal for a central definition-retrieval question.
- **Untimed practice item:** a genuine Module 1 boundary question with selectable response and reasoned explanatory feedback.
- **Theme preference:** light/dark state is persisted locally with `localStorage` under `inft255-theme`. This is a visual preference only, not learning-progress persistence.
- **Responsive navigation:** labelled desktop navigation and a keyboard-accessible mobile drawer.

---

## 3. Content integrity

- The Systems Lab uses the lecturer-supported UENR course-registration context from C1 and the Module 1 source map.
- Feedback uses the reasoning approved in `docs/phase-4-module-1-content.md`; it does not assert lecturer-approved marking.
- The resource screen exposes the verified Phase 1 resource records and correctly identifies that the linked external materials require connectivity.
- The dashboard labels XP, levels, daily challenge, progress, and portfolio validation as previews/planned mechanics. No XP, streak, badge, durable mastery, portfolio data, or score is awarded or stored in this phase.

---

## 4. Actual testing performed

On 17 November 2026, the following checks were run against `inft255-learning-environment.html`:

1. **HTML parser check:** Python `HTMLParser` successfully parsed the document.
2. **JavaScript syntax check:** the extracted inline script successfully passed `node --check`.
3. **Interaction inventory check:** a script confirmed that all six Module 1 activities are present exactly once: `boundary`, `ipo`, `analysis`, `constraints`, `classify`, and `roles`.
4. **Offline runtime-dependency check:** confirmed that the document has no external `<script>` or stylesheet `<link>` runtime dependency. Optional resource anchors remain external by design.
5. **Accessibility-marker check:** confirmed the presence of `aria-live`, reduced-motion handling, and local theme preference logic.
6. **Whitespace check:** `git diff --check` completed without errors.

These checks validate document parsing, JavaScript syntax, declared interaction inventory, and dependency structure. They are **not** a substitute for browser/device accessibility testing, learner testing, or assessment-validity review; those have not yet been claimed.

---

## 5. Known limitations and intentionally unimplemented requirements

The following are still in scope for future phases but are **not implemented** in this Module 1 interaction phase:

- full Module 1 lesson progression and completed lesson state;
- drag/mouse interaction alternatives (the current controls are deliberately keyboard-first classification controls);
- learner notes, bookmarks, and portfolio data persistence;
- 100+ MCQs, 20+ subjective questions, topic/mixed assessments, timed exams, answer reveal flow, and result history;
- XP, levels, badges, daily challenge scoring, streaks, mastery calculation, revision milestones, and final course challenge;
- progress import/export;
- Module 2–7 content and simulations;
- browser/device/responsive/manual accessibility test execution;
- final export/import, final offline QA, and final one-file production acceptance.

## 6. Phase 5 review gate

Review the implemented Module 1 Systems Lab and its explanation quality. On approval, the next work will remain progressive: develop the next approved module content and then add interactions against that content, while preserving the same standalone file and design system.
