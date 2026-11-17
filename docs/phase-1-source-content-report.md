# Phase 1 — Source and Content Report

**Course working title:** System Analysis & Design
**Prepared:** 17 November 2026 (UTC)
**Phase scope:** source analysis and academic research only — no app, curriculum, visual system, lesson build, or assessment bank has been implemented in this phase.

---

## 1. Executive finding

The supplied material supports a substantial, practice-oriented **System Analysis & Design** course, not a five-topic mini-course. The five weekly slide decks introduce systems, SDLC/methodologies, project planning/risk, and introductory UML. The 41-page comprehensive notes extend this to a coherent Week 1–13 syllabus covering requirements engineering; DFD and ERD; UML use-case, class, component, deployment, sequence, communication, activity, and state-machine diagrams; project portfolio work; a mid-semester examination; and a final case-study/project.

**Recommendation:** use the comprehensive notes as the proposed course spine and retain the five weekly decks as lecturer-provided reinforcement. This must be confirmed by the user/lecturer before Phase 2 because the material does not include an official catalogue outline.

**Important identity ambiguity:** the file name says `INFT_255`, whereas the cover of the comprehensive notes says `COMP 255`. The course code must not be guessed in the final product.

---

## 2. Source inventory and examination record

All six uploaded PDFs were opened, page-level text was extracted, and the diagram-led pages needed to understand the visual models were rendered and inspected. Page counts and internal authorship are taken from the PDFs themselves.

| ID | Uploaded source | Pages | Named author / origin inside file | Topics materially contributed | Reading status |
|---|---|---:|---|---|---|
| L1 | `WEEK_1_Lecture 01_System Analysis and Design (SAD).pdf` | 27 | Kwabena Adu | Definition of SAD; analysis vs design; system components, constraints, properties, boundaries, environment, and classifications | Examined in full |
| L2 | `WEEK_2_Lecture 02_System Analysis and Design (SAD).pdf` | 37 | PowerPoint material for Dennis, Wixom & Tegarden, *Systems Analysis and Design with UML*, 3rd ed.; copyright notice John Wiley & Sons (2009) | Four-phase SDLC; methodology categories and selection; Unified Process; UML overview; project roles and skills | Examined in full; methodology and UP diagrams visually inspected |
| L3 | `WEEK_3_Lecture 03_System Analysis and Design (SAD)_METHODOLOGIES.pdf` | 45 | No individual author shown | Waterfall, RAD, Spiral, V-Model; testing and verification/validation | Examined in full; all four model diagrams visually inspected |
| L4 | `WEEK_4_Lecture 04_System Analysis and Design (SAD)_PLANNING.pdf` | 34 | Veron Rue | Project planning, manager role, risk classes, assessment, response, planning, and monitoring | Examined in full |
| L5 | `WEEK_5_Lecture 05_System Analysis and Design (SAD).pdf` | 43 | Veron Rue | UML concepts, building blocks, relationships, diagram families, and use-case diagrams | Examined in full; embedded use-case examples visually inspected |
| C1 | `INFT_255_SYSTEM_ANALYSIS_AND_DESIGN_COMPREHENSIVE_NOTES_FOR_STUDENTS.pdf` | 41 | University of Energy and Natural Resources, Department of IT and Decision Sciences; 2026/2027; lecturer Philip Sarfo-Manu; internal title `COMP 255` | Full Week 1–13 sequence, learning outcomes, examples, quizzes, project work, assessment map, final case/project, reading list | Examined in full |

### Source authority and handling rules

- **C1 is the most complete lecturer-provided course source.** It explicitly presents a course order, assessment map, practical portfolio, and final assessment. This makes it the best provisional syllabus backbone, not proof of an official institutional catalogue.
- **L1–L5 are instructional source material, not automatically canonical standards.** They contain adapted/publisher-attributed content and occasional simplified wording. Later lessons will paraphrase rather than reproduce slide text or artwork.
- **Diagram images are teaching evidence, not app assets.** The app should create original accessible diagrams and interactions rather than copy publisher or slide graphics.
- **No official marking scheme, course outline document, or accessible quiz answer key was supplied.** C1 says answers are at the end of each week, but an answer-key section was not present in the provided notes. Answers for future practice questions must be independently validated and source-labelled.

