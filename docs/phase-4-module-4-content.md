# Phase 4 — Module 4 Content: Requirements Engineering, DFD, and ERD

**Course:** INFT 255 — System Analysis & Design
**Module position:** Week 5 and Week 6 consolidation
**Status:** Content complete for review. Diagram builders, SRS persistence, and assessment-engine integration are deferred to Phase 5/later phases.

---

## 1. Source boundaries and module outcome

| Label | Source | Use |
|---|---|---|
| Lecturer material | C1 pp. 16–20 | requirement types/quality, gathering, analysis strategies, SRS, DFD/ERD notation/rules, mid-semester revision. |
| Supplementary standards context | IEEE/ISO/IEC 29148 verified record | supports lifecycle view of requirements quality; full standard is not claimed accessible. |
| Verified supplemental video | Blancaflor Arada, *Data and Process Modeling* (50:10) | optional DFD reinforcement; record is in Phase 1 library. |
| Applied example | course-registration and hostel-booking examples grounded in supplied notes | illustrate modelling choices without inventing stakeholder evidence. |

### Module outcome

Learners can distinguish requirement types, choose/critique elicitation techniques, write testable requirement statements, structure an SRS, construct and validate levelled DFDs, construct an ERD with keys/cardinality, resolve an M:N relationship, and explain how requirements/data/process models remain traceable.

### Required artefacts

1. SRS outline with numbered functional/non-functional requirements.
2. Requirements-gathering plan and explicit assumptions.
3. Context, Level-0, and one Level-1 DFD with balancing check.
4. ERD with five or more entities, keys, cardinalities, and associative entity where needed.
5. Requirement-to-model traceability seed.

---

## 2. Lesson M4.1 — Requirements describe needed outcomes and qualities

**Primary source:** C1 pp. 16–17
**Key terms:** business requirement, user requirement, functional requirement, non-functional requirement, testable, traceable.

A requirement states what a system must do or a characteristic it must have. The course distinguishes:

| Type | Question answered | Example |
|---|---|---|
| Business requirement | Why is this system needed? | Reduce registration time and avoid duplicate records. |
| User requirement | What must a user accomplish? | A student can register for courses online. |
| Functional requirement (FR) | What behaviour/information must the system provide? | The system shall check prerequisites before enrolling a student. |
| Non-functional requirement (NFR) | What quality/constraint must the system meet? | The system shall respond within three seconds for 95% of requests. |

A good requirement is clear, complete, consistent, testable, feasible, traceable, and necessary. Avoid words such as *fast*, *easy*, and *adequate* unless the required condition is measurable.

### Rewrite activity

Weak: “The booking system must be user-friendly and secure.”

Improved: “NFR-01: A first-time student shall be able to submit a booking request using the documented steps without staff assistance in the defined test scenario.” “NFR-02: Only authorised hostel staff shall access applicant allocation records.”

The revised statements still need agreed measurement/verification details, but they are more inspectable than vague adjectives.

---

## 3. Lesson M4.2 — Elicit and analyse before specifying

**Primary source:** C1 pp. 16–17
**Key terms:** interview, JAD, questionnaire, observation, document analysis, user story, root cause.

| Technique | Strength | Limitation / planning implication |
|---|---|---|
| Interview | rich detail and follow-up probing | time-consuming; prepare neutral questions and diverse participants |
| JAD | stakeholders can agree quickly | needs facilitation and scheduling; influential voices must not silence others |
| Questionnaire | reaches many people at low cost | response/follow-up can be weak; not enough for deep workflow discovery |
| Document analysis | reveals formal current procedure/records | documents may be outdated or differ from actual practice |
| Observation | reveals actual work, exceptions, workarounds | people may act differently when observed; explain purpose respectfully |

Requirements analysis asks why a problem occurs and whether each activity adds value. The supplied strategies include problem analysis, root-cause/five-whys, duration analysis, activity-based costing, benchmarking, outcome analysis, technology analysis, and activity elimination.

