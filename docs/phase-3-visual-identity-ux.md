# Phase 3 — Visual Identity and User Experience Specification

**Product:** INFT 255 — System Analysis & Design
**Status:** Phase 3 complete; representative prototype supplied for review; no full course/content engine has been built.
**Design objective:** a rigorous, calm, model-centred learning workspace for a technical undergraduate course — not a decorative lecture-note site.

---

## 1. Design direction

### Product character

INFT 255 should feel like a well-equipped **analysis studio**: precise, structured, and encouraging. The visual system prioritises:

1. **Cognitive clarity:** lesson structure, diagrams, question feedback, and next actions are more prominent than decorative UI.
2. **Visible evidence of learning:** mastery reflects completed artefacts and demonstrated checks, not page visits.
3. **Analytical confidence:** restrained colour, generous but not wasteful spacing, stable navigation, and explicit source labels help a learner distinguish evidence from examples.
4. **Diagram literacy:** models are treated as readable working objects with a text alternative and a purpose, not as image decorations.
5. **Offline resilience:** no remote fonts, icon packages, images, or runtime dependencies are necessary for the core visual shell.

### Original visual identity: **Blueprint Studio**

The identity combines a warm paper-like canvas with deep blueprint navy, a vivid teal action colour, and precise information accents. It deliberately avoids large gradients, stock illustrations, excessive motion, oversized cards, and generic “ed-tech” visual clichés.

- **Wordmark concept:** `INFT 255` / `System Analysis & Design`, paired with a small node-and-connector mark rendered in inline SVG.
- **Motif:** a thin, low-contrast structural grid appears only in headers/workspaces to suggest diagrams without competing with them.
- **Tone:** professional, direct, and academically transparent; feedback speaks in evidence-based language (“The process has no output”) rather than gamified praise alone.

---

## 2. Colour and token system

All token pairs are tested conceptually for text/background contrast and must be rechecked against the final implementation. Colours convey state in combination with text/icon/shape; colour alone is never the only signal.

| Token | Light value | Dark value | Role |
|---|---|---|---|
| `--canvas` | `#F6F7F3` | `#111815` | app backdrop |
| `--surface` | `#FFFFFF` | `#18221E` | cards, panels, inputs |
| `--surface-muted` | `#EEF1EC` | `#22302A` | secondary panels and selected rows |
| `--ink` | `#17251F` | `#EEF5F0` | primary text |
| `--ink-muted` | `#52625A` | `#ADC1B5` | supporting text |
| `--line` | `#D7DED8` | `#33453B` | borders and dividers |
| `--navy` | `#153A5B` | `#8EC8F3` | structural navigation / diagrams |
| `--teal` | `#087E6B` | `#4AD5BA` | primary action / complete state |
| `--amber` | `#A85D10` | `#F5B65A` | alert / needs attention |
| `--berry` | `#A23F53` | `#FF9CAF` | review/error / risk accent |
| `--blue-soft` | `#E7F1F8` | `#173B51` | information state |
| `--teal-soft` | `#E2F4EE` | `#153D35` | progress state |
| `--amber-soft` | `#FFF2DE` | `#483314` | warning state |

### State language

| State | Visual treatment | Required textual reinforcement |
|---|---|---|
| Complete / mastered | teal fill or check; progress value | “Mastered” / percentage and evidence count |
| Continue / active | navy outline / teal action | action label: “Resume lesson” |
| Review recommended | amber icon/chip | specific weak concept |
| Incorrect / repair | berry border/icon, never red-only | why it is invalid and what rule to revisit |
| Lecturer material | navy outlined source chip | “Lecturer material” |
| Supplement / standards | neutral outlined source chip | full source category text |
| Applied example | teal outlined source chip | “Applied example” |

---

## 3. Typography, spacing, shape, and motion

### Typography

Use an offline-safe system stack: `Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`. `Inter` is optional if locally available; the product must not fetch it.

| Role | Size / leading | Weight | Usage |
|---|---|---:|---|
| Display / course title | clamp(1.85rem, 3vw, 2.8rem) / 1.08 | 720 | dashboard greeting, key workspace title |
| Screen title | clamp(1.45rem, 2vw, 2rem) / 1.15 | 700 | screen heading |
| Section heading | 1.05–1.25rem / 1.25 | 700 | card headings, lesson sections |
| Body | 0.98–1rem / 1.6 | 430 | explanations and instructions |
| Small metadata | 0.75–0.84rem / 1.45 | 600 | source tags, labels, timestamps |
| Numeric metric | 1.5–2rem / 1 | 720 | streak, mastery, XP |

Text must remain selectable, reflow at 200% zoom, and never be rendered as an image. Line length in lesson reading columns should generally remain at 62–76 characters.

### Layout and spacing