---

## 3. Complete course-content inventory

### 3.1 Course-level learning progression present in C1

| Course block | Weeks | Central question | Models / skills introduced | Evidence |
|---|---|---|---|---|
| Foundations | 1 | What is a system, and what does analysis/design mean? | system diagram; IPO/feedback/control/boundary reasoning | C1 pp. 2–5; L1 |
| Process | 2–3 | How is a system developed, and which lifecycle fits? | SDLC deliverables; methodology comparison; Unified Process | C1 pp. 6–11; L2–L3 |
| Management | 4 | Should the project proceed, and how is it planned/risk-managed? | system request; feasibility; ROI/payback/NPV; WBS; Gantt; CPM; risk register | C1 pp. 12–15; L4 |
| Requirements and data/process modelling | 5 | What must the system do and what data/processes does it need? | SRS; requirements; DFD; ERD | C1 pp. 16–19 |
| Assessment / consolidation | 6 | Can the learner integrate Weeks 1–5? | mid-semester revision and modelling/calculation practice | C1 p. 20 |
| OO foundations and UML vocabulary | 7 | How do objects represent the problem domain? | OO concepts; UML building blocks; 4+1 views; UML diagram taxonomy | C1 pp. 21–23; L5 |
| Functional modelling | 8 | What goals do external actors achieve? | UML relationships; use-case diagram; textual use-case specification; traceability | C1 pp. 24–26; L5 |
| Structural modelling | 9 | Which classes and components realize the requirements? | CRC cards; class/object/component diagrams; interfaces and multiplicity | C1 pp. 27–30 |
| Architecture and deployment | 10 | How will the system be organized and deployed? | layers; coupling/cohesion; deployment and interaction overviews | C1 pp. 31–33 |
| Behavioural modelling | 11 | How do objects collaborate and how does work flow? | sequence; communication; activity; optional state-machine diagrams | C1 pp. 34–37 |
| Revision | 12 | How do the models connect and remain consistent? | cross-model consistency and mixed revision | C1 pp. 38–39 |
| Final assessment/project | 13 | Can the learner analyze and design a complete case? | integrated SAD package, final case study, presentation | C1 pp. 40–41 |

### 3.2 Detailed topic and concept inventory

#### Week 1 — systems and SAD foundations

- **Core definitions:** system; information system; system analysis; system design.
- **System elements:** input, process/processor, output, feedback, control, boundary, environment, subsystem.
- **Properties:** organization, interaction, interdependence, integration, central objective, adaptability.
- **Classifications:** natural/man-made; open/closed; deterministic/probabilistic; physical/abstract; TPS/MIS/DSS/ESS/expert system; adaptive/non-adaptive; permanent/temporary; social/human–machine/machine.
- **Professional practice:** analyst roles (business, systems, infrastructure, change-management, project manager); analytical, business, technical, communication, interpersonal, ethical skills.
- **Applied work:** system description/project charter, IPO/feedback/boundary diagram, constraints, team roles.
- **Direct source examples:** university registration/results, hostel booking, Mobile Money agent management, clinic appointments, cocoa purchasing.

#### Week 2 — SDLC, methodology overview, roles