**User story format:** “As a [role], I want [goal] so that [value].” A story helps discuss needs but does not replace testable FR/NFR statements or models.

### Source-integrity rule

A Case Studio learner may use a simulated brief, but must label it as simulated. Do not claim “students said…” or invent interview results without actual evidence.

---

## 4. Lesson M4.3 — The SRS makes requirements reviewable

**Primary source:** C1 p. 17
**Key terms:** SRS, scope, assumptions, dependency, interface requirement, traceability matrix.

An SRS is a structured agreement/communication artifact. The course uses an outline based on IEEE 830 / ISO/IEC/IEEE 29148 traditions:

1. **Introduction:** purpose, scope, definitions, references.
2. **Overall description:** product perspective, user classes, operating environment, assumptions/dependencies.
3. **Specific requirements:** numbered FRs, NFRs, and external interface requirements.
4. **Appendices:** models, glossary, and traceability matrix.

Use stable IDs such as `FR-01` and `NFR-01`. The ID makes later traceability possible:

```text
FR-02 Check prerequisite
  → DFD process: Verify Student / Enrol in Courses
  → use case: Register for Courses
  → class operation: checkPrerequisite()
  → sequence message: checkPrerequisite(studentId)
```

The later arrows are future-course models; this module establishes the discipline of consistent requirement names and IDs.

---

## 5. Lesson M4.4 — DFDs model data movement, not program clicks

**Primary source:** C1 pp. 17–18
**Key terms:** external entity/source/sink, process, data store, data flow, context diagram, Level-0, Level-1, balancing.

A data flow diagram (DFD) shows how data enters, is transformed, is stored, and leaves a system. It is not a flowchart: it does **not** show program-control logic, click sequences, or every decision branch.

| Element | Naming rule | Registration example |
|---|---|---|
| External entity | noun | Student, Bank, Lecturer |
| Process | verb phrase | Verify Student; Enrol in Courses |
| Data store | noun | Student Records; Enrolment |
| Data flow | noun/data item | Registration request; clearance status |

### Levels

- **Context diagram:** entire system as one process with external entities and data flows.
- **Level-0 DFD:** three to seven major processes, stores, and flows.
- **Level-1/2:** decomposes one parent process into smaller numbered processes such as 3.1/3.2.

### Rules and common errors

1. Every process has at least one input and output. Input only/no output is a **black hole**; output/no input is a **miracle**.
2. Data does not flow directly between two external entities or directly between two data stores; a process must transform/read/write it.
3. Flows are nouns; processes are verb phrases.
4. Parent/child diagrams must **balance**: parent inputs/outputs remain represented in the decomposed child view.
5. Do not use DFDs to show control decisions; use an appropriate behavioural/process model later.

### Worked registration sequence

Context: Student sends registration request; Bank sends payment confirmation; system returns registration slip/class list/enrolment report to relevant actors.

Level-0: 1.0 Verify Student uses D1 Student Records; 2.0 Check Fee Clearance uses D2 Payments; 3.0 Enrol in Courses uses D3 Course Offerings/D4 Enrolment; 4.0 Produce Reports uses D4 Enrolment.

---

## 6. Lesson M4.5 — ERDs model data structure and relationships

**Primary source:** C1 pp. 18–19
**Key terms:** entity, attribute, primary key, foreign key, relationship, cardinality, participation, associative entity, composite key.

An ERD models the data the system needs to store, rather than the sequence of processing. An **entity** is a thing about which data is stored. An **attribute** describes it. A **primary key (PK)** uniquely identifies a record; a **foreign key (FK)** references a related entity’s PK.

| Entity | Example attributes |
|---|---|
| STUDENT | StudentID (PK), Name, Programme, Level |
| COURSE | CourseCode (PK), Title, CreditHours |
| LECTURER | StaffID (PK), Name, Department |
| ENROLLMENT | StudentID (FK), CourseCode (FK), Semester, Grade |

