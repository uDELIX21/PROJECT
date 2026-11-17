# Phase 2 — Curriculum and Learning Architecture

**Product:** INFT 255 — System Analysis & Design Learning Environment
**Prepared:** 17 November 2026 (UTC)
**Status:** Phase 2 design complete; awaiting review before visual design or implementation work begins.

---

## 1. Approved scope and curriculum decisions

| Decision | Approved direction | Consequence for the learning environment |
|---|---|---|
| Course identity | **INFT 255** | Use `INFT 255 — System Analysis & Design` as the product/course title. The conflicting `COMP 255` cover label is retained only in internal source traceability. |
| Syllabus authority | The comprehensive 2026/2027 notes (C1) are authoritative where they are richer than the short weekly slide decks. | Build the full Week 1–13 learning sequence, not merely five slide-based topics. |
| Course scope | Complete 13-week course, including requirements engineering and advanced UML modelling. | The final course path includes planning, requirements, DFD/ERD, UML functional/structural/behavioural models, architecture/deployment, revision, and final-case practice. |
| Assessment evidence | No official course outline, answer key, rubric, or past paper is available. | No future answer will be presented as lecturer-approved unless it comes from a provided source. Newly authored feedback must be reasoned, source-tagged, and internally reviewed. |

### Curriculum posture

The environment will teach learners to **produce and validate a coherent analysis-and-design package**, not just recognise definitions. It will move from a business problem to requirements, process/data models, object models, architecture, and behavioural models. Each stage must explicitly reuse outputs from earlier stages.

---

## 2. Course-wide learning outcomes

A learner who completes the approved INFT 255 pathway should be able to:

1. **Explain systems thinking** by identifying a system’s purpose, components, inputs, processes, outputs, feedback, controls, boundary, environment, constraints, and classification.
2. **Distinguish analysis from design** and identify the professional roles, skills, and ethical responsibilities involved in SAD work.
3. **Apply the SDLC** by placing deliverables, decisions, activities, and stakeholder responsibilities within planning, analysis, design, and implementation.
4. **Select and justify a development methodology** against requirement certainty, risk, schedule, safety, team capacity, technology familiarity, and user availability.
5. **Evaluate project viability and plan work** using a system request, technical/economic/organizational feasibility, ROI, payback, NPV, WBS, Gantt/CPM, slack, staffing, scope control, and a risk register.
6. **Elicit, write, analyse, and trace requirements** using testable functional/non-functional requirements, user stories, an SRS, and a traceability matrix.
7. **Model data and data movement** with balanced DFDs and correctly keyed/cardinalised ERDs, and explain the different questions each model answers.
8. **Apply OO and UML foundations** to identify classes, objects, attributes, methods, messages, encapsulation, inheritance, polymorphism, and architecture views.
9. **Create and critique UML models**: use-case descriptions/diagrams, class/object/component diagrams, deployment diagrams, sequence/communication diagrams, and activity diagrams (plus a state-machine extension where useful).
10. **Verify cross-model consistency** so requirements are represented by use cases, use cases are realised by class operations/messages, data persists appropriately, components are deployed on nodes, and design decisions respect constraints.
11. **Respond to examination-style case studies** with accurate terminology, defensible choices, visible calculations, labelled diagrams, and coherent justification.

---

## 3. Instructional architecture

### 3.1 Learning sequence

The primary path preserves the lecturer’s weekly order while grouping work into eight coherent modules. Each module ends with an observable artefact and a mastery check before a learner relies on it later.

```text
M0 Learn the course workflow
        ↓
M1 Systems and SAD foundations
        ↓
M2 SDLC and methodology choices
        ↓
M3 Planning, feasibility, scheduling and risk
        ↓
M4 Requirements, DFD and ERD
        ↓
M5 Object orientation and UML functional/structural models
        ↓
M6 Architecture, deployment and behavioural models
        ↓
M7 Revision, examination practice and capstone integration
```

### 3.2 Four learning modes

| Mode | Purpose | Where used | Not a substitute for |
|---|---|---|---|
| **Guided Study** | Explain a concept from first principles; expose misconceptions; practise one small skill at a time. | Every lesson | Project-quality modelling |
| **Case Studio** | Apply each week’s skill to one persistent system scenario and build a linked artifact. | Every module | A real stakeholder study |
| **Model Lab** | Manipulate a diagram/calculation, see structural errors, and explain a correction. | DFD, ERD, UML, CPM and risk topics | Professional modelling software |
| **Revision / Exam Practice** | Timed or untimed retrieval, calculations, diagram review, and case prompts. | Mid-semester and final modules | The lecturer’s official marking scheme |