- **SDLC phases:** planning, analysis, design, implementation.
- **Questions and deliverables:** system request/feasibility/project plan; system proposal; system specification; operational system/training/support plan.
- **Analysis/design methods:** as-is vs to-be, requirements gathering, design strategy, architecture/interfaces/database/program design, construction/testing/install/support.
- **Methodologies named:** waterfall, parallel, phased, system prototyping, throwaway prototyping, agile/XP.
- **Object-oriented delivery:** use-case-driven, architecture-centric, iterative, incremental; Unified Process phases (Inception, Elaboration, Construction, Transition); engineering/supporting workflows.
- **Professional roles:** business analyst, systems analyst, infrastructure analyst, change-management analyst, project manager; technical/business/analytical/interpersonal/management/ethical skills.
- **Visual evidence inspected:** waterfall, parallel development, phased development, system prototyping, throwaway prototyping, XP/Agile, and the two-dimensional Unified Process workflow diagram.

#### Week 3 — lifecycle methodology selection

- **Waterfall:** requirements → design → implementation/unit testing → integration/system testing → operation/maintenance; appropriate conditions, benefits, limits.
- **RAD:** business, data, and process modelling; application generation; testing/turnover; modular/time-boxed delivery; user workshops and early testing.
- **Spiral:** risk-driven repeated loops; objectives/alternatives/constraints; risk resolution; development/validation; next-loop planning.
- **V-Model:** planned matching verification/validation stages; requirement-to-acceptance-test, system-design-to-system-test, architecture-to-integration-test, module-design-to-unit-test mappings.
- **C1 extension:** incremental, iterative, Big-Bang, throwaway/evolutionary prototyping, Agile; selection criteria for requirements certainty, technical/business risk, speed, and safety criticality.
- **Practical work:** 1,000-word methodology selection report with comparison matrix, chosen lifecycle diagram, increments/iterations timeline.
- **Visual evidence inspected:** waterfall, RAD, spiral, and V-model diagrams.

#### Week 4 — project planning and risk management

- **Project setup:** planning begins before technical work; scope, resource need, size/cost/effort estimation, schedule, monitoring, staffing.
- **Initiation:** system request (sponsor, business need, high-level requirements, business value, special issues).
- **Feasibility:** technical, economic, organizational; project selection/strategic fit.
- **Economic calculations:** ROI, payback, NPV (with a worked Ghana-cedi registration-system example).
- **Planning:** WBS, Gantt chart, PERT/CPM, dependencies, critical path, slack, estimation approaches, timeboxing, scope creep, Brooks’ Law.
- **Risk:** risk versus current issue; project/technical/business; known/predictable/unpredictable; technology/people/organizational/tools/requirements/estimation risk categories.
- **Risk cycle:** identify; analyse/score; respond; monitor and control. Responses: avoid, mitigate/reduce, transfer, accept; contingency and triggers.
- **Quantitative reasoning:** priority/exposure as probability × impact; risk leverage formula in L4.
- **Practical work:** feasibility study, 12+ task WBS, Gantt/critical path, six-risk register.

#### Week 5 — requirements, DFD and ERD

- **Requirement hierarchy:** business, user, functional, non-functional requirements; characteristics of a good requirement.
- **Elicitation:** interviews, JAD, questionnaires, document analysis, observation; user stories.
- **Analysis strategies:** problem/root-cause/duration/activity-based-costing/benchmarking/outcome/technology/activity-elimination analysis.
- **SRS:** scope and definitions, product description, functional/non-functional/external-interface requirements, models/glossary/traceability; requirement IDs and testability.
- **DFD:** external entity, process, data store, data flow; context/Level-0/Level-1 etc.; balancing and naming; black hole, miracle, direct-flow/control-flow mistakes.
- **ERD:** entity, attribute, PK, FK, relationship, cardinality, participation; associative entity for M:N relationships.
- **Practical work:** two gathering activities; SRS with 12 functional and six non-functional requirements; context/Level-0/Level-1 DFD; ERD with five or more entities.

#### Week 6 — mid-semester consolidation

- **Coverage:** Weeks 1–5 for 15 marks.
- **Expected skills:** compare methodology, calculate a critical path, model a context diagram, reason about organizational feasibility, show work for economic/network calculations, verify DFD rules/balancing.

#### Week 7 — OO foundations and UML vocabulary