### Cardinality and M:N resolution

A student can take many courses and a course can include many students: this is M:N. Do not leave the M:N unexplained when the system must store facts about each enrolment. Add **ENROLLMENT** as an associative entity.

```text
STUDENT 1 ─── N ENROLLMENT N ─── 1 COURSE
```

`StudentID + CourseCode + Semester` can form the composite primary key in the supplied example. ENROLLMENT holds relationship-specific data such as Semester and Grade.

### ERD versus later class diagram

An ERD is data-centred: entities, attributes, keys, relationships. A class diagram later adds operations/behaviour and supports inheritance. They may use related nouns but are not interchangeable diagrams.

---

## 7. Lesson M4.6 — Validate the requirements package before UML work

**Primary source:** C1 pp. 19–20

Before building use cases/classes, run a basic consistency check:

- Does each important FR appear in a process/use case candidate?
- Are the same domain names used across SRS, DFD, and ERD?
- Are DFD data stores represented by data entities where appropriate?
- Does every Level-1 diagram preserve its parent’s input/output boundary flows?
- Are user stories treated as discussion starters rather than untested requirements?
- Does every M:N relationship requiring its own data use an associative entity?

This is the bridge to the mid-semester revision. It prevents learners from carrying inconsistent names into later UML models.

---

## 8. Case Studio — Requirements package scaffold

For the selected case, complete:

1. two gathering activities (real or explicitly simulated) and documented findings/assumptions;
2. 12 numbered functional requirements and six non-functional requirements, each testable;
3. context/Level-0/one Level-1 DFD with a balancing note;
4. ERD with five entities, PK/FK, cardinalities, and associative entity where needed;
5. traceability seed connecting selected FRs to DFD processes and ERD entities.

---

## 9. Future Module 4 model labs and simulations

| Interaction | Learner task | Feedback requirement |
|---|---|---|
| Requirement-quality editor | revise vague/duplicated/conflicting statements | show the missing measurable condition, ambiguity, or traceability issue |
| Gathering-technique planner | select technique/limitation for a stakeholder question | explain trade-off, not a universal best technique |
| SRS traceability builder | link requirement IDs to model elements | flag orphan FRs and unlinked model elements |
| DFD element builder | label entity/process/store/flow and enforce naming rule | identify process/data confusion |
| Context-to-Level-0 balancer | compare parent flows to child diagram | show missing/extra boundary flow clearly |
| DFD error clinic | repair black hole, miracle, direct store/entity flow | explain rule violation and correction |
| ERD cardinality/M:N resolver | assign PK/FK/cardinality and add associative entity | explain why relationship-specific data requires the association entity |
| Requirements package challenge | reconcile SRS, DFD, and ERD names | surface cross-model inconsistency rather than auto-fix without rationale |

---

## 10. Formative assessment seed — 18 MCQs