### 3.3 Persistent case-system strategy

A learner should select one case context when starting Case Studio. The course-provided contexts are:

- UENR Online Course Registration & Results System *(default worked case; richest source support)*
- Campus Hostel Booking and Management System
- Mobile Money Agent Management System (Sunyani agent network)
- Clinic Appointment and Patient Records System
- Cocoa Purchasing and Payment Tracking System

The product will not invent stakeholder interviews or field data. It will offer clearly marked **simulated briefs** for practice. Learners using a real project must replace assumptions with their own verified stakeholder evidence.

### 3.4 Artifact spine

| Stage | Learner produces | Later dependency |
|---|---|---|
| Foundation | system description, context/boundary/IPO map, constraints, roles | system request; feasibility assumptions |
| Lifecycle | phase/deliverable map, methodology rationale, release/iteration view | project plan |
| Planning | system request, feasibility calculation, WBS, schedule/critical path, risk register | scope and constraints for SRS/design |
| Requirements | SRS, requirement IDs, traceability seed, context/levelled DFDs, ERD | actor/use-case identification; classes |
| Functional OO | use-case diagram and descriptions | sequence/activity scenarios; traceability |
| Structural OO | candidate classes, CRC cards, class/component diagrams | message operations; deployment choices |
| Architecture / behaviour | layers, deployment, sequence, communication, activity models | consistency review |
| Capstone | integrated SAD package, justification, presentation outline | final case/project practice |

---

## 4. Detailed module blueprint

### M0 — Course orientation and model-literacy setup

**Timing:** onboarding; before Week 1
**Prerequisites:** none
**Purpose:** establish what learners will make, how evidence is labelled, and why consistency matters before teaching notation.

| Lesson | Core knowledge / skill | Practice and case activity | Evidence of understanding |
|---|---|---|---|
| M0.1 What this course builds | SAD package, course project, assessed artefacts, analysis-to-design progression | Inspect a simplified completed artefact map; locate each type of evidence | Explain why a use-case diagram alone is not a full SAD solution. |
| M0.2 Reading model notation | diagram conventions, labels, legend, source labels, accessibility text descriptions | Read a small example diagram and its text alternative | Identify what is represented, omitted, and assumed. |
| M0.3 Academic integrity and source use | lecturer material vs supplement vs applied example vs accuracy note; no fabricated stakeholder findings | Mark sample statements with an evidence label | Distinguish a sourced claim from an illustrative assumption. |

**Mastery check:** learner can name the seven artifact-spine stages and identify what later model depends on an SRS.
**Design note:** this is an orientation, not an assessed lecture-week replacement.

---

### M1 — Systems thinking and the role of SAD

**Timing:** Week 1
**Prerequisites:** M0
**Source basis:** C1 pp. 2–5; L1 pp. 2–27
**Entry concepts:** everyday organisation/process examples.

| Lesson | Topics and subtopics | Learning objectives | Case Studio activity | Formative assessment |
|---|---|---|---|---|
| M1.1 System, information system, and purpose | system; IS; interrelated components; goal/value | Define system/IS in own words and identify the purpose of a candidate system. | Write a one-paragraph system description for the chosen case. | Sort examples into system / subsystem / environment and justify one ambiguous case. |
| M1.2 System elements | inputs, processing, outputs, feedback, control, boundary, environment, subsystems | Map each element correctly and distinguish feedback from a normal output. | Build an IPO-feedback-control-boundary map. | Diagnose mislabelled registration-system elements. |
| M1.3 Analysis versus design | what vs how; stakeholder audiences; common deliverables | Separate a business requirement from a technical design choice. | Rephrase five premature-design statements as analysis statements. | Scenario sort: analysis activity / design activity / both / neither. |
| M1.4 Constraints, properties, and classifications | budget/time/technical/legal/organisational/human/quality; organisation, interaction, interdependence, integration, adaptation; system types | Identify constraints and explain a classification under stated assumptions. | Record six case constraints and their design effects. | Explain why boundary/environment or deterministic/probabilistic labels are defensible. |
| M1.5 Analyst roles and project value | analyst roles, skills, ethics, user fit, failure causes | Match responsibilities to roles and explain why technical success alone can fail organisationally. | Assign temporary project roles and stakeholder questions. | Short scenario justification. |

**Common misconceptions to address:** boundary vs interface; environment vs subsystem; feedback vs output; “analysis means coding”; closed systems as a literal norm; every machine as non-adaptive.
**Module artefact:** System Description and Charter Seed (purpose, users, boundary/environment, IPO-feedback map, constraints, roles).
**Mastery criterion:** accurately classify at least 80% of system elements and explain two analysis/design differences with a case example.