- **OO concepts:** class, object, attribute, method, message, encapsulation, information hiding, inheritance, polymorphism, dynamic binding; abstract versus concrete class.
- **UML purpose:** specification, visualization, construction, and documentation; UML as a language rather than a lifecycle method.
- **Building blocks:** things, relationships, diagrams; structural, behavioural, grouping, annotational things; dependency, association, generalization, realization; constraints/stereotypes/tagged values.
- **Architecture:** use-case, logical, process, implementation/component, deployment views (4+1 model).
- **UML taxonomy:** structural; behavioural; interaction diagrams and intended use.
- **Practical work:** candidate classes; inheritance/polymorphism; individual UML modelling plan.

#### Week 8 — UML relationships and use cases

- **Relationships:** dependency, association, aggregation, composition, generalization, realization; multiplicity.
- **Use-case modelling:** actor, use case, system boundary, association, `«include»`, `«extend»`, generalization; actor/goals identification.
- **Use-case descriptions:** ID, actors, stakeholders, trigger, pre/postconditions, normal/alternate/exception flows and non-functional notes.
- **Practical work:** four actors, ten use cases, include/extend/generalization, three full descriptions, SRS-to-use-case traceability.
- **Visual evidence inspected:** online-shopping use-case diagram and include/extend example.

#### Weeks 9–11 — UML structural, deployment, and behavioural models

- **Class/object diagrams:** textual analysis, CRC cards, responsibilities/collaborators, class box compartments, visibility, relationships, association class, multiplicity, constraints, validation.
- **Component diagrams:** modular components, provided/required interfaces, ports, dependencies.
- **Architecture/deployment:** HCI/problem-domain/data-management/physical layers; low coupling/high cohesion; nodes, artifacts, protocols, client-server/tier/cloud choices and local infrastructure constraints.
- **Sequence diagrams:** participant, lifeline, activation, synchronous/asynchronous/return/self messages, creation/destruction, `alt`/`opt`/`loop`/`par`/`ref` fragments.
- **Communication diagrams:** object links and numbered/nested messages; contrast with sequence diagrams.
- **Activity diagrams:** initial/final nodes, action/control/object flows, decisions/merges, guards, fork/join, swimlanes.
- **Extension:** state-machine diagrams for the lifecycle of a complex object.
- **Practical work:** class/component/deployment models; for three use cases, activity + sequence + communication models; cross-model consistency check.

#### Weeks 12–13 — revision and final integrated assessment

- **Concept integration:** what vs how, incremental vs iterative, DFD vs flowchart, ERD vs class diagram, include vs extend, aggregation vs composition, sequence vs communication, activity vs state machine, association vs dependency.
- **Final assessment:** full SAD case; use-case description; class, sequence, activity and deployment diagrams; final group portfolio/document and 10-minute presentation.

---

## 4. Assessed work and deliverable evidence

### Formal assessment map stated in C1

| Component | Mark share | Evidence / implication for the learning product |
|---|---:|---|
| Attendance | 5 | Product may track engagement, but must not claim to record official attendance without institutional integration. |
| Quizzes | 10 | Topic practice, corrective feedback, and revision views are directly relevant. |
| Assignments | 10 | Learners need model-building scaffolds and rubrics, not only multiple-choice recall. |
| Mid-semester examination | 15 | Needs Weeks 1–5 mixed concept/calculation/diagram preparation. |
| Final examination / project | 60 | Needs cross-model case practice, diagram literacy, traceability, and integrated portfolio support. |

### Existing assessment material

C1 contains approximately 112 quiz/revision prompts across Weeks 1–12, but they are mixed short answer, true/false, calculations, scenario recommendations, and diagram tasks — **not** a validated 100-question MCQ bank. Answers are not accessible in the supplied PDFs.

Existing assignment constraints that future learning activities must respect:

