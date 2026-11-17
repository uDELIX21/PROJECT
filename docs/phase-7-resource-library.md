# Phase 7 — Topic-Organised Resource Library

**Course:** INFT 255 — System Analysis & Design
**Scope:** Offline catalogue plus optional external enrichment links
**Status:** Implemented in the standalone app and smoke tested for review.

## 1. Library design and source-integrity policy

The **Resources** screen in `inft255-learning-environment.html` is now a searchable/filterable catalogue of 17 records. It works offline because record metadata is embedded locally; only an external destination needs an internet connection.

Learners can filter by Module/topic and resource type or search title, author/channel, topic, or concept. Each card includes:

- title;
- author, institution, channel, or course-built provenance;
- direct destination URL for external records;
- verified YouTube duration where available;
- relevant course topic;
- what to pay attention to;
- educational reason for recommendation;
- verification/access status; and
- an offline local-lab route where a practical demonstration exists inside the application.

A failed/unavailable external URL does not break the learning experience: the offline record remains visible with bibliographic/context details. Textbook lookup cards are deliberately labelled **unverified search suggestions** rather than being presented as checked book pages or verified editions.

## 2. Verified external catalogue

| Module / type | Title | Author / institution / channel | Direct URL | Topic | What to pay attention to | Why recommended | Verification / access status |
|---|---|---|---|---|---|---|---|
| M1 · Standards/legal context | Data Protection Act, 2012 (Act 843) | Ghana Legal Information Institute · Act of Ghana | https://ghalii.org/akn/gh/act/2012/843/eng@2012-05-18 | System constraints; personal-data context | Why student/patient data handling is a system constraint; it is not legal advice. | Ghana-specific, accessible constraint context for case scenarios. | **Verified** — accessible legislative text checked 17 Nov 2026. External text. |
| M2 · Academic/institutional guide | Guidelines for Planning and Development of Software for Buildings and Building Systems (NISTIR 7499) | Priya D. Lavappa · National Institute of Standards and Technology | https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir7499.pdf | SDLC, requirements, planning, schedules | Compare its structured lifecycle/templates with the course’s four high-level phases; do not equate labels. | Open government report with useful requirements and planning templates. | **Verified** — PDF, authorship, abstract, contents, and relevance checked 17 Nov 2026. Optional external PDF. |
| M2 · Academic publication | A Spiral Model of Software Development and Enhancement | Barry W. Boehm · *IEEE Computer* (1988) | https://ieeexplore.ieee.org/abstract/document/59 | Risk-driven Spiral development | Why each loop resolves a named uncertainty/risk. | Primary scholarly citation for Spiral-model context. | **Verified landing/abstract** — official IEEE record/metadata checked 17 Nov 2026. Full text may require access. |
| M3 · Academic/institutional guide | Continuous Risk Management Guidebook | Carnegie Mellon University Software Engineering Institute · Alberts et al. | https://www.sei.cmu.edu/library/continuous-risk-management-guidebook/ | Continuous risk identification, prioritisation, response, monitoring | How response/monitoring continue after initial scoring. | Credible reinforcement for risk-register ownership, triggers, and review. | **Verified** — CMU SEI page, author list, abstract, relevance, and PDF link checked 17 Nov 2026. |
| M4 · Standards/academic context | ISO/IEC/IEEE 29148:2018 — Requirements Engineering | IEEE Standards Association / ISO / IEC | https://standards.ieee.org/standard/29148-2018.html | Requirement quality, requirements processes, information items | Treat it as standards context for clarity/traceability, not a substitute for C1’s SRS lesson. | Grounds requirement quality in a recognised engineering-standard record. | **Verified official record** — scope/relevance checked 17 Nov 2026. Full standard is access-dependent. |
| M4 · Verified YouTube lecture | Systems Analysis and Design 4 — Requirements Modeling | Blancaflor Arada · YouTube | https://www.youtube.com/watch?v=NIm7fwvKq20 | Requirements analysis, fact finding, JAD, user involvement | **Duration: 1:00:17 (verified).** Watch fact-finding choices, JAD, and user involvement. | Long-form reinforcement for elicitation and requirements modelling. | **Verified** — public page, duration, description, and relevant transcript checked 17 Nov 2026. Channel institutional affiliation is not asserted. |
| M4 · Verified YouTube lecture | Systems Analysis and Design 5 — Data and Process Modeling | Blancaflor Arada · YouTube | https://www.youtube.com/watch?v=5xSLDaxUq64 | DFD symbols, levelling, balancing, common errors | **Duration: 50:10 (verified).** Watch process/data naming, balancing, black holes, and miracles. | Direct reinforcement for difficult DFD-validation skills. | **Verified** — public page, duration, description, and relevant transcript checked 17 Nov 2026. Channel institutional affiliation is not asserted. |
| M5 · Standards/formal specification | OMG Unified Modeling Language (UML), Version 2.5 | Object Management Group | https://www.omg.org/spec/UML/2.5/PDF | UML notation and semantic accuracy | Consult selectively for notation/terminology accuracy; it is a specification, not beginner teaching. | Primary formal reference for careful UML accuracy checks. | **Verified** — official formal specification page checked 17 Nov 2026. Technical external source. |
| M5 · Standards/version provenance | UML formal-version directory | Object Management Group | https://www.omg.org/spec/UML/ | UML version provenance | Why beginner sources can describe different taxonomy/version labels. | Supports version-aware teaching without a timeless diagram-count claim. | **Verified** — official directory checked 17 Nov 2026. |
| M5 · Verified YouTube lecture | Systems Analysis and Design 6 — Object Modeling | Blancaflor Arada · YouTube | https://www.youtube.com/watch?v=md4K1f_qpWQ | Objects, classes, attributes, methods, inheritance, UML orientation | **Duration: 37:42 (verified).** Watch class/object/attribute/method/message distinctions before CRC/class work. | Focused OO and object-modelling preparation. | **Verified** — public page, duration, description, and relevant transcript checked 17 Nov 2026. Channel institutional affiliation is not asserted. |
| M5 · Academic publication | Architectural Blueprints: The 4+1 View Model of Software Architecture | Philippe Kruchten | https://arxiv.org/abs/2006.04975 | Complementary architecture views and scenario-driven design | Relate use-case/logical/process/development/physical concerns to stakeholder questions. | Open author record grounding the complementary-view framework. | **Verified** — arXiv record, author, scope, PDF link, and relevance checked 17 Nov 2026. |
| M6 · Verified YouTube lecture | System Analysis and Design, Lecture 10: UML Activity Diagram, Swimlane Diagram | New Ur Academy · YouTube | https://www.youtube.com/watch?v=HdvXzD-2ONs | Activity diagrams, swimlanes, workflow modelling | **Duration: 33:08 (verified).** Watch action/control flow, decisions, and responsibility partitions. | Focused visual reinforcement for the activity/swimlane modelling task. | **Verified** — public page, duration, and scope description checked 17 Nov 2026. Channel institutional affiliation is not asserted. |

