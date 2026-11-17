# Phase 4 — Module 5 Content: Object Orientation and UML Functional / Structural Models

**Course:** INFT 255 — System Analysis & Design
**Module position:** Weeks 7–9
**Status:** Content complete for review. UML interaction implementation is deliberately deferred to Phase 5.

---

## 1. Source boundaries and module outcome

| Learner-facing label | Source | Use in this module |
|---|---|---|
| Lecturer material | C1 pp. 21–30; Week 5 deck | OO vocabulary, UML relationships, use cases, class/object diagrams, CRC, and component concepts. |
| Standards / academic context | OMG *UML 2.5*; Kruchten *4+1 View Model* verified records | clarify UML as a language, notation semantics, and architecture-view rationale. |
| Verified video reinforcement | Blancaflor Arada, *Systems Analysis and Design 6 — Object Modeling* (37:42) | optional OO/class-model preparation; details recorded in Phase 1 report. |
| Applied example | Course registration case carried from C1 | demonstrates traceability without asserting real stakeholder findings. |

### Module outcome

Learners can identify meaningful OO candidates from requirements; distinguish class/object, attribute/state, method/message, inheritance/polymorphism, and encapsulation; choose UML relationships and multiplicities with rationale; construct goal-centred use-case models/descriptions; use CRC reasoning; and create/critique basic class, object, and component diagrams that trace back to requirements.

### Required artefacts

1. UML modelling plan using stakeholder/view questions.
2. Use-case diagram with at least four actors, ten goal-level use cases, an `«include»`, an `«extend»`, and actor/use-case generalisation where justified.
3. Three textual use-case descriptions connected to requirement IDs.
4. Candidate-class list and five CRC cards.
5. Class diagram, object snapshot, and basic component diagram.
6. FR → use case → class/operation traceability seed.

---

## 2. Lesson M5.1 — Object orientation models responsibilities and collaborating things

**Primary source:** C1 pp. 21–22
**Key terms:** object, class, instance, attribute, state, operation/method, message, encapsulation, information hiding, inheritance, polymorphism, dynamic binding, abstract/concrete.

| Term | Meaning | Registration example |
|---|---|---|
| Object / instance | one identifiable runtime thing with state and behaviour | the particular student `S-1042` |
| Class | blueprint for similar objects | `Student` |
| Attribute / state | data held by an object | `studentId`, `programme`, `clearanceStatus` |
| Operation / method | service/behaviour offered by a class | `checkPrerequisite(course)` |
| Message | request from one object to another to perform an operation | `registration.checkPrerequisite(course)` |

**Encapsulation** packages state and related operations. **Information hiding** limits dependence on internal representation: a collaborator needs the advertised operation/interface, not the private implementation. This supports change control; it must **not** be taught as an argument for tight coupling. Good design normally seeks appropriate **low coupling** and focused/high cohesion.

**Inheritance** represents a stable “is-a” relationship: `Student` and `Lecturer` may inherit shared identity/contact features from abstract `UniversityMember` if this improves the model. **Polymorphism** allows subclasses to respond appropriately to the same operation contract; dynamic binding selects the concrete behaviour at runtime. Do not create inheritance merely because two classes share an attribute.

---

## 3. Lesson M5.2 — UML is a language, not a project method

**Primary source:** C1 pp. 22–23
**Supplementary context:** OMG UML 2.5 verified record; Kruchten verified record.

UML helps specify, visualise, construct, and document aspects of a system. It does not prescribe an SDLC, replace requirements work, or make a diagram correct merely because a notation symbol was used.

A practical model-selection question is: **what stakeholder question needs answering?**

| Question | Useful view/model | It does not replace |
|---|---|---|
| Which user goals/functional requirements matter? | use-case view / use-case diagram and descriptions | a data/behaviour design model |
| Which responsibilities and data collaborate? | logical/class/object view | deployed infrastructure details |
| Which code modules expose/need interfaces? | component / development view | a physical-node diagram |
| Where do software artifacts run and communicate? | deployment / physical view | a class model |
| Which high-value scenarios prove the architecture? | use-case/scenario view | every other architecture view |

C1’s use-case, logical, process, implementation/component, and deployment perspectives align with the 4+1 idea of complementary stakeholder views. They are not five independent drawings: a critical scenario connects the views.