1. **Methodology Selection Report:** about 1,000 words; compare at least four models on requirement stability, team size, risk, deadline, and user availability.
2. **Use Case Model:** at least four actors, ten use cases, an `«include»`, an `«extend»`, a generalization, and three detailed use-case descriptions.
3. **Behavioural Models:** one key-use-case activity diagram with swimlanes/decision/fork-join; normal and alternate sequence flows; a communication-diagram conversion; a class-model update.
4. **Final group portfolio:** Sections 1–11, executive summary, consistency/traceability, and 10-minute presentation.

**Assessment limitation:** The Phase 6 target of 100 quality MCQs and 20 subjective questions cannot be honestly declared complete from the source material alone. Later questions must be authored individually, mapped to outcomes/source sections, reviewed for correctness and non-repetition, and clearly separate lecturer-based facts from supplementary theory. A lecturer answer key, marking rubric, or past paper would materially improve alignment.

---

## 5. Content relationships that must drive future teaching

The course is deliberately cumulative. A later diagram must not appear as an isolated drawing exercise.

```text
System purpose, boundary, constraints
        ↓
Business need / feasibility / lifecycle choice / plan / risks
        ↓
Requirements (SRS) ─── DFD (process/data movement) ─── ERD (data structure)
        ↓
Use cases (actors and goals) ─── traceability to functional requirements
        ↓
Candidate classes / CRC / class model / components
        ↓
Architecture and deployment constraints
        ↓
Sequence + communication + activity models
        ↓
Cross-model validation → final SAD package
```

This means that future learning should retain one or more persistent case systems (for example, course registration and hostel booking) so a learner can observe the same requirement propagate into DFD, ERD, use case, class, sequence, activity, component, and deployment models.

---

## 6. Research needs and verified supplementary resource catalogue

### Verification method

A resource is labelled **Verified** only where its direct page/URL was opened on 17 November 2026 and the retrieved content was relevant to the named topic. “Verified landing/abstract” means the direct record was checked but the complete publication requires purchase or subscription; it is not a claim that the full text was accessed. No video is described as university-produced unless its page establishes that provenance.

