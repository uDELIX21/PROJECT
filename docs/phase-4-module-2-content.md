# Phase 4 — Module 2 Content: SDLC, Methodology Selection, and the Unified Process

**Course:** INFT 255 — System Analysis & Design
**Module position:** Weeks 2–3; follows Module 1 systems thinking
**Status:** Content complete for review. Module 2 simulations, assessment engine states, and durable progress are not yet implemented.

---

## 1. Source boundaries and module outcome

| Label | Source | Permitted use in this module |
|---|---|---|
| Lecturer material | C1 pp. 6–11; L2 pp. 2–37; L3 pp. 2–45 | SDLC phases/deliverables, methodology explanations, Unified Process, roles, supplied examples. |
| Supplementary academic explanation | NISTIR 7499; Boehm IEEE abstract/metadata | Clarify that lifecycle labels are frameworks and that Spiral is risk-driven. Do not quote inaccessible full texts. |
| Applied example | Original but source-consistent course-registration, hostel-booking, clinic, and mobile-app situations | Practise selection criteria without fabricating empirical claims. |
| Accuracy note | Phase 1 source-integrity report | Avoid presenting waterfall/RAD as a universal or literal one-way process. |

### Module outcome

Learners will be able to place activities and deliverables in the four SDLC phases, distinguish a lifecycle framework from a development methodology, compare plan-driven and iterative approaches, choose and justify a method against stated constraints, and explain the Unified Process as iterative/incremental work whose workflows vary in intensity over time.

### Prerequisite evidence

- Module 1 system purpose, boundary, constraints, and roles.
- A stated business problem and at least three constraints for the Case Studio system.

### Module 2 artefacts

1. SDLC activity/deliverable map.
2. Half-page system request.
3. Methodology selection matrix and written recommendation.
4. Iteration/release view or phase plan.

---

## 2. Lesson M2.1 — The SDLC is gradual refinement

**Estimated study time:** 22 minutes
**Primary source:** Lecturer material — C1 pp. 6–7; L2 pp. 4–11
**Key terms:** SDLC, phase, step, technique, deliverable, gradual refinement, maintenance.

A systems development life cycle (SDLC) is a structured way to understand a business need, decide whether and how to address it, build/deliver a solution, and support it over time. The supplied course uses four high-level phases:

| Phase | Central question | Main activities | Main deliverable |
|---|---|---|---|
| Planning | Why should we build it, and how will the work be organised? | system request, feasibility, project management | request, feasibility analysis, project plan |
| Analysis | What should the system do, for whom, where, and when? | strategy, requirements gathering, proposal | system proposal / requirements models |
| Design | How will the solution operate? | design strategy, architecture, interfaces, data/program design | system specification |
| Implementation | Build, test, install, and support it. | construction, testing, conversion, training, support | operational system and support plan |

**Gradual refinement** means each phase makes the previous output more specific. A need such as “reduce registration delays” becomes a system request, then requirements/models, then a design specification, then an implemented and supported solution. A discovery may trigger a revisit, but that does not erase the value of structured deliverables.

### Worked trace — hostel booking

- **Planning:** hostel manager identifies double booking and lost revenue; sponsor submits request and feasibility is checked.
- **Analysis:** students and staff are interviewed; current front-desk process and booking rules are studied.
- **Design:** team chooses a solution approach, defines Room/Student/Booking behaviour/data, interface flow, and hosting needs.
- **Implementation:** application is built/tested, introduced alongside the old method where appropriate, staff are trained, and support procedures begin.

### Misconceptions

- **“The SDLC is a programming method.”** It is an overall lifecycle framework. A methodology states a more specific way to organise the work.
- **“Implementation begins only after all learning ends.”** It includes construction/testing/install/training/support; a later revision can generate a new planning cycle.
- **“A phase produces one document only.”** Each phase may produce several connected artefacts, but its named deliverable expresses the main decision/evidence point.

### Visual specification for later implementation

A four-stage refinement rail: Business need → System request/feasibility → Proposal/models → Specification → Working system/support. Each arrow exposes the question answered and one example deliverable; an accessible linear version lists the same sequence.

---

## 3. Lesson M2.2 — Planning and analysis protect the problem definition