| ID | Level | Prompt | Correct answer and explanation | Source |
|---|---|---|---|---|
| M4-Q01 | Remember | A requirement stating “The system shall generate a transcript” is: A business B user C functional D non-functional | **C.** It specifies system behaviour/output. | C1 p. 16 |
| M4-Q02 | Understand | Why is “The system must be fast” weak? A It is an output. B It lacks measurable criteria for verification. C It is always a functional requirement. D It is a primary key. | **B.** Replace vague quality language with a measurable target/context. | C1 p. 16 |
| M4-Q03 | Apply | Which is the strongest NFR? A easy to use B secure C respond within 3 seconds for 95% of requests D use a blue button | **C.** It gives measurable performance condition. | C1 p. 16 |
| M4-Q04 | Understand | Which technique best reveals how clerks actually bypass a documented procedure? A observation B only questionnaire C only code review D deployment | **A.** Observation can reveal actual work, while its observer effect should be considered. | C1 p. 16 |
| M4-Q05 | Analyse | A document says bookings are approved in one day, but observation finds staff use paper notes and wait three days. Best response? A trust document only B record discrepancy and investigate current practice C call it a DFD output D delete observation | **B.** Documents may be outdated; analyse the difference. | C1 p. 16 |
| M4-Q06 | Remember | A well-structured SRS includes purpose/scope, overall description, specific requirements, and: A random screenshots B appendices/models/glossary/traceability C source code D only a Gantt chart | **B.** Models/glossary/traceability support review. | C1 p. 17 |
| M4-Q07 | Apply | Why give a requirement ID such as FR-02? A to make it longer B to support traceability/review/change discussion C to replace testing D to name a data store | **B.** Stable IDs link requirements to models/tests later. | C1 p. 17 |
| M4-Q08 | Understand | A DFD primarily shows: A screen layout B data movement/transformation/storage C class inheritance D test schedule | **B.** DFDs model what happens to data, not UI or program-control detail. | C1 p. 17 |
| M4-Q09 | Apply | Best DFD process label: A Student Records B payment confirmation C Check Fee Clearance D Click Submit | **C.** A process is a verb phrase; others are store/flow/interface action. | C1 pp. 17–18 |
| M4-Q10 | Analyse | A DFD process receives a registration request but produces no output. It is a: A data store B black hole C miracle D foreign key | **B.** A process with no output is invalid. | C1 p. 18 |
| M4-Q11 | Analyse | A Level-1 decomposition introduces an output to Bank that the parent Level-0 process did not show. Main problem: A inheritance B lack of balancing C missing PK D too many actors | **B.** Parent and child boundary flows must balance. | C1 p. 18 |
| M4-Q12 | Evaluate | A team draws a direct arrow from STUDENT RECORDS store to Student external entity. Best correction? A direct data is always valid B add a process that reads/transforms the record and sends named output C rename Student as a process D use a class diagram only | **B.** Direct store-to-entity flow violates the DFD rule. | C1 p. 18 |
| M4-Q13 | Remember | A PK is an attribute that: A stores any repeated note B uniquely identifies a record C is always an FK D describes a process | **B.** A primary key distinguishes each entity instance/record. | C1 p. 18 |
| M4-Q14 | Apply | CourseCode in ENROLLMENT referencing COURSE is a: A control B output C foreign key D use case | **C.** It refers to the related entity’s primary key. | C1 pp. 18–19 |
| M4-Q15 | Analyse | STUDENT and COURSE are M:N and grade/semester must be stored for each enrolment. Best ERD choice? A remove COURSE B add ENROLLMENT associative entity C use a DFD store only D duplicate student fields | **B.** ENROLLMENT resolves M:N and holds relationship-specific facts. | C1 p. 19 |
| M4-Q16 | Understand | How does an ERD differ from a class diagram? A ERD models stored data; class diagram adds operations/behaviour and inheritance. B ERD is a test plan. C class diagram has no attributes. D no difference. | **A.** They overlap in nouns but serve different modelling purposes. | C1 p. 19 |
| M4-Q17 | Apply | “As a student, I want to view available rooms so that I can choose a suitable option” is best described as a: A user story B NPV C deployment node D foreign key | **A.** It is user-story form; later work turns needs into testable requirements/models. | C1 p. 16 |
| M4-Q18 | Evaluate | An SRS has 20 FRs but no links to DFD/ERD/use cases. What is the main improvement? A remove IDs B create traceability links and investigate orphan models/requirements C add animation D change every FR to NFR | **B.** Traceability exposes missing or inconsistent model support. | C1 pp. 17–19 |

**Cognitive coverage:** remembering 3; understanding 4; applying 5; analysing 4; evaluating 2. Several prompts draw on more than one operation; Phase 6 review will finalise consistent course-wide labels and remove any redundancy.

---

## 11. Subjective examination-practice seed — four questions

### M4-S01 — Requirement quality (8 marks)

**Prompt:** Rewrite these statements as testable requirements and identify their type: “The hostel system must be easy to use”; “Students should get rooms quickly”; “Use a cloud database.” Explain why the final statement is not a requirement at the same level.