---

### M2 — SDLC, methodology selection, and the Unified Process

**Timing:** Weeks 2–3
**Prerequisites:** M1; clear statement of a business problem
**Source basis:** C1 pp. 6–11; L2 pp. 2–37; L3 pp. 2–45; NISTIR 7499; Boehm (metadata/abstract only)
**Entry concepts:** problem, requirements, constraints, system boundary.

| Lesson | Topics and subtopics | Learning objectives | Case Studio activity | Formative assessment |
|---|---|---|---|---|
| M2.1 SDLC as gradual refinement | planning, analysis, design, implementation; steps, questions, deliverables, feedback into revisions | Place activities/deliverables in an SDLC phase and explain refinement. | Map three case activities and outputs to each phase. | Deliverable-to-phase match with explanation. |
| M2.2 Planning and analysis | system request; feasibility; workplan; as-is/to-be; gathering; proposal | Explain why the proposal is a decision point rather than a code artefact. | Draft a half-page system request. | Find unsupported claims in a weak system request. |
| M2.3 Design and implementation | build/buy/outsource; architecture; interfaces; data/program design; test/install/train/support | Distinguish design decisions from implementation/support tasks. | Outline implementation and support implications of the case. | Sequence an incorrect lifecycle story. |
| M2.4 Plan-driven and rapid models | waterfall, parallel, phased/incremental, system prototype, throwaway prototype, RAD, iterative, Big-Bang, Agile/XP | Compare model strengths/limits without treating a model as universally best. | Construct a model-choice matrix from case constraints. | Match a project condition to a defensible model, then reject one poor fit. |
| M2.5 Spiral and V-Model | risk-driven loops; objectives/alternatives/constraints; verification vs validation; test-stage pairing | Explain Spiral risk resolution and V-Model traceability. | Map a selected risk to a Spiral loop; pair a test with a V-stage. | Label an incomplete spiral/V visual model. |
| M2.6 Unified Process and OO delivery | Inception, Elaboration, Construction, Transition; engineering/supporting workflows; iterative/incremental/architecture-centric/use-case-driven | Interpret UP as overlapping workflow intensity, not a four-box waterfall. | Sketch an iteration/release timeline for the case. | Compare UP phases with four SDLC phases. |

**Required accuracy notes:** do not teach RAD as one fixed method; waterfall illustrations are plan-driven abstractions, not proof that feedback never occurs; retain historical examples as historical.
**Module artefacts:** SDLC Plan, System Request, Methodology Selection Matrix, Lifecycle/Release View.
**Mastery criterion:** give a criteria-based methodology recommendation and map every major course artefact to a lifecycle stage.

---

### M3 — Project initiation, feasibility, schedule, and risk

**Timing:** Week 4
**Prerequisites:** M1–M2; selected case and provisional methodology
**Source basis:** C1 pp. 12–15; L4 pp. 1–34; CMU SEI guide; NISTIR 7499; Ghana Act 843 as contextual legal source
**Entry concepts:** business need, constraints, cost/benefit, methodology choice.

| Lesson | Topics and subtopics | Learning objectives | Case Studio activity | Formative assessment |
|---|---|---|---|---|
| M3.1 System request and project selection | sponsor, business need, high-level requirements, value, special issues; strategic fit | Draft a concise request and distinguish benefit from a feature. | Improve the M2 request using an explicit sponsor/value/special-issues table. | Identify missing request elements. |
| M3.2 Feasibility | technical, economic, organisational feasibility; stakeholders, champions/resisters | Evaluate feasibility using evidence and stated assumptions. | Score a three-part feasibility snapshot. | Diagnose the feasibility type a scenario describes. |
| M3.3 Economic reasoning | costs/benefits, cash flow, ROI, payback, NPV, discounting | Calculate and interpret simple ROI, payback, and NPV; show working. | Recalculate a variant of the registration example and state a cautious recommendation. | Formula, working, and interpretation check. |
| M3.4 Work decomposition and schedule logic | WBS; task owner/duration/dependency/deliverable; Gantt; network; CPM; critical path; slack | Produce a network from dependencies and identify duration, critical path, and slack. | Build a 12+ task WBS and schedule. | Change one duration and explain the project effect. |
| M3.5 Estimation, staffing, scope | analogy, function points, COCOMO-type intuition, timeboxing, scope creep, change control, jelled teams, Brooks’ Law | Explain why estimates evolve and why adding people can delay a late project. | Write one change-control rule and staffing assumption. | Choose appropriate response to a scope/estimation scenario. |
| M3.6 Risk management | risk vs issue; categories; identification; qualitative analysis; exposure; avoid/mitigate/transfer/accept; contingency/triggers; monitoring | Build a prioritised risk register and make a proportionate response choice. | Create a six-risk register with score, owner, response, trigger, and contingency. | Distinguish risk/issue; rank responses and justify. |