**Estimated study time:** 24 minutes
**Primary source:** Lecturer material — C1 pp. 6–7; L2 pp. 6–7
**Key terms:** system request, sponsor, feasibility, as-is, to-be, requirements gathering, system proposal.

### Planning

A system request expresses a business opportunity/problem before the team assumes a solution. It should include:

| Element | Question it answers |
|---|---|
| Sponsor | Who champions, authorises, or funds the work? |
| Business need | What problem or opportunity exists? |
| Business requirements | At a high level, what outcome/capability is needed? |
| Business value | What tangible or intangible improvement is expected? |
| Special issues | What deadline, policy, risk, regulation, or constraint matters early? |

Planning asks whether the work is feasible and how it will be managed. It does not yet claim to know every user story or database detail.

### Analysis

Analysis studies the **as-is** situation and defines a credible **to-be** need. Gathering methods in the supplied material include interviews, observation, questionnaires, document analysis, and JAD. The course later develops these in depth; here the important point is that a proposal must be evidence-based rather than a list of preferred features.

A system proposal normally joins requirements, a system concept, and models. The sponsor/committee can use it as a go/no-go decision point.

### Applied repair activity

Weak request: “Build an app for hostel booking immediately.”

Improved request: “The hostel manager reports duplicate reservations and delayed confirmation during peak periods. The project seeks a reliable booking process that lets students request rooms, lets staff review availability, and produces an auditable booking record before the next allocation period. Constraints include a fixed allocation deadline and mixed mobile connectivity.”

The improved request describes a need/value/constraint. It still does not decide the programming language or cloud provider.

---

## 4. Lesson M2.3 — Design and implementation make requirements operational

**Estimated study time:** 20 minutes
**Primary source:** Lecturer material — C1 pp. 6–7; L2 pp. 8–10
**Key terms:** build/buy/outsource, architecture, interface, specification, construction, installation, conversion, training, support.

During design, the team decides how the solution will meet the approved requirements and constraints:

1. **Design strategy:** build internally, buy packaged software, or outsource/partner.
2. **Architecture and interface:** hardware/software/network organisation and user interaction/reporting approach.
3. **Database/file specification:** what must be stored and how data structures support work.
4. **Program/class design:** components/classes/programs and their responsibilities.

The combined technical design is the **system specification**. It should be traceable to analysis, not a new unapproved feature list.

Implementation then constructs/tests the solution, installs it, trains users, and establishes a support plan. Installation can include conversion from old to new process; a parallel run is one possible conversion strategy, not a rule for every project.

### Examination distinction

| Prompt | Best phase | Why |
|---|---|---|
| Interview clerks about current rework | Analysis | Identifies current needs/process problems. |
| Decide whether to build or buy | Design | Selects a solution strategy. |
| Plan user training during rollout | Implementation | Supports adoption/install. |
| Assess whether the project can be afforded | Planning | Economic feasibility informs go/no-go. |

---

## 5. Lesson M2.4 — Choose a method by conditions, not fashion

**Estimated study time:** 30 minutes
**Primary source:** Lecturer material — C1 pp. 8–11; L2 pp. 13–22; L3 pp. 3–32
**Key terms:** methodology, waterfall, parallel, phased/incremental, iterative, prototype, RAD, Agile, Big-Bang.

A **methodology** is a formalised approach for carrying out lifecycle work. It changes the order, overlap, repetition, user involvement, risk treatment, and deliverables — not the basic need to understand, design, build, test, and support a system.

| Method | Useful conditions | Strength | Main risk/limitation |
|---|---|---|---|
| Waterfall | stable, well-understood requirements; documentation/milestones valued | clear phase control and review points | late discovery is expensive; working software appears late |
| Parallel development | a design can be divided into relatively independent subprojects | shorter overall schedule through concurrent work | integration/dependency management becomes difficult |
| Phased / incremental development | essential capabilities can be released first | early usable delivery; later increments add functionality | needs a sound overall architecture and careful integration |
| Iterative development | the whole solution benefits from repeated refinement | feedback and risks appear earlier | can drift without scope/review discipline |
| System/evolutionary prototype | users need to react to a working model that may evolve | clarifies expectations through feedback | users may mistake a prototype for a finished system |
| Throwaway prototype | uncertainty must be explored without carrying early code into production | reduces requirement misunderstanding | time spent on prototype is intentionally not production implementation |
| RAD | small skilled team, available users, modular scope, short timebox | rapid feedback/delivery using workshops/prototypes/components | user expectations/scope can grow; poor fit for high-risk very large work |
| Agile / XP | change is expected and feedback is frequent | iterative/incremental working software and collaboration | still requires discipline, priorities, and stakeholder availability |
| Big-Bang | very small, low-consequence, one-person academic experiment only | low process overhead | high rework/coordination risk; not a default recommendation |