- Base spacing unit: **4px**; standard scale: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64.
- Desktop shell: 272px persistent navigation, 1fr content frame, 32px page padding, max content width 1480px.
- Main reading/lesson column: 720–780px; supporting rail: 280–340px where helpful.
- Cards use 16–20px padding, 12px radius, a 1px border, and low-elevation shadow only where layering needs it.
- Data tables become stacked labelled rows on narrow screens rather than horizontal scroll by default.

### Motion

- Motion is functional: a 120–180ms transition for drawer, feedback, and flashcard state only.
- Respect `prefers-reduced-motion`; all content must stay usable when animation is disabled.
- No looping decorative animation. A progress update must have textual feedback and not depend on movement.

---

## 4. Information architecture and global navigation

| Destination | Learner question | Primary contents | Persistent utility |
|---|---|---|---|
| **Dashboard** | What should I do now? | continue card, module progress, mastery, weakness/strength, daily challenge, recent evidence | course switcher, profile summary |
| **Learn** | What do I need to understand? | module map, structured lesson, visual explanation, glossary, notes/bookmarks | source label and lesson progress |
| **Model Lab** | Can I reason through this model? | DFD/ERD/UML/CPM/risk interactive tasks and diagnosis | rule sheet, reset, accessible text description |
| **Practice** | Can I retrieve and apply it? | topic quizzes, flashcards, untimed practice, feedback history | mode, timer setting, filter by objective |
| **Exams** | Can I perform under assessment conditions? | mixed-topic sets, timed simulation, subjective case prompts, revealable model guides | timer, autosave, review queue |
| **Resources** | Where can I study further? | topic-organised verified library, source/access label, reading/watch focus | source filter and offline availability notice |
| **Portfolio** | Are my models coherent? | artefact spine, traceability, validation checks, export-ready status | case selector and integrity check |

Secondary controls: search, bookmarks, notes, import/export, theme, reduced-motion acknowledgement, and help are compact top-bar actions or a mobile overflow panel. They never displace the next learning action.

---

## 5. Representative screen specifications

### A. Dashboard

**Job:** make the next best learning action obvious in under five seconds.

- A compact course header shows current module, “continue” action, and 0–100 completion state.
- A large **Continue learning** panel names the exact concept and estimated study block, with an original mini-diagram preview rather than a hero image.
- Three balanced evidence metrics: module completion, practice accuracy, portfolio consistency. Do not show artificial “hours learned” as mastery.
- A `Mastery map` lists strong, active, and review-needed topics. It must name the weak rule (e.g., “DFD balancing”), not merely show a red bar.
- The daily challenge is a small retrieval task whose XP can only be awarded once correct/meaningfully attempted, not on opening the card.

### B. Lesson Studio

**Job:** turn a concept into an explanation, a visual model, a small check, and a next action.

1. Breadcrumb/module/lesson metadata and a source label.
2. A concise objective (“By the end, you can…”).
3. Explanation in chunks: definition → why it matters → annotated visual → worked example → common error.
4. A diagram card with a text alternative, legend, and an option to switch to a linear accessible description.
5. Key terms and a small flashcard/retrieval block.
6. One knowledge check with immediate reasoning, then an explicit next action: practise, model lab, or continue.

### C. Model Lab

**Job:** make a technical model rule observable and repairable.

- The interaction canvas is paired with a text/keyboard control list. Canvas manipulation is never the sole path.
- A `Rule in focus` banner cites the rule, e.g., “Every DFD process needs at least one input and one output.”
- A learner can inspect a deliberately flawed diagram, select the issue, receive a reasoned explanation, reset, or open the prerequisite explanation.
- Future labs will include: DFD balancing, ERD cardinality/M:N resolution, methodology selection matrix, critical path/slack, UML relationship semantics, use-case include/extend, class multiplicity, sequence-message/operation consistency, activity-flow guards/forks, and deployment mapping.

### D. Practice and Exam Studio

**Job:** differentiate low-stakes learning from assessment rehearsal.

- Mode selector: topic check, flashcards, untimed mixed practice, timed exam simulation.
- Question cards retain topic/outcome metadata internally; learner sees clear prompt, usable answer controls, submit state, then feedback.
- Feedback always gives correctness, explanation, misconception/review link, and source category. It does not merely say “Correct”.
- Subjective prompts hide model answer and mark guide behind a learner-activated “Reveal guide” control. Revealing does not imply answer submission or official grading.
- A timed mode has a visible timer and review/flag state, but no pressure effects, auditory alarms, or data loss on time expiry.

### E. Resource Library

**Job:** provide transparent, relevant enrichment without pretending every link is available offline.

- Organise by the eight curriculum modules and tag by type: verified video, standard, academic publication, textbook/reference, legal context, interactive tool.
- Every item exposes title, author/channel, direct URL, verification/access status, topic, duration if verified, `Pay attention to`, and `Why recommended`.
- External links use standard anchors with an explicit `Opens external resource` cue. Offline mode clearly states that resource metadata remains available but remote content needs connectivity.