### UML building blocks

- **Things:** structural, behavioural, grouping, and annotational elements.
- **Relationships:** dependency, association, generalisation, realisation (with aggregation/composition as association variants for lifecycle/whole-part meaning).
- **Diagrams:** selected representations for a question, not a checklist to draw without purpose.
- **Constraints/stereotypes/tagged values:** qualified notation such as `{ordered}`, `«include»`, or a documented property. Use only when their meaning is explained.

**Accuracy note:** UML diagram taxonomy/count wording varies across versions and introductory sources. The application will identify UML 2.5 as its checked formal reference and teach the needed diagram purposes rather than claim one timeless count.

---

## 4. Lesson M5.3 — Relationship notation communicates different claims

**Primary source:** C1 pp. 23–24
**Key terms:** dependency, association, aggregation, composition, generalisation, realisation, multiplicity, role.

| Relationship | Claim being made | Typical visual / example | Misuse to avoid |
|---|---|---|---|
| Dependency | one element temporarily uses/depends on another | dashed arrow; `RegistrationService` uses `PaymentGateway` | using it for persistent structural knowledge |
| Association | objects have a structural connection/know about each other | solid line; `Student`—`Enrollment` | claiming lifecycle ownership without evidence |
| Aggregation | weak whole-part relation; parts may exist independently | hollow diamond at whole | using diamond simply because one noun contains another |
| Composition | strong whole-part ownership; part lifecycle depends on whole | filled diamond at whole; `RegistrationSession` contains session entries, only if the lifecycle claim holds | treating every FK or database containment as composition |
| Generalisation | specialised element is a kind of general element | solid line with hollow triangle toward parent | modelling a role/use as “is-a” when it is only a relationship |
| Realisation | implementation fulfils a contract/interface | dashed line with hollow triangle toward interface | using it when there is no defined contract |

**Notation accuracy:** association is normally shown as a **solid line**. A dashed arrow communicates dependency; it is not an association. This corrects the simplified/conflicting statement in a supplied slide and follows the C1/OMG-aligned distinction.

**Multiplicity** describes allowed number of linked instances at each end: `1`, `0..1`, `0..*`, `1..*`. State a rule in words before choosing a multiplicity. For example, an `Enrollment` has exactly one `Student`; a `Student` may have zero or many `Enrollment` records in a given model. Multiplicity is not a guess about a one-time screenshot.

---

## 5. Lesson M5.4 — Use cases model externally visible goals

**Primary source:** C1 pp. 24–26
**Key terms:** actor, use case, system boundary, association, `«include»`, `«extend»`, actor generalisation, goal level.

A **use case** is a goal-oriented system capability delivering observable value to an external **actor**. An actor is a role external to the system boundary, not a database, internal class, button, screen, or necessarily one named person.

```text
               ┌──── Course Registration System ────┐
Student ───────│ (Register for Courses)               │
               │      «include»                      │
               │ (Check Prerequisite)                │
               │      «extend»                       │
               │ (Request Override)                  │
Bank ──────────│ (Confirm Payment)                   │
               └─────────────────────────────────────┘
```

**Accessible text alternative:** A Student interacts with Register for Courses. Registration always includes Check Prerequisite. Request Override is an optional/conditional extension at an identified extension point. Bank is external and interacts with Confirm Payment.

| Relation | Use when | Direction / reasoning |
|---|---|---|
| Actor–use case association | actor participates in the goal | line connects actor and use case |
| `«include»` | base use case always reuses a required common subfunction | dashed arrow from base use case to included use case |
| `«extend»` | optional/conditional additional behaviour augments a complete base use case | dashed arrow from extension use case to base use case |
| Generalisation | specialised actor/use case inherits a more general role/goal | hollow triangle points to general actor/use case |

Do not label implementation steps (“Click Submit”) as use cases. Use a stable verb–object user goal such as `Register for Courses`. Do not use `«include»` merely to make a diagram visually detailed; explain the mandatory reuse. Do not reverse the include/extend arrow.

---

## 6. Lesson M5.5 — Textual use-case descriptions make behaviour reviewable

**Primary source:** C1 pp. 26–27

A diagram is an overview; a description makes the scenario testable and exposes assumptions.