> **Accuracy note:** The supplied waterfall diagrams are useful plan-driven representations. Do not infer that real projects can never revisit earlier decisions. Similarly, “RAD” covers practices that use rapid feedback and construction; learners should not reduce it to “coding quickly without analysis.”

### Method-selection mini case

A Sunyani start-up needs a simple booking service in eight weeks. Users expect changes after seeing early versions; the feature set can be split into booking, payment, and notification releases; the team can meet users weekly.

A defensible recommendation is incremental/iterative or Agile with prototypes. The reason is not that a label is fashionable; it is that requirements are expected to change, feedback is available, and phased value is possible. A strict waterfall plan would be a weaker default because it delays visible feedback.

---

## 6. Lesson M2.5 — Spiral and V-Model make risk and verification visible

**Estimated study time:** 25 minutes
**Primary source:** Lecturer material — C1 pp. 8–9; L3 pp. 25–45; Boehm IEEE abstract/metadata
**Key terms:** Spiral, objectives, alternatives, constraints, risk resolution, verification, validation, acceptance testing.

### Spiral Model

The Spiral model is risk-driven and repeats four concerns in each loop:

1. Determine objectives, alternatives, and constraints.
2. Identify/evaluate risks and resolve important uncertainty (for example through a prototype, simulation, benchmark, or analysis).
3. Develop and verify the next level of the product.
4. Review and plan the next loop.

The choice inside a loop depends on the risk. A prototype may be used to resolve user-interface uncertainty; a benchmark may resolve performance uncertainty. Spiral is therefore suited to large/complex/high-risk work only when the team has enough risk-analysis capability and resources.

### V-Model

The V-Model places planned test activity alongside corresponding development decisions:

| Development / verification side | Matching validation / test side |
|---|---|
| business/user requirements | acceptance testing |
| system requirements/design | system testing |
| high-level architecture design | integration testing |
| detailed/module design | unit testing |
| coding | bottom of the V |

**Verification** examines whether development work/products conform to specified requirements/design through review or static analysis. **Validation** uses executed system behaviour/testing to check whether the solution meets expected needs. They are related but not identical.

### Common error

“Testing happens after coding, so the V-Model is the same as waterfall.” The V-Model is sequential/plan-driven, but its distinguishing teaching point is that test planning and traceability are considered alongside the corresponding development stage rather than only at the end.

---

## 7. Lesson M2.6 — The Unified Process connects iterations and workflows

**Estimated study time:** 20 minutes
**Primary source:** Lecturer material — C1 pp. 21–23; L2 pp. 23–28
**Key terms:** Unified Process, inception, elaboration, construction, transition, engineering workflow, supporting workflow, architecture-centric, use-case-driven.

The Unified Process (UP) is an object-oriented approach that specifies when/how UML techniques may be used. It is:

- **Iterative and incremental:** the system grows and is refined over repeated work cycles.
- **Use-case-driven:** user goals help drive analysis/design/testing priorities.
- **Architecture-centric:** early work reduces structural/technical risk, not only feature uncertainty.

| UP phase | Main emphasis | Typical question |
|---|---|---|
| Inception | scope, business case, major risks | Is this project worth pursuing and what is its initial direction? |
| Elaboration | core requirements and architecture/risk reduction | Can a credible architecture/supporting plan address the main risks? |
| Construction | build and test increments | Can we complete reliable functionality in managed iterations? |
| Transition | deliver/deploy to users | Can users adopt and operate the solution successfully? |

Workflows such as business modelling, requirements, analysis, design, implementation, testing, and deployment occur through the lifecycle at varying intensity. Supporting workflows include project management, configuration/change management, and environment. Therefore, UP is not a diagram with one workflow active at a time.