## 3. Clearly labelled recommended-reading search suggestions

These are derived from the supplied C1 bibliography but were **not** individually verified as exact external pages/editions. They are search aids, not citations or purchase recommendations.

| Module / type | Title / source basis | Creator details retained from C1 | Search URL | Topic / educational value | Verification status |
|---|---|---|---|---|---|
| M5 · Textbook/recommended reading suggestion | Course-provided object-oriented SAD bibliography lookup | C1 names Dennis, Wixom & Tegarden (2015, 5th ed.); Satzinger, Jackson & Burd (2016); Booch, Rumbaugh & Jacobson. | https://www.google.com/search?q=systems+analysis+design+Dennis+Wixom+Tegarden+2015+5th+edition | Starting point for OO analysis, UML, and SAD reading. Verify edition, authorship, access, and relevance through a library/catalogue. | **Unverified search suggestion** — individual title/edition/page availability was not checked. |
| M6 · Textbook/recommended reading suggestion | Course-provided software-engineering bibliography lookup | C1 names Whitten & Bentley (2017), Dennis, Wixom & Roth (2018), Tilley & Rosenblatt (2016), and Pressman. | https://www.google.com/search?q=systems+analysis+design+Pressman+Whitten+Bentley+recommended+reading | Starting point for software-engineering, architecture, deployment, and SAD reading. Confirm the exact work before relying on it. | **Unverified search suggestion** — individual title/edition/page availability was not checked. |

## 4. Offline practical demonstrations included in the library

| Module / type | Resource | Course-built provenance | What to practise | Why recommended | Status |
|---|---|---|---|---|---|
| M3 · Offline practical demonstration | Economic, critical-path, and risk model labs | INFT 255 Blueprint Studio; lecturer-supported Module 3 material | NPV/payback assumptions, critical path/slack, risk response. | Local calculations/decision feedback show working and interpretation without a network dependency. | Available offline; opens the Systems Lab. |
| M4 · Offline practical demonstration | Requirements, DFD, and ERD model clinics | INFT 255 Blueprint Studio; lecturer-supported Module 4 material | Testable requirements, DFD/balancing rules, ERD cardinality/M:N resolution. | Keyboard-accessible error repair aligns with actual course model rules. | Available offline; opens the Systems Lab. |
| M6 · Offline practical demonstration | UML architecture and behavioural model labs | INFT 255 Blueprint Studio; lecturer-supported Modules 5–6 material | Use cases, component interfaces, deployment, sequence, activity, state, validation. | Connects external UML references to no-network model decisions and corrections. | Available offline; opens the Systems Lab. |

## 5. Actual implementation and checks

Implemented in `inft255-learning-environment.html`:

- topic filter, resource-type filter, and text search;
- all 17 records rendered from local data;
- verification/status and access disclosure on every card;
- verified YouTube duration/channel/title/direct-link/topic/attention/recommendation fields;
- offline local practical-demonstration routing to the Systems Lab; and
- explicit resilience/unverified-search notices.

Actual checks performed:

1. Python `HTMLParser` parsed the full HTML document.
2. Extracted JavaScript passed `node --check`.
3. JSDOM smoke test confirmed 17 rendered records, text filtering to the four verified YouTube records, and local practical-resource navigation to Systems Lab.
4. `git diff --check` passed.

No current live re-check of external link availability, manual browser/device test, full link-health audit, or final accessibility/visual QA is claimed here.

## 6. Review gate

Approve or request changes to the resource library before the next Phase 7 segment: durable progress/dashboard/import-export and evidence-based gamification. The final application remains incomplete until its later integration and QA phases.