**Common misconceptions:** positive ROI does not prove organisational feasibility; Gantt bars alone do not prove dependencies; critical path is the *longest* dependency path; risk score is prioritisation rather than a precise forecast; transfer does not eliminate a risk.
**Module artefacts:** Feasibility Study, Economic Calculation Sheet, WBS, Network/Gantt, Critical Path Analysis, Risk Register.
**Mastery criterion:** show correct calculation/process for each feasibility/scheduling task and defend one risk response against alternatives.

---

### M4 — Requirements engineering, DFD, and ERD

**Timing:** Week 5, with Week 6 consolidation
**Prerequisites:** M1–M3; accepted business need/scope/constraints
**Source basis:** C1 pp. 16–20; IEEE/ISO/IEC 29148 verified record; YouTube resources 9–10 in Phase 1 report
**Entry concepts:** stakeholder, system boundary, business problem, scope.

| Lesson | Topics and subtopics | Learning objectives | Case Studio activity | Formative assessment |
|---|---|---|---|---|
| M4.1 Requirement types and quality | business/user/functional/non-functional; clear, complete, consistent, testable, feasible, traceable, necessary | Classify requirements and turn vague statements into testable ones. | Create an initial FR/NFR list with IDs. | Improve deliberately vague requirements. |
| M4.2 Elicitation and analysis | interview, JAD, questionnaire, document analysis, observation; problem/root cause/duration/ABC/benchmark/outcome/technology/activity-elimination analysis; user stories | Select a technique for a stakeholder context and explain its limitation. | Design two simulated collection activities and record assumptions separately. | Technique-selection mini cases. |
| M4.3 SRS and traceability | SRS sections, product context, assumptions/dependencies, interface requirements, requirement IDs, traceability matrix | Organise an SRS and link requirements to later model elements. | Build the SRS outline and FR/NFR traceability seed. | Locate untestable, duplicated, and conflicting requirements. |
| M4.4 Context and levelled DFD | source/sink, process, data store, data flow; naming; context/Level-0/Level-1; decomposition | Create a context DFD and decompose it without adding/removing external flow. | Draw context and Level-0 models. | Identify incorrect process/data-flow naming and invalid direct flows. |
| M4.5 DFD validation | balancing; black holes, miracles, grey holes; logical data movement vs flowchart control | Test a DFD for structural validity and correct it. | Decompose one Level-0 process to Level-1. | Error-spotting Model Lab with correction rationale. |
| M4.6 ERD | entity, attribute, PK/FK, relationship, cardinality, participation, associative entity, composite key | Construct an ERD and resolve M:N accurately. | Define five entities, keys, cardinalities, and associative entities as needed. | Cardinality/foreign-key reasoning cases. |
| M4.7 DFD/ERD bridge and mid-semester readiness | process versus data model; data dictionary prompts; cross-model names | Explain why DFD and ERD are complementary rather than substitutes. | Run a names-and-data consistency check. | Mixed Week 1–5 case practice. |

**Common misconceptions:** a DFD is not a flowchart; a context diagram is not merely a small Level-0; flow labels are nouns; M:N is not solved by writing “many” twice; an NFR is not just a feature with a quality adjective.
**Module artefacts:** SRS, Requirement Traceability Seed, Context/Level-0/Level-1 DFDs, ERD, Data/Name Consistency Check.
**Mastery criterion:** write testable requirements; create a balanced DFD; resolve at least one M:N relationship; explain a data/process-model difference.

---

### M5 — Object orientation and UML functional/structural models

**Timing:** Weeks 7–9
**Prerequisites:** M4, particularly a stable SRS/ERD/DFD naming set
**Source basis:** C1 pp. 21–30; L5 pp. 1–43; OMG UML 2.5; Kruchten 4+1; YouTube resource 11 in Phase 1 report
**Entry concepts:** functional requirements, actor, entity/attribute, relationship, traceability.