### Comparison: SDLC versus UP

The course’s four-phase SDLC expresses broad lifecycle questions/deliverables. UP describes an iterative process whose phases and workflows organise object-oriented work. They can be related, but a learner should not force “Inception = Planning only” or “Construction = Implementation only” as a perfect one-to-one mapping.

---

## 8. Case Studio — methodology selection report scaffold

### Brief

For the selected course project, recommend one methodology from the covered methods. The recommendation must compare at least four candidates against:

- requirement stability;
- user availability;
- project/team size;
- deadline;
- technology familiarity;
- business/technical risk;
- safety/quality consequences where relevant.

### Matrix template

| Criterion | Weight / importance | Waterfall | Incremental / iterative | Prototype / RAD | Spiral / V-Model | Evidence / rationale |
|---|---:|---:|---:|---:|---:|---|
| Requirement uncertainty |  |  |  |  |  |  |
| User availability |  |  |  |  |  |  |
| Deadline |  |  |  |  |  |  |
| Risk / criticality |  |  |  |  |  |  |
| Team/technology fit |  |  |  |  |  |  |

### Self-check

- Does the recommendation state the actual case conditions, not only generic advantages?
- Does it reject at least one plausible alternative with a reason?
- Does it distinguish the high-level SDLC from the specific method?
- Does it show what will be delivered in the first release/iteration where relevant?

---

## 9. Future Module 2 learning interactions

| Interaction | Meaningful learner task | Feedback rule |
|---|---|---|
| SDLC deliverable route | place activities/deliverables in Planning, Analysis, Design, or Implementation | explain the key question and output of the correct phase |
| Method-selection matrix simulation | adjust requirement certainty, deadline, user availability, technical risk, and safety need; compare method fit | show trade-offs, not a falsely deterministic “best methodology” |
| Waterfall/parallel/phased visual sequence | inspect what can overlap and what integration risk remains | identify why parallel work requires integration discipline |
| Prototype lifecycle decision | decide whether a mock-up is throwaway or evolutionary from a scenario | explain user expectation and production-quality risk |
| Spiral risk-loop planner | choose objective, risk, risk-resolution activity, and next-loop plan | require a specific uncertainty/resolution link |
| V-model traceability matcher | pair a development decision with planned test level | distinguish verification and validation clearly |
| UP workflow intensity visual | compare iteration points and workflows | explain that workflows overlap with differing intensity |

---

## 10. Formative assessment seed — 18 MCQs

These drafts are source-mapped, non-repetitive Module 2 items for later Phase 6 review. They have explanations but are not yet loaded into an assessment engine or presented as official lecturer answer keys.