```text
UC-03: Register for Courses
Primary actor: Student
Trigger: Student submits selected courses.
Preconditions: Student is authenticated; registration period is open.
Postconditions: Valid enrolments are recorded, or no enrolment is changed.
Normal flow:
  1. Student selects courses.
  2. System verifies student identity and prerequisite status.
  3. System checks fee clearance and class capacity.
  4. System records enrolment and presents confirmation.
Alternative / exception:
  3a. If a prerequisite is not met, system explains the rejection and offers the relevant next action.
Non-functional note: Response target and access-control rules are specified by linked NFRs.
Traceability: FR-02, FR-05; NFR-03.
```

A description should identify ID, actors/stakeholders, trigger, assumptions/preconditions, normal flow, alternate/exception flows, postconditions, and relevant non-functional notes. It should not silently invent actual business policy. Applied examples remain explicitly simulated until stakeholder evidence exists.

---

## 7. Lesson M5.6 — Discover candidate classes, then test responsibilities

**Primary source:** C1 pp. 27–28
**Key terms:** textual analysis, CRC card, responsibility, collaborator, domain/design boundary.

Textual analysis can begin with nouns/noun phrases as candidate classes and verbs as candidate responsibilities. It is a prompt, not an automatic conversion: do not turn every word into a class. Filter likely duplicates, attributes, broad concepts, UI labels, reports, and transient events; retain domain concepts that have identity, information, behaviour, or meaningful collaboration.

| Candidate | Decision | Rationale |
|---|---|---|
| Student | class | has identity, data, and interacts with enrolment goals |
| Course | class | has identity/data and supports eligibility/capacity rules |
| Enrollment | class/association class | captures Student–Course relationship facts such as semester/status |
| “Submit” | operation/event, not normally a class | verb/action does not establish enduring domain identity |
| Student name | attribute | describes Student rather than an independent collaboration |

A **CRC card** records **Class – Responsibilities – Collaborators**. Example:

| Class | Responsibilities | Collaborators |
|---|---|---|
| Enrollment | validate status; record course choice; expose confirmation data | Student, Course, RegistrationService |

Role-play a textual use-case flow: pass a “message” between cards and ask whether each responsibility has a sensible owner. If no class can answer a required message, revise the candidate model rather than adding a random arrow.

---

## 8. Lesson M5.7 — Class and object diagrams test static structure

**Primary source:** C1 pp. 28–29
**Key terms:** visibility, type, operation, association class, object snapshot, constraint.

A class box usually has name, attributes, and operations. Typical visibility marks are `+` public, `-` private, and `#` protected; their detailed language implementation depends on the target language, but the model should communicate responsibility and intended access.

```text
+---------------------------+       1        0..*
| Student                   |----------------------| Enrollment
+---------------------------+                      +----------------------------+
| - studentId: String       |                      | - semester: String         |
| - clearanceStatus: Status |                      | - status: EnrolmentStatus  |
+---------------------------+                      +----------------------------+
| + requestRegistration()   |                      | + confirm()                |
+---------------------------+                      +----------------------------+
```

**Accessible text alternative:** Student has private `studentId` and `clearanceStatus` attributes and a public `requestRegistration` operation. Each Enrollment is linked to exactly one Student; a Student can have zero or more Enrollment records. Enrollment has semester/status data and a confirm operation.

An **object diagram** is a snapshot of particular instances and links, for example `s1042:Student` linked to `enr77:Enrollment`. It checks whether a class diagram can represent a plausible actual case. It does not replace the class diagram’s general rules.

Validate a class diagram by checking: clear responsibilities; sensible names/types; multiplicities in words; no duplicated relationship facts; use-case messages map to operations/responsibilities; required persisted facts agree with the ERD; and inheritance/whole-part claims are defensible.

---

## 9. Lesson M5.8 — Components expose replaceable interface boundaries

**Primary source:** C1 pp. 29–30
**Key terms:** component, provided interface, required interface, port, dependency.

A component groups cohesive implementation responsibility behind interfaces. It is not simply a class drawn larger. For the registration example, possible components are `Registration UI`, `Registration Service`, `Student Records Adapter`, `Payment Adapter`, and `Reporting Service`.