| Lesson | Topics and subtopics | Learning objectives | Case Studio activity | Formative assessment |
|---|---|---|---|---|
| M5.1 OO analysis vocabulary | object/class/instance, attribute/state, method/message, encapsulation, information hiding, inheritance, polymorphism, dynamic binding, abstract/concrete | Describe an OO concept with a system example and distinguish class from object. | Extract a candidate vocabulary from the SRS. | Match concept to example/counterexample. |
| M5.2 UML purpose, building blocks and views | UML as language not method; things/relationships/diagrams; stereotypes, constraints; 4+1 views | Choose a diagram/view for a stakeholder question. | Create a UML model plan for the selected case. | Diagram-purpose/view matching. |
| M5.3 UML relationships and multiplicity | dependency, association, aggregation, composition, generalization, realisation; roles, multiplicity | Select notation that expresses ownership, temporary use, is-a, or contract implementation. | Annotate candidate relationships with rationale. | Relationship and multiplicity correction lab. |
| M5.4 Use-case diagrams | actor, user goal, system boundary, association, `«include»`, `«extend»`, generalisation | Identify external actors/goals and represent mandatory versus conditional shared behaviour. | Make a 4-actor/10-use-case diagram. | Correct bad “click button” use cases and reversed include/extend arrows. |
| M5.5 Textual use-case descriptions and traceability | ID, actor, trigger, pre/postconditions, normal/alternate/exception flows, NFR note; FR-to-UC traceability | Write a testable, goal-level use-case description. | Write three descriptions and link each to requirements. | Find missing preconditions/alternate flows. |
| M5.6 Candidate classes and CRC | textual analysis, nouns/verbs, filtering, responsibilities, collaboration, role-play | Identify candidate classes without turning every noun into a class. | Build five CRC cards and role-play two use cases. | Candidate-class decision rationale. |
| M5.7 Class and object diagrams | compartments, visibility, types, operations, association class, multiplicity, inheritance, object snapshots | Build a readable class model and test it against a real object snapshot. | Create an eight-class model with attributes, operations and relationships. | Diagnose multiplicity/visibility/association errors. |
| M5.8 Component diagrams | component, provided/required interface, port, dependency, replacement through interfaces | Explain module boundaries and interface dependencies. | Produce five components with provided/required interfaces. | Interface matching lab. |

**Required accuracy notes:** teach association as a solid line and dependency as a dashed arrow; do not imply encapsulation promotes tight coupling; state the UML version/framework when presenting taxonomy counts.
**Module artefacts:** UML Modelling Plan, Use-Case Diagram, Three Use-Case Descriptions, Traceability Matrix, Candidate-Class List, CRC Cards, Class/Object Diagram, Component Diagram.
**Mastery criterion:** trace an FR to a use case, a supporting class, and at least one class operation; explain every relationship/multiplicity in the class model.

---

### M6 — Architecture, deployment, and behavioural modelling

**Timing:** Weeks 10–11
**Prerequisites:** M5 structural/functional models; known NFRs/constraints
**Source basis:** C1 pp. 31–37; OMG UML 2.5; Kruchten 4+1; verified activity-diagram video (Phase 1 resource 12)
**Entry concepts:** use-case scenario, class operations, component interfaces, NFRs, risk/constraints.

| Lesson | Topics and subtopics | Learning objectives | Case Studio activity | Formative assessment |
|---|---|---|---|---|
| M6.1 From analysis to design | analysis versus design; validation/balancing; factoring, packages, layers; HCI/domain/data/physical layers; low coupling/high cohesion | Explain how analysis models are elaborated into design choices under constraints. | Sort classes/components into layers and record an architectural rationale. | Detect misplaced dependency/coupling problem. |
| M6.2 Deployment and physical architecture | nodes, devices/execution environments, artifacts, communication paths/protocols, client/server/tier/cloud choices, availability/bandwidth/power considerations | Map software artifacts to physical nodes and justify choices using NFRs. | Draw a four-node deployment model with artifacts and protocols. | Node/artifact/protocol distinction check. |
| M6.3 Sequence diagrams | scenario selection, participants, lifelines, activations, synchronous/asynchronous/return/self messages, creation/destruction, `alt`/`opt`/`loop`/`par`/`ref` | Translate a use-case flow into time-ordered valid messages. | Create normal and alternate sequence scenarios. | Find messages that lack receiving operations. |
| M6.4 Communication diagrams | links, numbered/nested messages, structure emphasis, semantic equivalence with sequence diagram | Convert a scenario without losing ordering or participant links. | Convert one sequence to communication form. | Compare two representations of one scenario. |
| M6.5 Activity diagrams | initial/final, action/control flow, decision/merge, guards, fork/join, swimlane, object flow | Model an end-to-end workflow with complete decision guards and responsibility partitions. | Create an activity model for a high-value use case. | Fix unmatched fork/join and incomplete guard cases. |
| M6.6 State machines and final consistency | state/event/guard/action; when a state-machine helps; use case ↔ class ↔ sequence ↔ ERD ↔ deployment consistency | Test models for contradictions and decide whether an object lifecycle needs a state model. | Complete a formal cross-model validation checklist. | Trace a missing/contradictory name through the artifact set. |