| # | Title and direct URL | Author / lecturer / institution / channel | Relevant topic | Educational value | Verification status |
|---:|---|---|---|---|---|
| 1 | [OMG Unified Modeling Language (UML), Version 2.5](https://www.omg.org/spec/UML/2.5/PDF) | Object Management Group (OMG) | Weeks 7–11 UML notation and semantics | Primary formal reference for checking terminology and diagram semantics when authoring original models. | **Verified — full official specification page opened.** It identifies Version 2.5 as a formal minor revision of UML 2.4.1. Use selectively; it is a specification, not beginner teaching material. |
| 2 | [UML formal-version directory](https://www.omg.org/spec/UML/) | Object Management Group (OMG) | UML version provenance | Confirms which historical formal UML version pages are available from the standards body. | **Verified — official page opened.** It lists UML 2.5 (June 2015) as its current formal version link. |
| 3 | [Guidelines for Planning and Development of Software for Buildings and Building Systems (NISTIR 7499)](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir7499.pdf) | Priya D. Lavappa, National Institute of Standards and Technology (2008) | Weeks 2–4: SDLC, waterfall planning, requirements and schedules | An open government report with an SDLC chapter, a requirements template, and project schedule template. It is a structured worked reference, not a replacement for the course’s four-phase vocabulary. | **Verified — open PDF opened; title, author, abstract, contents, and relevance checked.** |
| 4 | [ISO/IEC/IEEE 29148:2018 — Requirements engineering](https://standards.ieee.org/standard/29148-2018.html) | IEEE Standards Association / ISO / IEC | Week 5: requirement quality, requirements processes and information items | Supports the treatment of requirements as clear, traceable, lifecycle-managed engineering artifacts rather than informal feature requests. | **Verified — official standard record opened.** Full standard is purchase/subscription access; do not claim the learner receives its full text. |
| 5 | [A Spiral Model of Software Development and Enhancement](https://ieeexplore.ieee.org/abstract/document/59?reload=true) | Barry W. Boehm, *IEEE Computer*, 21(5), 1988, pp. 61–72; DOI: 10.1109/2.59 | Week 3: Spiral model | The primary scholarly citation for the risk-driven model. Useful to anchor the course’s four-activity spiral explanation. | **Verified — IEEE record and abstract opened.** Full article requires sign-in/purchase; cite only metadata/abstract-supported claims unless licensed access is later supplied. |
| 6 | [Continuous Risk Management Guidebook](https://www.sei.cmu.edu/library/continuous-risk-management-guidebook/) | Christopher J. Alberts, Audrey J. Dorofee, Ron Higuera, Richard L. Murphy, Julie A. Walker, Ray C. Williams; Carnegie Mellon University Software Engineering Institute (1996) | Week 4: continuous risk identification, prioritisation, response and monitoring | A directly relevant guidebook that frames risk management as continuous practice and offers a downloadable PDF. | **Verified — CMU SEI landing page opened; author list, abstract, relevance, and PDF link checked.** |
| 7 | [Architectural Blueprints: The 4+1 View Model of Software Architecture](https://arxiv.org/abs/2006.04975) | Philippe Kruchten; open early draft of the IEEE Software paper | Weeks 7 and 10: use-case/logical/process/development/physical views | Gives scholarly grounding for the architecture-view framework used in C1 and helps distinguish stakeholder concerns. | **Verified — arXiv abstract record opened; author, scope, PDF link, and relevance checked.** |
| 8 | [Data Protection Act, 2012 (Act 843)](https://ghalii.org/akn/gh/act/2012/843/eng@2012-05-18) | Ghana Legal Information Institute (GhaLII); Act of Ghana | Week 1/10 constraints; student/patient/personal data scenarios | Verifies the lecturer material’s Ghana-specific legal-constraint example. It establishes data protection/processing context for case studies; it is not a substitute for legal advice. | **Verified — accessible legislative text opened.** It identifies Act 843, its assent/commencement dates, purpose, and data-protection commission provisions. |
| 9 | [Systems Analysis and Design 4 — Requirements Modeling](https://www.youtube.com/watch?v=NIm7fwvKq20) | Blancaflor Arada (YouTube), 1:00:17 | Week 5: systems-analysis activities, requirements modelling, JAD, fact finding | A longer supplementary explanation that visibly covers requirements modelling, elicitation, JAD, analysis activities, and related skills. | **Verified — public video page, duration, description, and relevant transcript opened.** Channel institutional affiliation is not asserted; use as optional reinforcement, not primary authority. |
| 10 | [Systems Analysis and Design 5 — Data and Process Modeling](https://www.youtube.com/watch?v=5xSLDaxUq64) | Blancaflor Arada (YouTube), 50:10 | Week 5: DFDs, levelling, balancing and process/data naming | The transcript directly covers DFD purpose, notation families, black holes/miracles, levelling, and balancing — high-value support for a difficult diagram topic. | **Verified — public video page, duration, description, and relevant transcript opened.** Channel institutional affiliation is not asserted. |
| 11 | [Systems Analysis and Design 6 — Object Modeling](https://www.youtube.com/watch?v=md4K1f_qpWQ) | Blancaflor Arada (YouTube), 37:42 | Weeks 7–9: objects, attributes, methods, classes, instances, inheritance and UML orientation | A relevant preparatory explanation before class diagrams and OO modelling. The transcript identifies the course/object-modelling learning objectives. | **Verified — public video page, duration, description, and relevant transcript opened.** Channel institutional affiliation is not asserted. |
| 12 | [System Analysis and Design, Lecture 10: UML Activity Diagram, Swimlane Diagram](https://www.youtube.com/watch?v=HdvXzD-2ONs) | New Ur Academy (YouTube), 33:08 | Week 11: activity diagrams and swimlanes | Focused visual reinforcement for activity/swinlane modelling, a key behavioural-model task in C1. | **Verified — public video page, duration, description, and scope description opened.** Channel institutional affiliation is not asserted. |

### Course-provided bibliography retained for future citation checking

C1 lists Dennis, Wixom & Tegarden (2015, 5th ed.); Satzinger, Jackson & Burd (2016); Whitten & Bentley (2017); Dennis, Wixom & Roth (2018); Tilley & Rosenblatt (2016); Booch, Rumbaugh & Jacobson; Boehm (1988); Kruchten (1995); ISO/IEC/IEEE 29148; and Pressman. These are appropriate leads, but no copyrighted text will be treated as externally verified or reproduced unless an accessible source is individually checked.

---

## 7. Accuracy, currency, and source-integrity review

The goal is not to overwrite the lecturer’s materials. It is to teach their concepts accurately, label any clarification, and avoid importing unverified claims.

| Area | Issue found | Required treatment in later content |
|---|---|---|
| Course code | File name `INFT_255` conflicts with C1 cover `COMP 255`. | Ask user/lecturer; do not hard-code either code until confirmed. |
| Scope | Weekly slide decks stop at Week 5 while C1 specifies Week 1–13. | **Resolved by user approval (17 November 2026):** use C1 as authoritative where richer and cover the full 13-week sequence. |
| UML diagram count | L5 says 13 UML diagram types; L2/C1 describe UML 2.x as 14. UML version families and classifications change across materials. | Use a version-labelled lesson based on the checked OMG UML 2.5 reference; explain that interaction diagrams are a behavioural subset and avoid treating a single diagram count as timeless. |
| UML association notation | L5 describes association using a dotted line. Standard UML teaching normally uses a solid association line; a dashed arrow is commonly used for dependency. C1 has the more appropriate distinction. | Correct this explicitly in an **accuracy note** and quiz notation carefully. Do not copy the slide wording. |
| Encapsulation and coupling | L5 says encapsulation binds data/object “enabling tight coupling.” Encapsulation/information hiding should not be taught as a benefit of tight coupling. | Teach encapsulation and information hiding accurately; explain the design preference for low coupling and high cohesion, as C1 later does. |
| “Non-adaptive machines” | L1 gives machines as an example of non-adaptive systems. This is an overgeneralisation; many engineered systems adapt through feedback/control. | Present classifications as analytic lenses and ask learners to justify a classification under stated assumptions. |
| Waterfall/RAD simplification | L3 describes strict one-way waterfall and calls RAD linear-sequential while also discussing prototyping. These are useful introductory models but can conceal feedback/iteration. | Label as a plan-driven textbook representation; distinguish staged RAD from prototyping/iterative practices; teach model selection, not dogma. |
| Risk-process naming | L4 says three main activities but separately includes identification, analysis, control/planning/monitoring; C1 states four activities. | Use the transparent four-step cycle: identify → analyse → response-plan → monitor/control. Map L4 wording rather than claim a contradiction. |
| Risk scoring | L4 uses `p = r × s`; C1 uses probability × impact with 1–5 scoring. | Explain scale choices and units. Do not imply risk scores are precise probabilities; use ranking/priority examples. |
| Project-failure figures | C1 repeats a 1996 Standish statistic; L2 presents 2004–05 failures/losses. | Treat these as historical teaching examples with attribution and date, never as current industry statistics. Do not amplify them without up-to-date verification. |
| Legal example | C1 names Ghana’s Data Protection Act, 2012 (Act 843). | It was checked through GhaLII. Label it as a contextual design constraint, not legal advice; do not infer specific compliance obligations beyond the accessible legislative text. |
| Question answers | C1 says quiz answers are at the end of each week, but no accessible answer key is present. | Do not silently infer a lecturer-approved key. Build feedback from vetted reasoning and label it author-created; request official answers/rubric if available. |
| Copyright | L2 has a Wiley copyright notice; other slides may incorporate third-party graphics. | Create original diagrams/explanations. Do not embed lecture/PDF pages or reuse publisher visuals in the final app. |

### Additional explanation priorities

The supplied materials need deeper, interactive explanations in these places before assessment questions are written:

1. **System boundaries, control, feedback, and environment** — distinguish them with the same Ghanaian case instead of memorised definitions.
2. **Methodology selection** — learners need scenario trade-offs, not lists of advantages/disadvantages.
3. **Critical path and slack** — calculations require active network manipulation and working, not a static Gantt image.
4. **Requirement quality and traceability** — convert vague requirements into testable FR/NFR statements and connect each to use cases/models.
5. **DFD versus flowchart and DFD balancing** — common misconception area; needs immediate-error feedback.
6. **ERD-to-class-model boundary** — entities/data persistence versus objects/behaviour/inheritance.
7. **`«include»` versus `«extend»` and actor versus internal component** — common UML errors and an excellent candidate for an interaction.
8. **Association/aggregation/composition and multiplicity** — need life-cycle/ownership counterexamples, not only symbols.
9. **Sequence versus communication diagrams** — same scenario in two views; messages must match class operations.
10. **Deployment architecture under local constraints** — use power, bandwidth, device, and data-privacy constraints without inventing local statistics.

---

## 8. Content labelling policy proposed for the learning environment

Every future lesson, card, diagram, worked example, resource, or question should carry one of these internal source labels (and expose an understandable learner-facing version where useful):

| Label | Meaning | Examples in this course |
|---|---|---|
| **Lecturer material** | Directly supported by an uploaded PDF | four SDLC phases; C1’s course-registration example; project-work requirements |
| **Supplementary academic explanation** | Added to clarify/enrich and backed by a checked academic/standards source | formal UML terminology; requirements-engineering lifecycle framing; 4+1 architecture context |
| **Standards / legal context** | A verified standards body, law, or official technical source | OMG UML specification; Act 843 example; IEEE 29148 record |
| **Applied example** | An original teaching scenario illustrating the concept, not a claim about the lecturer/course | an original hostel-booking DFD or risk-register scenario |
| **Accuracy note** | A transparent clarification where a supplied slide is simplified, dated, or inconsistent | UML diagram taxonomy; association notation; historical failure figures |

No resource, video, claim, statistic, answer, or link should be called verified unless the relevant page has actually been checked.

---

## 9. Limitations and unresolved items

1. **No course outline/rubric/past paper was attached.** C1 is the strongest supplied syllabus document but may not be the official course catalogue.
2. **Course identity resolved by user approval (17 November 2026):** use `INFT 255` in the product title. The `COMP 255` cover label remains in source traceability only.
3. **Syllabus scope resolved by user approval (17 November 2026):** treat C1 as authoritative where richer and cover the full Week 1–13 sequence.
4. **No accessible official answer key:** supplied questions cannot be represented as lecturer-approved scored answers without validation.
5. **Some lecture visuals have no accompanying semantic explanation:** diagrams were inspected where essential, but future app diagrams will be original, source-tagged re-creations rather than scanned reproductions.
6. **External resource access varies:** IEEE 29148 and Boehm are verified via official records/abstracts but full content is restricted; their links should be presented honestly as access-dependent.
7. **No claims are made about testing or app functionality.** Nothing has been implemented yet.

---

## 10. Phase 2 approval record

**Approval received on 17 November 2026.** The user confirmed all Phase 2 gates:

1. Use **INFT 255** as the product course code.
2. Treat C1’s full **Week 1–13** scope as authoritative where it is richer than the Week 1–5 slides.
3. Cover the complete 13-week course, including requirements and advanced UML modelling.
4. No official course outline, rubric, past exam, or answer key is available.

The resulting curriculum architecture is recorded in `docs/phase-2-curriculum-learning-architecture.md`.