```text
[Registration UI] -- requires IRegistration --> [Registration Service]
[Registration Service] -- requires IPayment --> [Payment Adapter]
[Registration Service] -- provides IRegistration --> other approved consumers
```

**Accessible text alternative:** The UI relies on a registration interface provided by Registration Service. Registration Service relies on a payment interface supplied by Payment Adapter. The model shows interface dependencies, not where any component physically runs; deployment is introduced in Module 6.

A useful design question is: could a component implementation change while consumers retain the same contract? If yes, make the contract explicit and test whether required/provided interfaces match. Component boundaries do not remove the need for deployment/security/availability reasoning later.

---

## 10. Case Studio — UML functional/structural package

For the selected case, create:

1. an FR-to-use-case map and 10 goal-level use cases with actors;
2. one justified `«include»`, one `«extend»`, and a generalisation only where the “is-a” claim is sound;
3. three fully described use cases with alternate/exception paths and linked requirement IDs;
4. a candidate-class decision log, five CRC cards, and an eight-class model;
5. a class/object consistency check against the Module 4 ERD;
6. five components with named required/provided interfaces;
7. a traceability extract: `FR → UC → class responsibility/operation → component`.

---

## 11. Future Module 5 visual explanations and simulations

| Interaction | Learner task | Feedback requirement |
|---|---|---|
| OO vocabulary sorter | distinguish class/object/attribute/method/message and inheritance/polymorphism examples | explain the ownership/behaviour rationale, not only the label |
| View-to-question planner | select UML view/model for stakeholder concern | flag when a model answers a different question |
| Relationship and multiplicity clinic | choose dependency/association/aggregation/composition/generalisation/realisation and multiplicity | require lifecycle or contract rationale; correct solid/dashed notation misconception |
| Use-case boundary builder | select external actors, goal-level use cases, include/extend/generalisation | explain direction and mandatory/conditional reuse |
| Use-case description debugger | repair trigger/precondition/normal/alternate/postcondition gaps | identify the missing testable condition |
| CRC role-play | assign messages to collaborators and detect unowned responsibility | show why a responsibility is misplaced/duplicated |
| Class/object validator | compare a class model with object snapshot and ERD constraints | reveal incompatible multiplicity/key/relationship interpretation |
| Component-interface matcher | connect required/provided interfaces and flag invalid dependency | distinguish logical component interface from deployment node |
| Module challenge | trace one FR through use case, class operation, and component | explain every link and surface orphaned artefacts |

---

## 12. Formative assessment seed — 18 MCQs