| ID | Level | Prompt | Correct answer and reasoning | Source |
|---|---|---|---|---|
| M2-Q01 | Remember | Which SDLC phase asks why a system should be built? A Planning B Analysis C Design D Implementation | **A.** Planning includes initiation, feasibility, and project management. | C1 p. 6 |
| M2-Q02 | Understand | A system proposal primarily belongs to which phase? A Planning B Analysis C Design D Implementation | **B.** It combines requirements/concept/models for a continuation decision after analysis. | C1 p. 6 |
| M2-Q03 | Apply | “Choose whether to buy a package or build in-house” is chiefly a: A planning feasibility calculation B analysis elicitation technique C design strategy decision D installation activity | **C.** It decides how the approved need will be addressed. | C1 p. 6 |
| M2-Q04 | Understand | Why is the SDLC called gradual refinement? A Every phase uses identical data. B Each phase makes previous outputs more detailed for the next decision. C Coding begins before planning. D No deliverables are produced. | **B.** Outputs become progressively more specific and inform later work. | C1 pp. 6–7 |
| M2-Q05 | Apply | Which item is most appropriate in a system request? A complete database schema B sponsor, business need, value, and special issues C final unit-test log D deployment-node diagram | **B.** Those request elements justify/define the initial work; later detail belongs elsewhere. | C1 p. 12 |
| M2-Q06 | Analyse | A team writes “use a React interface” before interviewing users. What is the strongest concern? A It has completed implementation. B It may have selected a solution before understanding requirements. C It has chosen the V-Model. D It has created feedback. | **B.** This is premature design, not evidence of analysed need. | C1 pp. 6–7 |
| M2-Q07 | Remember | Which model delivers usable functionality in pieces, with later releases adding features? A Waterfall B Incremental/phased C V-Model D Big-Bang | **B.** Each increment adds usable capability. | C1 p. 10; L2 pp. 17–18 |
| M2-Q08 | Understand | What most distinguishes iterative from incremental development? A Iterative refines the whole repeatedly; incremental adds new parts/releases. B Iterative has no testing. C Incremental never plans. D They are always identical. | **A.** They may be combined, but the emphasis differs. | C1 pp. 10–11 |
| M2-Q09 | Apply | A mock-up is built to clarify unclear requirements and will be discarded before production. It is a: A phased release B throwaway prototype C deployment artifact D V-Model test | **B.** Its purpose is learning/clarification, not production evolution. | C1 p. 10; L2 p. 19 |
| M2-Q10 | Analyse | A high-risk national tax platform has evolving needs and dedicated risk expertise. Which model is most defensible? A Big-Bang B Spiral C basic Waterfall D one-pass prototype only | **B.** Spiral explicitly structures repeated risk identification/resolution. | C1 pp. 8–9 |
| M2-Q11 | Understand | In the V-Model, detailed/module design is most directly paired with: A acceptance testing B system testing C integration testing D unit testing | **D.** Unit-test planning/testing corresponds to detailed module design. | C1 p. 9; L3 p. 42 |
| M2-Q12 | Analyse | A student says validation means reviewing a requirements document without running anything. Best correction? A Correct; validation is static only. B That describes verification; validation evaluates executed behaviour against expected needs. C Both terms mean coding. D Neither is relevant to testing. | **B.** The module distinguishes review/static verification from execution-based validation. | L3 pp. 35–36 |
| M2-Q13 | Apply | A small skilled team has available users, modular scope, and a fixed 60–90-day deadline. Which is a plausible fit? A RAD B V-Model only C Big-Bang D no methodology | **A.** These conditions support rapid workshops/prototypes/timeboxing, while scope must remain controlled. | C1 p. 8; L3 pp. 17–24 |
| M2-Q14 | Evaluate | Why is “Agile is best because it is modern” not an adequate recommendation? A Agile cannot use feedback. B Method selection must relate to requirement change, users, risk, schedule, and team conditions. C Waterfall is illegal. D Methods do not affect delivery. | **B.** A method is justified by context/trade-offs, not popularity. | C1 pp. 8–11 |
| M2-Q15 | Remember | Which UP phase focuses on initial scope, business case, and major risks? A Inception B Elaboration C Construction D Transition | **A.** Inception establishes initial direction and feasibility/business case. | C1 p. 22; L2 p. 26 |
| M2-Q16 | Understand | In the Unified Process, why can requirements and testing both appear across more than one phase? A They are forbidden in Construction. B Workflows occur throughout the lifecycle but vary in intensity. C UP has no phases. D Testing replaces design. | **B.** The UP is two-dimensional: phases plus overlapping workflows. | C1 p. 22; L2 pp. 24–28 |
| M2-Q17 | Apply | A project wants early payment confirmation feedback but must deliver results reporting later. What release view best demonstrates incremental thinking? A deliver all features at final handover B release registration/payment first, then reporting in a later usable increment C skip analysis D perform acceptance testing first | **B.** It stages usable capability while retaining later scope. | C1 p. 10 |
| M2-Q18 | Evaluate | A safety-critical control system has stable requirements and requires planned traceability from requirements through testing. Which approach is strongest? A V-Model B Big-Bang C uncontrolled prototype D no test plan | **A.** V-Model explicitly pairs development stages and test planning; stable/safety-critical conditions support it. | C1 p. 9; L3 pp. 33–45 |

**Cognitive coverage:** remembering 3; understanding 5; applying 5; analysing 3; evaluating 2. Several items use multiple cognitive operations; later course-wide review will rebalance categorisation and eliminate any redundancy.

---

## 11. Subjective / examination-practice seed — four questions

### M2-S01 — Phase and deliverable reasoning (8 marks)

**Prompt:** For a campus hostel system, classify the following into an SDLC phase and state the expected deliverable: feasibility study; interview students; choose build/buy/outsource; train front-desk staff. Explain why a request does not need a final database schema.