**Common misconceptions:** node is not the same as artifact; sequence order is not object ownership; a message must map to an operation/defined responsibility; an activity diagram models workflow, while a state machine models one object’s life; component boundaries do not erase deployment needs.
**Module artefacts:** Layered Architecture, Deployment Diagram, Sequence Diagram, Communication Diagram, Activity Diagram, optional State Machine, Cross-Model Validation Record.
**Mastery criterion:** defend an architectural/deployment choice against a stated constraint and show traceability from a use-case step to a message, operation, class, component, and node where applicable.

---

### M7 — Revision, exam practice, and capstone integration

**Timing:** Weeks 12–13
**Prerequisites:** M1–M6 artefacts; no unresolved model-critical contradiction
**Source basis:** C1 pp. 38–41; all prior modules
**Entry concepts:** integrated model set and source labelling.

| Lesson | Topics and subtopics | Learning objectives | Practice / Capstone activity | Formative / summative evidence |
|---|---|---|---|---|
| M7.1 Concept bridge | analysis/design; incremental/iterative; DFD/flowchart; ERD/class; include/extend; aggregation/composition; sequence/communication; activity/state; association/dependency | Compare near-neighbour concepts precisely. | Complete a “why this model?” concept map. | Mixed discrimination questions with explanations. |
| M7.2 Mid-course repair | Weeks 1–5 terminology, calculation working, DFD/ERD quality | Diagnose and repair foundational errors before final UML integration. | Review a flawed mini-case solution. | Untimed mid-semester simulation. |
| M7.3 UML model clinic | use-case/class/component/deployment/behavioural quality and traceability | Critique models using a transparent checklist. | Peer/self review an integrated case package. | Error tagging and repair rationale. |
| M7.4 Final case strategy | unpacking a case, identifying actors/goals/data/classes/constraints, allocating time, stating assumptions | Plan a defensible solution under exam constraints. | Work through the course car-wash case or approved alternative. | Timed/untimed case planning exercise. |
| M7.5 Final SAD package | executive summary, model sequence, consistency, presentation | Assemble and communicate an evidence-based design package. | Finalise the Case Studio portfolio and presentation outline. | Capstone rubric preview; learner reflection on unresolved assumptions. |

**Module artefact:** Integrated SAD Package and Final Case-Study Plan.
**Mastery criterion:** create or critique a coherent mini-case answer that maintains consistent names/relationships across requirements, diagrams, calculations, and design rationale.

---

## 5. Week-to-module traceability

| Week | Primary module / lesson focus | Required learner artefact | Direct primary source |
|---:|---|---|---|
| 1 | M1 | system description/IPO/constraints/roles | C1 pp. 2–5; L1 |
| 2 | M2.1–M2.3 | SDLC plan and system request | C1 pp. 6–7; L2 |
| 3A | M2.4–M2.5 | methodology comparison/rationale | C1 pp. 8–9; L3 |
| 3B | M2.4–M2.6 | iteration/release view | C1 pp. 10–11; L2 |
| 4 | M3 | feasibility, WBS/schedule, risk register | C1 pp. 12–15; L4 |
| 5 | M4 | SRS, DFDs, ERD | C1 pp. 16–19 |
| 6 | M4.7 / M7.2 | mid-semester repair record | C1 p. 20 |
| 7 | M5.1–M5.2 | candidate classes/UML modelling plan | C1 pp. 21–23; L5 |
| 8 | M5.3–M5.5 | use-case model/descriptions | C1 pp. 24–26; L5 |
| 9 | M5.6–M5.8 | CRC/class/component models | C1 pp. 27–30 |
| 10 | M6.1–M6.2 | layers/deployment model | C1 pp. 31–33 |
| 11 | M6.3–M6.6 | sequence/communication/activity/consistency | C1 pp. 34–37 |
| 12 | M7.1–M7.3 | revision concept map/model-clinic record | C1 pp. 38–39 |
| 13 | M7.4–M7.5 | final SAD package / case plan | C1 pp. 40–41 |

---

## 6. Assessment architecture (blueprint only; no bank authored yet)

### 6.1 Design principles