<details><summary>Reveal model answer and marking guide</summary>

Answers vary if measurable and scoped. Example NFR: “A first-time student shall submit a booking request using the documented steps in the stated usability test scenario without staff assistance.” Example functional/performance statement: “The system shall return available-room results within [agreed threshold] for [defined request load].” “Use a cloud database” is a design choice; it may satisfy a requirement but does not state the needed outcome/quality itself.

**Marks:** two measurable rewrites (4); correct type/reasoning (2); analysis/design distinction (2).
</details>

### M4-S02 — DFD construction/validation (10 marks)

**Prompt:** Describe a context diagram and Level-0 DFD for a library-lending system involving Member, Librarian, and Book Records. Include at least three major processes, one data store, named flows, and two DFD validation rules.

<details><summary>Reveal model answer and marking guide</summary>

Context: Member/librarian send lending/return/member/book data to Library Lending System; system sends loan confirmation, due-date notice, and reports as appropriate. Level-0 might include Verify Member, Record Loan/Return, Update Availability, Produce Overdue Report; Book/Loan Records is a data store. Flows are nouns (loan request, member status, loan record). Rules: every process has input/output; no direct entity-to-entity or store-to-store/entity flows; parent/child balance; processes are verb phrases.

**Marks:** external entities/flows (2); major processes/store (3); valid naming (2); two rules explained (2); coherent boundary/levels (1).
</details>

### M4-S03 — ERD and M:N resolution (8 marks)

**Prompt:** A student can enrol in many courses and each course has many students. The system must retain semester and grade for each enrolment. Describe the ERD entities/keys/cardinalities needed and explain why direct M:N is insufficient.

<details><summary>Reveal model answer and marking guide</summary>

STUDENT(StudentID PK…), COURSE(CourseCode PK…), ENROLLMENT(StudentID FK, CourseCode FK, Semester, Grade; composite PK may include StudentID/CourseCode/Semester). STUDENT 1:N ENROLLMENT and COURSE 1:N ENROLLMENT. Direct M:N does not provide a place for relationship-specific semester/grade data or an enrolment record identity.

**Marks:** entities/keys (3); cardinalities (2); associative-entity explanation (2); relationship-specific attributes (1).
</details>

### M4-S04 — Package consistency (8 marks)

**Prompt:** FR-03 says “The system shall prevent booking of an unavailable room.” The Level-0 DFD has `Reserve Room` but no room-availability data/store; the ERD has ROOM but no booking status; a user story says “As a student, I want to browse rooms.” Identify three inconsistencies or missing links and propose corrections.

<details><summary>Reveal model answer and marking guide</summary>

Potential corrections: add availability/room-status input/store and checking process/data flow to DFD; include availability/status data/relationship in ERD (for example Room and Booking/Reservation with status/date constraints); create/trace a functional requirement/use-case candidate for browsing rooms; link FR-03 to availability check/reservation model; ensure terminology Room/Booking/Reservation is consistent. Other reasoned corrections earn credit.

**Marks:** three valid issues (3); model corrections (3); traceability/naming explanation (2).
</details>

---

## 12. Phase 4 Module 4 review

### Completed

- Six source-labelled requirements/modelling lessons, examples, misconceptions, and validation rules.
- Requirements-package Case Studio scaffold and eight future model-lab specifications.
- 18 MCQ drafts and four subjective prompts with hidden/revealable model guides.

### Limitations / deferrals

- Across Modules 1–4, the reviewed content seed is 70 MCQs and 16 subjective prompts; it remains below the 100/20 target and is not a functional bank.
- Neither DFD/ERD drawing nor automatic model validation is implemented yet.
- The app must keep simulated gathering results distinct from real stakeholder evidence.

## 13. Approval gate

Approve or request changes to Module 4 content. On approval, the next Phase 5 work will implement the requirements-quality, DFD, ERD, and traceability model labs in the same standalone HTML file.