| ID | Level | Prompt | Correct answer and explanation | Source |
|---|---|---|---|---|
| M5-Q01 | Remember | `Student` is best described as: A object snapshot B class C message D deployment node | **B.** It is a blueprint/type for individual student objects. | C1 p. 21 |
| M5-Q02 | Understand | Which distinction is correct? A a method is an object’s request and a message is behaviour B a message requests an operation/method from another object C class and object are always the same D attributes are external actors | **B.** A message asks a receiving object to perform an operation. | C1 p. 21 |
| M5-Q03 | Apply | Which candidate is normally an attribute rather than a class in a registration domain? A Student B Course C studentId D Enrollment | **C.** It describes/identifies Student; it is not usually an independent collaborator. | C1 pp. 21, 27 |
| M5-Q04 | Understand | Information hiding primarily means: A publish every internal field B depend on advertised services rather than internal representation C use maximum coupling D delete operations | **B.** Collaborators should not rely unnecessarily on internal implementation. | C1 p. 21 |
| M5-Q05 | Analyse | A model makes `ScholarshipStudent` inherit from `Student` only because both contain an email address. Best critique? A valid inheritance B shared attribute alone does not establish a stable is-a specialisation C must be composition D it is a DFD error | **B.** Inheritance requires an appropriate specialisation claim, not mere duplicate data. | C1 pp. 21–22 |
| M5-Q06 | Remember | UML is best described as: A one mandatory SDLC B a language for specifying/visualising/documenting models C a database engine D a test case | **B.** UML is a modelling language, not a lifecycle method. | C1 p. 22; OMG |
| M5-Q07 | Apply | A stakeholder asks where software artifacts run and what protocol connects them. Best next model: A use-case diagram B deployment diagram C ERD D context DFD | **B.** Deployment answers physical-node/artifact/communication questions. | C1 pp. 22–23 |
| M5-Q08 | Understand | Standard UML convention normally shows an association as: A solid line B dashed arrow C filled diamond only D actor oval | **A.** Dashed arrows are commonly dependency; association is solid. | C1 p. 23; OMG |
| M5-Q09 | Apply | `RegistrationService` temporarily calls a `PaymentGateway` interface but does not retain a structural link. Best relationship: A composition B dependency C generalisation D association class | **B.** A temporary use/dependence is expressed as dependency. | C1 p. 23 |
| M5-Q10 | Analyse | Which claim most strongly justifies composition? A Course lists a title B a part cannot meaningfully exist once its owning whole is destroyed C two classes exchange a message D every student has an ID | **B.** Composition asserts strong ownership/lifecycle dependence. | C1 pp. 23–24 |
| M5-Q11 | Apply | One Student can have zero or more Enrollment records; every Enrollment has exactly one Student. Correct multiplicities are: A Student end 1 and Enrollment end 0..* B Student end 0..* and Enrollment end 1 C both 1 D both 0..* | **A.** At the Student end, each Enrollment sees one Student; at Enrollment end, a Student sees 0..*. | C1 p. 24 |
| M5-Q12 | Remember | An actor in a use-case model is: A a database table B an external role that interacts with the system C always a named human D an internal class | **B.** It represents an external role, which can be a system/service. | C1 p. 24 |
| M5-Q13 | Analyse | `Register for Courses` always checks prerequisites. A `Request Override` occurs only when normal eligibility fails. Correct relation choice? A override includes registration; registration extends override B registration includes check; override extends registration C both are aggregation D no relationship can be shown | **B.** Required common behaviour is include; conditional extra behaviour is extend. | C1 pp. 24–26 |
| M5-Q14 | Evaluate | A use-case ellipse labelled “Click Submit Button” is weakest because: A buttons are illegal in UI B it describes a UI step, not an externally valuable actor goal C actors cannot submit D it lacks a primary key | **B.** Use cases should express goal-level capability, not implementation clicks. | C1 pp. 24–25 |
| M5-Q15 | Apply | Which omitted item most weakens a description of `Register for Courses`? A alternate path for unmet prerequisite B font name C class colour D source-code variable name | **A.** Alternate/exception paths are necessary to review how the goal behaves when the normal path fails. | C1 p. 26 |
| M5-Q16 | Understand | A CRC card is used primarily to: A calculate NPV B list class responsibilities and collaborators C assign IP addresses D balance DFD levels | **B.** CRC supports responsibility/collaboration reasoning. | C1 pp. 27–28 |
| M5-Q17 | Analyse | A use-case step sends `checkPrerequisite(course)` to Student. Class-model validation should confirm: A Course must be an actor B a suitable receiving responsibility/operation exists C every line is composition D the DFD has no stores | **B.** Sequence/use-case actions need a defensible owner in the class model. | C1 pp. 26–29 |
| M5-Q18 | Evaluate | A team calls a deployment node `Payment Adapter` and places it beside `Registration Service`. Best correction? A erase the adapter B model logical components/interfaces separately; show physical nodes/artifacts in deployment later C make it an actor D use only ERD | **B.** Component/interface and deployment node answer different questions. | C1 pp. 29–30 |

**Cognitive coverage:** remembering 3; understanding 4; applying 5; analysing 4; evaluating 2. Items are author-created, source-mapped formative drafts—not lecturer-approved answers. Later assessment review will remove redundancy across the full bank.

---

## 13. Subjective examination-practice seed — four questions

### M5-S01 — OO candidates and responsibilities (10 marks)

**Prompt:** From the statement “A student selects courses; the system validates prerequisites and fee clearance; successful selections create an enrolment record and confirmation,” identify four candidate classes, two attributes, four operations/responsibilities, and explain one item you would *not* turn into a class.

<details><summary>Reveal model answer and marking guide</summary>

Possible classes include Student, Course, Enrollment, and RegistrationService (or a suitably justified domain/service class). Attributes can include Student.studentId, Student.clearanceStatus, Course.courseCode, Enrollment.status. Responsibilities can include Student.requestRegistration, RegistrationService.validatePrerequisites, RegistrationService.checkClearance, Enrollment.confirm/create. “Select”/“successful” is an action/state phrase rather than normally an enduring independent class; a good answer explains the choice. Other coherent assignments earn credit.