1. **Progress requires demonstrated understanding.** A click-through state does not equal completion.
2. **Questions must be non-repetitive.** The future 100+ MCQ bank cannot be created by paraphrasing the same definition.
3. **Every question needs provenance and feedback.** Record source topic, cognitive level, answer rationale, misconception addressed, and whether it is lecturer-based or supplementary.
4. **Model work needs process feedback.** Diagram and calculation items should assess rationale and validation, not only final labels.
5. **No false official answer key.** New answers are author-reviewed explanations, not lecturer-approved keys.

### 6.2 Question blueprint for later Phase 6 production

| Domain | Recall / identify | Explain / compare | Apply / construct | Analyse / evaluate | Planned minimum question capacity |
|---|---:|---:|---:|---:|---:|
| Systems and SAD | 4 | 4 | 4 | 3 | 15 |
| SDLC and methodology | 5 | 6 | 6 | 5 | 22 |
| Planning, feasibility and risk | 5 | 5 | 9 | 8 | 27 |
| Requirements, DFD and ERD | 6 | 7 | 12 | 10 | 35 |
| OO and UML functional/structural | 7 | 8 | 14 | 11 | 40 |
| Architecture and behavioural UML | 6 | 6 | 12 | 10 | 34 |
| Integrated revision / cases | 3 | 4 | 8 | 10 | 25 |
| **Potential total, after review** | **36** | **40** | **65** | **57** | **198** |

This capacity is intentionally larger than the required 100 MCQs so the eventual bank can select high-quality, balanced items rather than force weak questions into the product.

### 6.3 Assessment forms by point in the pathway

| Assessment | Purpose | Required response format | Feedback policy |
|---|---|---|---|
| Lesson knowledge check | identify one misconception immediately | 3–6 MCQ/matching/short classification items | Explain the correct reasoning; name the relevant concept and source label. |
| Model Lab | diagnose structural error | select, repair, and justify a diagram/calculation element | Explain the violated rule and show a corrected state. |
| Module checkpoint | decide readiness for next dependency | mixed recall, application, mini-scenario | Keep attempts and topic-level outcomes; recommend review, not a false pass. |
| Case Studio review | preserve artifact coherence | artifact checklist, self-explanation, guided validation | Flag assumptions and missing evidence rather than invent data. |
| Mid-semester practice | Weeks 1–5 preparation | short-answer, calculation working, diagram prompt | Provide model reasoning/marking guidance authored for the app, labelled non-official. |
| Final practice | integrated case and diagram synthesis | timed/untimed multi-part case | Reveal model answer/mark guide only on learner choice; label as author-created unless an official rubric is later supplied. |

### 6.4 Subjective-question blueprint

At least 20 later subjective questions will be distributed across: methodology justification (3), feasibility/economic/schedule/risk analysis (4), requirements/SRS (3), DFD/ERD construction and critique (4), use-case/class/component work (3), architecture/deployment (1), sequence/communication/activity/state work (2), and integrated final case study (2+). Each must include an answer framework, a mark allocation, common-error notes, and a hidden/reveal-on-demand model guide.

---

## 7. Resource assignment plan

Verified resources from Phase 1 are optional reinforcement and never replace lecturer material. The future resource library will show its checked status, access condition, topic, and a specific “watch/read for” prompt.

| Curriculum point | Resource | Learner task | Access / integrity note |
|---|---|---|---|
| M2 SDLC | NISTIR 7499 | Compare its extended SDLC stages/templates with the course’s four high-level phases; do not treat the labels as identical. | Verified open PDF. |
| M2 Spiral | Boehm IEEE record | Read the verified abstract/metadata; identify why Spiral is described as risk-driven. | Full text access may require purchase/sign-in. |
| M3 Risk | CMU SEI *Continuous Risk Management Guidebook* | Compare the course risk-register cycle with continuous risk practice. | Verified CMU page; PDF linked. |
| M4 Requirements | IEEE/ISO/IEC 29148 record | Use as a standards context for requirement quality/processes, not as a required purchase. | Verified official record; full standard is access-dependent. |
| M4 DFD | Blancaflor Arada, Data and Process Modeling | Watch for levelling/balancing and DFD errors; cross-check against C1 rules. | Verified public video; not claimed as university content. |
| M4 Requirements | Blancaflor Arada, Requirements Modeling | Watch for elicitation/JAD context, then apply C1’s SRS scope. | Verified public video; not claimed as university content. |
| M5 OO | Blancaflor Arada, Object Modeling | Rehearse class/object/attribute/method/message vocabulary. | Verified public video; not claimed as university content. |
| M5–M6 UML | OMG UML 2.5 specification | Consult only when checking notation/terminology in an accuracy note. | Verified official specification; technical, not entry-level reading. |
| M5–M6 Architecture | Kruchten 4+1 article | Relate the course use-case/logical/process/component/deployment views to stakeholder concerns. | Verified open preprint. |
| M6 Activity | New Ur Academy activity/swimlane lecture | Reinforce activity/swimlane notation after guided course lesson. | Verified public video; not claimed as university content. |
| M1/M6 legal constraint | Ghana Data Protection Act, 2012 (Act 843) | Identify why personal-data handling can be a constraint in a scenario; do not provide legal advice. | Verified accessible legislative text. |