<details><summary>Reveal model answer and marking guide</summary>

- Feasibility study: Planning; feasibility analysis/request evidence.
- Interview students: Analysis; requirements evidence/model/proposal input.
- Build/buy/outsource: Design; design strategy/system specification.
- Train front-desk staff: Implementation; training/support/installation plan.
- A request states need/value/scope/special issues early; complete database schema is design detail produced after requirements are understood.

**Marks:** 1 mark for each phase (4), 0.5 mark each suitable deliverable (2), 2 marks for request-versus-schema reasoning.
</details>

### M2-S02 — Methodology recommendation (10 marks)

**Prompt:** A clinic wants an appointment service within two months. Receptionists can meet the team weekly; initial requirements are unclear; the booking, reminder, and report features can be released separately. Recommend a methodology and reject one weaker alternative.

<details><summary>Reveal model answer and marking guide</summary>

A strong answer recommends incremental/iterative development or Agile supported by early prototypes. The uncertain requirements and regular feedback support iteration/prototyping; separable features support increments; two-month deadline calls for prioritised scope/timeboxing. A strict waterfall approach is weaker as the default because it expects stable requirements and delays feedback. Credit alternative recommendations if criteria and limitations are reasoned.

**Marks:** justified method choice (4); use of at least three stated conditions (3); meaningful rejection/limitation of another method (2); clear conclusion (1).
</details>

### M2-S03 — Spiral and V-Model comparison (8 marks)

**Prompt:** Compare Spiral and V-Model in purpose, risk/testing emphasis, suitable project conditions, and one limitation of each.

<details><summary>Reveal model answer and marking guide</summary>

Spiral is iterative and risk-driven: each loop identifies objectives/alternatives/constraints, resolves important risks, develops/verifies, then plans. It fits large/evolving/high-risk work but needs expertise/resources and can make milestones difficult. V-Model is plan-driven and links each development stage to a matching test level; it fits stable/safety-critical work with traceability needs but is rigid and gives limited early working feedback.

**Marks:** Spiral explanation (3); V-Model explanation (3); one suitable-condition comparison (1); one valid limitation each (1 total when both supplied).
</details>

### M2-S04 — Unified Process workflow interpretation (6 marks)

**Prompt:** Explain why it is misleading to draw the Unified Process as four non-overlapping boxes labelled Inception, Elaboration, Construction, and Transition with only one activity in each.

<details><summary>Reveal model answer and marking guide</summary>

UP has phases over time, but requirements, analysis, design, implementation, testing, deployment, project management, and change/configuration work occur across the lifecycle with different intensity. It is iterative/incremental, use-case-driven, and architecture-centric. A one-box-per-activity view hides overlap and feedback.

**Marks:** phase/workflow distinction (2); varied intensity/overlap (2); iterative/incremental or architecture/use-case explanation (1); clear conclusion about the misleading diagram (1).
</details>

---

## 12. Phase 4 Module 2 review

### Completed

- Six complete lessons covering SDLC, planning/analysis, design/implementation, methodology selection, Spiral/V-Model, and Unified Process.
- Lecturer-supported tables, case demonstrations, misconceptions, accuracy notes, and exam-writing distinctions.
- Methodology-selection Case Studio scaffold.
- Seven specific future simulations/interactions tied to the Module 2 syllabus.
- Eighteen MCQ drafts with explanations and four subjective prompts with revealable model guides.

### Limitations / deferrals

- No Module 2 interaction, lesson-completion state, assessment session, score, or model-guide reveal control has been implemented in the HTML file yet.
- Module 2’s 18 MCQs/four subjective prompts remain only a reviewed seed; they do not satisfy the course-wide 100/20 target or claim lecturer approval.
- The running total is 34 MCQ drafts and eight subjective prompts across Modules 1–2. It is a content-development count, not a functional bank count.
- The methodology simulator must expose trade-offs rather than promise a mathematically “correct” universal method.

## 13. Next approval gate

Review Module 2 for academic accuracy and scenario relevance. Once approved, the next progressive build will implement Module 2’s visual explanations/simulations and add its reviewed content into `inft255-learning-environment.html` before Module 3 content begins.