**Marks:** candidate classes with rationale (4); attributes (2); responsibilities/owners (3); non-class reasoning (1).
</details>

### M5-S02 — Use-case relationships and description (10 marks)

**Prompt:** For a course-registration system, propose a goal-level `Register for Courses` use case, one included use case, one conditional extending use case, and a compact description including actor, trigger, precondition, normal flow, alternate flow, postcondition, and one linked requirement ID.

<details><summary>Reveal model answer and marking guide</summary>

Example: Student starts `Register for Courses`; it `«include»`s `Check Prerequisite` because checking is required; `Request Override` `«extend»`s Registration only if a prerequisite fails and policy allows an override. Trigger can be student submission; preconditions can include authenticated student/active period; normal flow selects, checks, validates, records, confirms; alternate explains unmet prerequisite; postcondition records valid enrolment or makes no improper change; link FR-02/another stated FR. Include arrows/labels must support mandatory versus conditional meaning.

**Marks:** goal/actor/boundary (2); include/extend choice/direction/rationale (3); description elements (4); requirement traceability (1).
</details>

### M5-S03 — Relationship/multiplicity critique (8 marks)

**Prompt:** A class diagram has `Student` connected to `Enrollment` by composition, with `Student 1..*` at the Enrollment end and `Enrollment 0..1` at the Student end. Critique the multiplicities and the composition claim using stated business assumptions.

<details><summary>Reveal model answer and marking guide</summary>

For the normal rule “an Enrollment belongs to one Student; a Student may have zero or many Enrollment records,” multiplicities should express 1 Student per Enrollment and 0..* Enrollments per Student (placed at the opposite ends accordingly). Composition is only justified if enrollment records cannot meaningfully outlive their owning student in the relevant system/lifecycle; otherwise a plain association may be more defensible. The answer must state assumptions rather than claim the correct ownership without evidence.

**Marks:** correct multiplicity reasoning (4); lifecycle/whole-part analysis (2); clear assumptions/notation explanation (2).
</details>

### M5-S04 — Traceability and component boundary (10 marks)

**Prompt:** FR-05 says “The system shall confirm payment before recording enrolment.” Explain a traceability path from this FR through a use case, a class responsibility/operation, and components/interfaces. Identify one design inconsistency if the class model lacks any payment-related responsibility.

<details><summary>Reveal model answer and marking guide</summary>

Example: FR-05 → `Register for Courses` description step `Confirm Payment` / use case → `RegistrationService.confirmPayment()` or a PaymentService/adapter responsibility → Registration Service requires `IPayment`, Payment Adapter provides `IPayment`. If no class/service responsibility can receive/coordinate the payment check, the use case cannot be realised in the model; add/reassign a justified responsibility and trace it. It is not enough to draw a component without a contract.

**Marks:** FR-to-use-case link (2); operation/responsibility ownership (3); required/provided interface/component mapping (3); inconsistency/correction (2).
</details>

---

## 14. Phase 4 Module 5 review

### Completed

- Eight source-labelled OO/UML functional and structural lessons, original accessible text diagrams, case continuity, terminology corrections, and validation rules.
- Case Studio functional/structural artifact package and nine planned interactive model labs.
- 18 MCQ drafts and four subjective prompts with hidden model answers/marking guides.

### Limits and academic safeguards

- Across Modules 1–5, the reviewed source-mapped seed is **88 MCQs and 20 subjective prompts**. This meets the subjective-number target in draft count but is not a finished functional assessment bank; it remains below the 100-MCQ requirement.
- No lecturer answer key or marking rubric was supplied. Answers are author-created, explained, and source-mapped; they are **not lecturer-approved**.
- UML diagrams are original teaching representations, not reproduced lecture/publisher visuals. The full OMG standard is a specification reference, not asserted as fully accessible course reading.
- This package does not yet implement an app lesson, freeform UML editor, assessment session, scoring, or saved artefact.

## 15. Approval gate

Approve or request changes to Module 5 content. Approval authorises Phase 5 implementation of the OO/UML functional/structural simulations in the existing single-file offline HTML application; it does not yet authorise Module 6 content or end-to-end final integration.