---

## 8. Prerequisite and mastery map

| Learner wants to… | Must first demonstrate | Suggested remediation if not ready |
|---|---|---|
| Choose a methodology | system problem, stakeholder need, constraints, SDLC deliverables | M1.2–M1.4 and M2.1 |
| Compute feasibility/schedule/risk | business need, scope assumption, cost/benefit and dependency reading | M3.1–M3.4; calculator/walkthrough mode |
| Write an SRS | scope, stakeholder/user need, functional vs non-functional distinction | M4.1–M4.2 |
| Draw DFD/ERD | system boundary, requirement nouns/actions, data/process distinction | M4.4–M4.6 |
| Draw use cases | requirement IDs, actors, system boundary, goal naming | M4.3 and M5.3–M5.4 |
| Draw class/component models | use-case descriptions, entity/relationship concepts, OO vocabulary | M5.1 and M5.6 |
| Draw sequence/activity models | selected use-case scenario, class responsibilities/operations | M5.5–M5.7 and M6.3–M6.5 |
| Attempt final case | all previous artefacts and validation checklist | M7.1–M7.3 |

**Proposed readiness thresholds for later implementation:**

- “Ready to continue” after **80% or more** on a short concept checkpoint *and* completion of the required artifact validation points.
- “Review recommended” at **60–79%**; surface specific weak concepts/diagram rules.
- “Rebuild foundation” below **60%**; route to the prerequisite lesson with a smaller practice set.

These are product-learning thresholds, not official course grades.

---

## 9. Content architecture and traceability rules

### 9.1 Required metadata for every future content object

Every lesson, quiz item, diagram, resource, formula, case prompt, or model answer must track:

- module / week / outcome / prerequisite;
- source label: **Lecturer material**, **Supplementary academic explanation**, **Standards/legal context**, **Applied example**, or **Accuracy note**;
- exact primary source locator where relevant (e.g., `C1 p. 18, DFD rules`);
- cognitive level and misconception targeted;
- accessibility text alternative for diagrams;
- whether a resource link was verified and on what date;
- assessment review status.

### 9.2 Naming consistency rules

1. A case system has one stable name and explicit boundary.
2. A named requirement receives a unique ID (`FR-01`, `NFR-01`, etc.).
3. External entities/actors, data stores/entities, classes, components, and nodes use distinguishable but related names.
4. Every use case traces to one or more requirements; every important scenario has supporting classes/messages; every received message maps to an operation/responsibility.
5. A DFD data flow is a noun/data item; a process is a verb phrase; a use case/activity is a goal/action phrase; a class is generally a singular noun.
6. An app-generated model answer must declare assumptions rather than smuggling invented domain facts into a solution.

### 9.3 Offline-first content requirement

The later standalone HTML must include the full lesson text, diagrams, question data, worked examples, explanations, and progress logic locally. External links are optional enrichment only and must fail gracefully without breaking the lesson or assessment flow.

---

## 10. Phase 2 completion review

### Completed in this phase

- Approved course code, source authority, scope, and answer-key policy recorded.
- Full course-level outcomes and learning progression established.
- Eight-module / Week 1–13 curriculum mapped to topics, subtopics, prerequisites, activities, artefacts, mastery checks, common misconceptions, and direct sources.
- Persistent case-system strategy and cross-model artifact spine designed.
- Question/subjective assessment blueprint and non-official-feedback policy set.
- Supplementary resources mapped only where they were verified in Phase 1.
- Content metadata, naming, traceability, and offline-first requirements established.

### Outstanding / deliberately deferred

- No lesson prose, worked diagrams, question bank, simulations, or learner interface has been implemented.
- No design language, wireframes, colours, typography, or representative screens have been selected; those are Phase 3 work.
- No official marking scheme exists; later model answers require author review and explicit non-official labelling.
- No future content should be built until the visual identity and representative product experience are approved in Phase 3.

## 11. Phase 3 approval gate

Review this curriculum architecture and approve or request changes before Phase 3 begins. Phase 3 will produce only the visual identity, responsive layout rules, navigation approach, dashboard, and a small set of representative screens — it will not expand the full course or build the final app in one pass.