### F. Portfolio / Consistency workspace

**Job:** show an evolving SAD package rather than a checklist of opened pages.

- The artefact spine is the primary navigation: System → Lifecycle → Plan → Requirements → Functional model → Structural model → Architecture/behaviour → Final package.
- Each stage shows evidence, source label, revision state, and validation dependencies.
- The “consistency scan” uses plain language: “UC-03 Register for Courses has no linked class operation yet.” It must not claim professional-model validation until implemented and verified.

---

## 6. Responsive rules

| Range | Navigation | Content behaviour | Priority |
|---|---|---|---|
| ≥1200px desktop | persistent labelled sidebar | dashboard grids may use 12 columns; lesson supports a narrow right rail | reading and model comparison |
| 768–1199px tablet / small laptop | 72px icon rail or collapsible labels | 6–8 column responsive grid; rail moves below lesson | preserve context and action labels |
| <768px mobile | bottom or drawer navigation with text labels; no icon-only primary destinations | one-column cards; 16px gutters; model canvas replaced/supplemented by linear controls | lesson reading, checks, flashcards, answer controls |
| <420px narrow mobile | drawer navigation; avoid bottom-bar crowding | metrics stack; resource table becomes labelled cards | text readability and form controls |

Minimum interactive hit area is 44×44 CSS px. Content must not require horizontal scrolling at 320px except where a labelled, controllable diagram viewport is genuinely necessary; then an equivalent text representation is supplied.

---

## 7. Accessibility requirements

The final application must be designed and tested against these implementation requirements:

- Semantic landmarks: skip link, `nav`, `main`, headings in order, labelled buttons/inputs, visible focus.
- Keyboard access for all menus, screen switches, flashcards, questions, timer controls, model-lab equivalents, source links, import/export, and theme settings.
- No colour-only status; icon/label/shape and `aria-live` feedback complement colour.
- Diagram cards include a concise summary, element list, relationships/flows, and keyboard-accessible inspection.
- Form errors and answer feedback use text and programmatic associations (`aria-describedby`, live region where appropriate).
- Support 200% zoom, browser text resize, high contrast, dark/light themes, and reduced motion.
- Reading order must match visual order. Avoid focus being trapped in the mobile drawer or flashcard.
- Timed assessment needs pause/accommodation settings in the eventual implementation; visual design reserves this control but does not make an unsupported claim today.

---

## 8. Gamification design rules for later phases

Gamification should affirm evidence, not reward navigation.

| Mechanic | Earned when | Not earned for | Dashboard representation |
|---|---|---|---|
| XP | correct retrieval, a completed explained repair, validated artefact step, reviewed revision task | opening a page, flipping a card without response | current XP and next level threshold |
| Level | cumulative verified XP threshold | arbitrary session time | named level with accessible numerical progress |
| Badge | meeting defined multi-step learning evidence | a single click or streak alone | criteria and date/evidence count |
| Daily challenge | meaningful attempt with explanation; full XP only after correct/repaired result | loading the challenge | small actionable card |
| Streak | one meaningful active-learning event on a local calendar day | passive reading | count plus “what preserved it” text |
| Topic mastery | sufficient performance across recall, application, and correction/revision | one lucky quiz attempt | mastery map by concept |
| Revision milestone | successful spaced return to a previously weak objective | automatic calendar passage | review queue / milestone chip |
| Final course challenge | integrated case/model consistency work | completion of all page views | capstone readiness panel |

Future content and scoring rules must be explicitly described before building them. The Phase 3 prototype only visualises their intended hierarchy; it does not award durable progress.

---

## 9. Prototype boundaries and Phase 4 gate

`inft255-learning-environment.html` is the evolving standalone, offline application shell. At Phase 3 it demonstrated the approved shell, colour tokens, dark mode, responsive navigation, dashboard hierarchy, a Lesson Studio state, a Model Lab visual, a practice-feedback state, and Resource Library presentation; later phases extend the same file rather than replace the visual direction.

It is **not** the final application and does not claim to implement course progress, question banks, assessment timing, simulations, note persistence, resource verification, portfolio validation, or the required 100 MCQs / 20 subjective questions. Those are content and interaction phases that must be developed and reviewed progressively.

### Phase 3 completion checkpoint

- Visual identity and design tokens: defined.
- Navigation and responsive behaviour: defined and prototyped.
- Dashboard and representative screens: defined and prototyped.
- Accessibility requirements: recorded for implementation/testing.
- Full lesson content, full design system production QA, simulations, assessments, resource library data, and gamification engine: intentionally deferred.

**Next phase after approval: Phase 4 — develop and review content module by module, beginning with M1 Systems Thinking and the Role of SAD.**
