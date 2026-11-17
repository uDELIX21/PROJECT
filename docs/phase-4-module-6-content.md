# Phase 4 — Module 6 Content: Architecture, Deployment, Behavioural Models, and Cross-Model Validation

**Course:** INFT 255 — System Analysis & Design
**Module position:** Weeks 10–11
**Status:** Content complete for review. Module 6 simulations, course-wide assessment sessions, and persistent artefact storage remain deferred to later approved phases.

---

## 1. Source boundaries and module outcome

| Learner-facing label | Source | Use in this module |
|---|---|---|
| Lecturer material | C1 pp. 31–37 | design transition, layering, deployment, sequence/communication/activity/state models, validation. |
| Standards / academic context | OMG UML 2.5; Kruchten *4+1 View Model* verified records | notation/architecture clarification and view rationale. |
| Verified video reinforcement | New Ur Academy, *System Analysis and Design, Lecture 10: UML Activity Diagram, Swimlane Diagram* (33:08) | optional activity/swimlane reinforcement; details retained in Phase 1 report. |
| Applied example | Course registration and payment-confirmation scenarios derived from supplied notes | makes model links visible; it does not assert real stakeholder findings. |

### Module outcome

Learners can distinguish analysis from design decisions; allocate concerns to appropriate layers and components; map artifacts to deployment nodes while reasoning from constraints; create/critique sequence and communication representations of one scenario; model workflow in an activity diagram; decide when an object state machine is useful; and test consistency from requirements through runtime messages, operations, components, and deployed artifacts.

### Required artefacts

1. Layered architecture and component dependency rationale.
2. Deployment diagram with nodes, execution environments/artifacts, communication paths/protocol assumptions, and constraint rationale.
3. Normal and alternate sequence diagrams for a high-value use case.
4. Communication-diagram conversion of one sequence scenario.
5. Activity diagram with guards, swimlanes, and matched fork/join where relevant.
6. Optional state machine for a lifecycle-heavy object.
7. Cross-model validation record.

---

## 2. Lesson M6.1 — Design elaborates the analysis model under constraints

**Primary source:** C1 pp. 31–32
**Key terms:** analysis, design, validation, layering, package, cohesion, coupling, interface, HCI layer, domain/problem layer, data-management layer, physical layer.

Analysis establishes **what** the system needs to accomplish and why. Design makes justified **how** choices: responsibilities, component boundaries, interfaces, persistence, technology, physical placement, and interaction protocols. It is not a one-way handoff: design can expose an ambiguity that requires a requirement/model review.

A useful layered teaching view is:

```text
[HCI / presentation]  →  user interaction and input/output presentation
          ↓
[Domain / application] →  business rules and use-case coordination
          ↓
[Data management]      →  persistence, retrieval, external data adapters
          ↓
[Physical / deployment]→  nodes, devices, runtime environments, networks
```

**Accessible text alternative:** The presentation layer calls domain/application services. Those services depend on data-management services/adapters. Physical deployment determines where the resulting artifacts execute and connect; it is not another class diagram layer.

- **High cohesion:** a module has a focused, related purpose.
- **Low coupling:** modules minimise unnecessary knowledge/dependence on each other’s internals.
- **Validation:** a design choice must still respect requirements, NFRs, constraints, and earlier models.

Example: `Registration UI` should request registration work through a documented service interface rather than directly changing enrolment database records. This separates HCI concerns from rules such as prerequisite/clearance checks and gives later tests a clearer boundary.

---

## 3. Lesson M6.2 — Deployment models physical/execution reality

**Primary source:** C1 pp. 32–33
**Key terms:** node, device, execution environment, artifact, communication path, protocol, client/server, tier, cloud.

A deployment diagram shows how deployed software artifacts are allocated to **nodes** and connected. A node can represent hardware or an execution environment. An **artifact** is a deployable piece of information/software; it is not automatically the same as a component/class/node.

```text
[Student device / browser]
          | HTTPS (assumed secure transport)
          v
[Web/App server] -- database connection --> [Database server]
          |
          | approved integration protocol (assumption)
          v
[External payment gateway]
```

**Accessible text alternative:** A student uses a browser on a client device. It communicates with a university web/application server using HTTPS as a stated assumption. The application server connects to a database server and an external payment gateway. The diagram does not claim a specific real university architecture.

Deployment decisions must state their constraints/assumptions. For example, connectivity, device variability, availability, privacy/security needs, backup/recovery, operating support, and external integration availability may influence the design. Ghana’s Data Protection Act context can inform constraint discussion but this learning environment does not provide legal advice or infer undisclosed compliance obligations.

### Distinctions

| Question | Correct primary model |
|---|---|
| What code/module contract does Registration Service offer? | component diagram/interface model |
| Which server/device/environment runs a deployable artifact? | deployment diagram |
| Which object owns `confirmPayment()`? | class/responsibility model |
| What happens first during payment confirmation? | sequence/communication model |

---

## 4. Lesson M6.3 — Sequence diagrams expose time-ordered collaboration

**Primary source:** C1 pp. 33–35
**Key terms:** participant, lifeline, activation, synchronous/asynchronous message, return, self-message, create/destroy, combined fragment, `alt`, `opt`, `loop`, `par`, `ref`.

Choose one use-case scenario, then turn its normal and alternate flows into ordered messages. Each participant should be a justified actor, boundary/UI, controller/service, entity, or external system—not every database field.

```text
Student → RegistrationUI: submitSelection(courses)
RegistrationUI → RegistrationService: register(studentId, courses)
RegistrationService → StudentRecord: checkPrerequisites(courses)
StudentRecord --> RegistrationService: eligible / ineligible
alt [eligible]
  RegistrationService → PaymentGateway: confirmPayment(studentId)
  PaymentGateway --> RegistrationService: confirmation
  RegistrationService → Enrollment: create(courses)
  RegistrationService --> RegistrationUI: registrationConfirmation
else [not eligible]
  RegistrationService --> RegistrationUI: explainRejection
end
```

**Accessible text alternative:** Student sends selected courses to the UI; the UI calls Registration Service. The service checks prerequisites. If eligible, it confirms payment, creates Enrollment, and returns confirmation. If not eligible, it returns an explanation. The `alt` fragment labels the two guarded outcomes.

### Review rules

1. Time runs from top to bottom. Lifelines are participants, not merely data stores.
2. A message should correspond to an operation/responsibility in the class/component model or expose a gap to resolve.
3. A synchronous message conventionally expects completion before the sender continues; asynchronous messaging has different waiting/return implications. Use the chosen semantics consistently rather than treating arrow styling as decoration.
4. Use `alt` for mutually exclusive guarded paths, `opt` for optional one-path behaviour, `loop` for repeated behaviour, `par` for concurrent regions, and `ref` to name a reused interaction.
5. A return need not be drawn for every call; when shown, it should clarify an important returned result.

An alternate flow should not be hidden in prose if it changes the ordering/recipient/error handling of the design.

---

## 5. Lesson M6.4 — Communication diagrams preserve collaboration and order differently

**Primary source:** C1 p. 35
**Key terms:** link, numbered message, nested message, structural emphasis, semantic equivalence.

A communication diagram can represent the same scenario as a sequence diagram. It foregrounds participating objects/links rather than a vertical time axis. Numbering preserves order.

```text
student:Student -- 1: submitSelection(courses) --> ui:RegistrationUI
ui:RegistrationUI -- 1.1: register(studentId,courses) --> service:RegistrationService
service:RegistrationService -- 1.1.1: checkPrerequisites(courses) --> record:StudentRecord
service:RegistrationService -- 1.2 [eligible]: confirmPayment(studentId) --> gateway:PaymentGateway
service:RegistrationService -- 1.3 [eligible]: create(courses) --> enrollment:Enrollment
```

**Accessible text alternative:** The Student sends message 1 to Registration UI. UI sends nested message 1.1 to Registration Service. The service checks prerequisites with 1.1.1; if eligible it calls payment with 1.2 and creates enrolment with 1.3. Links show which objects communicate, while numbers show the sequence.

The two diagrams are **not** separate requirements. If converted accurately, they describe the same scenario/semantics: participants, messages, guards, and ordering must remain consistent. A communication diagram is not an excuse to omit order merely because it has no long lifelines.

---

## 6. Lesson M6.5 — Activity diagrams model workflow and responsibility flow

**Primary source:** C1 pp. 35–36
**Key terms:** initial node, final node, action, control flow, object flow, decision, merge, guard, fork, join, swimlane.

An activity diagram models workflow. It can show actions performed by different roles, conditional paths, parallel work, and objects/data moving between actions. It does not show the lifecycle of one object in the same way as a state machine.

```text
Start
  ↓
[Student] Select courses
  ↓
[System] Validate prerequisites
  ↓
<eligible?> ──[no]──> [System] Explain rejection ──> End
     │[yes]
     v
[System] Confirm payment
  ↓
[System] Record enrolment
  ↓
[Student] Receive confirmation
  ↓
End
```

**Accessible text alternative:** Activity begins when the Student selects courses. The System validates prerequisites. At decision `eligible?`, `no` leads to explanation/rejection and end; `yes` leads to payment confirmation, recording enrolment, confirmation, and end. Student/System labels are swimlane responsibilities.

### Activity-model checks

- A decision’s outgoing flows use complete, mutually meaningful guard conditions such as `[yes]` and `[no]`; a merge reunites alternatives.
- A fork splits concurrent flows; a join waits for required concurrent flows. Do not use fork/join merely to make a model look advanced.
- Name actions with verbs and show whether an object/data result is transferred when that is meaningful.
- Swimlanes clarify responsibility; they do not show deployment nodes.

---

## 7. Lesson M6.6 — State machines and cross-model validation expose contradictions

**Primary source:** C1 pp. 36–37
**Key terms:** state, event, transition, guard, action, lifecycle, traceability, consistency.

A state machine is useful when a **single object** has important states and transitions that govern behaviour. For example, an `Enrollment` may be `Pending`, `Confirmed`, `Rejected`, or `Cancelled` under clearly stated policy. A generic “student registration workflow” with multiple participants may be better as an activity diagram instead.

```text
[Pending] -- paymentConfirmed [eligible] / recordEnrollment --> [Confirmed]
[Pending] -- prerequisiteFailed --> [Rejected]
[Confirmed] -- cancelWithinPolicy --> [Cancelled]
```

**Accessible text alternative:** An Enrollment begins Pending. Payment confirmed with the eligible guard records it and reaches Confirmed. A prerequisite failure moves it to Rejected. A policy-valid cancellation moves Confirmed to Cancelled. The policy and action must be verified/assumed, not invented as a real institutional rule.

### Cross-model consistency checklist

| Trace question | Evidence to inspect |
|---|---|
| Is the requirement represented as an observable goal? | SRS FR ↔ use case / description |
| Can the planned runtime collaboration realise the use case? | use-case step ↔ sequence/communication message ↔ class operation/responsibility |
| Is data represented where it is stored/changed? | sequence message ↔ class/ERD attribute or relationship ↔ data-management component |
| Is a component interface available for external collaboration? | responsibility ↔ required/provided interface ↔ component dependency |
| Can the design run in the stated environment? | component/artifact ↔ deployment node/path ↔ NFR/constraint |
| Are normal/alternate workflow and state rules coherent? | use-case ↔ activity ↔ sequence ↔ state machine where used |

Example inconsistency: a sequence shows `PaymentGateway.confirm()` but there is no `IPayment` required interface, payment adapter, responsibility, or deployment integration path. The remedy is not to hide the message; investigate whether the requirement/design scope is missing or misnamed, then update the linked artifacts with rationale.

---

## 8. Case Studio — Design and behaviour package

For the selected case, complete:

1. a layer/package allocation and a low-coupling/high-cohesion rationale;
2. five components and required/provided interfaces;
3. a deployment diagram with at least four nodes/execution environments/artifacts, named communication paths, and explicit assumptions;
4. normal plus alternate sequence diagrams for one high-value use case;
5. a communication conversion that preserves participants, order, and guards;
6. an activity diagram with swimlanes, decision guards, and a fork/join only if real concurrency is supported;
7. optional state machine for a lifecycle-heavy object;
8. a completed cross-model validation checklist with at least two repaired inconsistencies.

---

## 9. Future Module 6 visual explanations and simulations

| Interaction | Learner task | Feedback requirement |
|---|---|---|
| Layering/coupling clinic | place UI, domain, data, and physical concerns; identify inappropriate cross-layer dependence | explain cohesion/coupling and distinguish logical layers from physical nodes |
| Deployment mapper | allocate artifacts to nodes and select a communication-path rationale under constraints | flag node/artifact/component conflation and surface stated assumptions |
| Sequence scenario builder | order messages and complete a normal/alternate scenario | explain time order, receiving operation, and guarded `alt` flow |
| Fragment selector | select `alt`, `opt`, `loop`, `par`, or `ref` for a stated interaction condition | explain the interaction semantics rather than symbol appearance |
| Sequence-to-communication converter | apply message numbering and links to a known scenario | compare participants/order/guards against the source sequence |
| Activity workflow clinic | repair guards, decision/merge, fork/join, and swimlane responsibility | identify missing path or unmatched concurrency rule |
| State-machine decision lab | choose state versus activity representation and repair state/event/guard/action labels | explain object lifecycle focus and label any assumption |
| Cross-model consistency inspector | trace an FR through use-case, message, operation, interface, data, and node | identify orphan/contradictory artefact and a reasoned repair |
| Module challenge | design/review a payment-confirmation path from constraint to deployment | require visible links rather than a collection of disconnected diagrams |

---

## 10. Formative assessment seed — 18 MCQs

| ID | Level | Prompt | Correct answer and explanation | Source |
|---|---|---|---|---|
| M6-Q01 | Remember | A deployment diagram primarily shows: A FR wording B nodes/artifacts/communication paths C DFD balancing D user-story priority | **B.** It maps deployed software/artifacts to physical or execution nodes and their connections. | C1 pp. 32–33 |
| M6-Q02 | Understand | Which distinction is correct? A component and deployment node are always identical B a component is a logical modular unit; a node is physical/execution infrastructure C an artifact is an actor D a node is a class operation | **B.** Components, artifacts, and nodes answer different architectural questions. | C1 pp. 29–33 |
| M6-Q03 | Apply | A UI directly updates enrolment database records, bypassing prerequisite/clearance rules. Best architectural correction? A put payment in an ERD B route through a domain/application service interface C add an actor D remove the UI | **B.** This keeps HCI separate from business rules and data-management concerns. | C1 pp. 31–32 |
| M6-Q04 | Understand | High cohesion means: A module has a focused related purpose B every module knows all internals C one database is used D every action is concurrent | **A.** Cohesion concerns how strongly a module’s responsibilities belong together. | C1 p. 31 |
| M6-Q05 | Analyse | A design introduces a server name into a class diagram to answer where artifacts run. Main issue? A class diagram has too many operations B it mixes deployment concern into a logical class-structure question C it lacks a PK D it must use include | **B.** Use deployment modelling for node/artifact placement. | C1 pp. 31–33 |
| M6-Q06 | Remember | In a sequence diagram, vertical order primarily represents: A package ownership B time/order of interaction C database cardinality D actor generalisation | **B.** Time proceeds from top to bottom. | C1 pp. 33–34 |
| M6-Q07 | Apply | A prerequisite check can either allow or reject a registration. Best combined fragment: A `loop` B `alt` with `[eligible]` and `[not eligible]` guards C `par` D `ref` only | **B.** `alt` represents mutually exclusive guarded alternatives. | C1 pp. 33–35 |
| M6-Q08 | Analyse | A sequence message calls `confirmPayment()` but no class/service owns that operation. Best conclusion? A messages need not map to design B cross-model gap; add/reassign a justified responsibility or revise the scenario C turn it into a DFD store D ignore it | **B.** A message needs a defensible receiving responsibility/operation. | C1 pp. 33–35 |
| M6-Q09 | Understand | A communication diagram differs from a sequence diagram mainly because it: A cannot show order B emphasises links/numbered messages rather than a vertical time axis C replaces use cases D is a deployment diagram | **B.** Numbering preserves message order while the layout emphasises collaboration links. | C1 p. 35 |
| M6-Q10 | Apply | A communication conversion shows messages 1, 2, 4 with no explained omitted action. Most accurate feedback: A valid because arrows exist B review order/numbering; the conversion must preserve a coherent sequence C add a PK D call it a state | **B.** Numbers communicate order and should consistently represent the source scenario. | C1 p. 35 |
| M6-Q11 | Remember | An activity-diagram guard such as `[eligible]` labels: A an object attribute B condition enabling an outgoing control flow C an IP address D a component port | **B.** A guard is a condition for taking that flow. | C1 pp. 35–36 |
| M6-Q12 | Apply | Two checks genuinely run concurrently and recording may begin only after both finish. Use: A decision/merge B fork followed by join C actor generalisation D composition | **B.** Fork creates concurrent flows; join synchronises required completion. | C1 pp. 35–36 |
| M6-Q13 | Analyse | An activity decision has `[yes]` but no stated alternate guard/path. Main repair? A add a meaningful `[no]`/otherwise outcome and merge/end as appropriate B replace with a component C add an FK D remove all guards | **A.** Decision outcomes must make the workflow complete/understandable. | C1 pp. 35–36 |
| M6-Q14 | Understand | When is a state machine most useful? A to model the lifecycle of one object with meaningful states/events B to show every department’s workflow C to calculate NPV D to list use-case actors | **A.** It focuses on an object’s states and transitions. | C1 pp. 36–37 |
| M6-Q15 | Apply | `Enrollment` changes from Pending to Confirmed only when payment is confirmed and eligibility holds. Which form is strongest? A Pending → Confirmed with no label B Pending -- paymentConfirmed [eligible] / recordEnrollment --> Confirmed C a DFD arrow D an include relation | **B.** The transition identifies event, guard, and action. | C1 pp. 36–37 |
| M6-Q16 | Analyse | A component model requires `IPayment`, but deployment has no payment adapter/artifact or external integration path. This is: A valid low coupling B a cross-model inconsistency requiring investigation/repair C a complete state machine D a data-flow balance | **B.** A required integration needs a credible design/deployment counterpart. | C1 pp. 32–37 |
| M6-Q17 | Evaluate | A team deploys a payment-confirmation feature without recording connectivity/availability/security assumptions. Best improvement? A claim all constraints are met B state relevant assumptions/constraints and validate the deployment choice against them C add more classes only D replace with a DFD | **B.** Deployment reasoning must be explicit and constraint-aware. | C1 pp. 32–33 |
| M6-Q18 | Evaluate | FR-05 requires payment confirmation before enrolment record creation, but the activity diagram records enrolment first. Best response? A leave both diagrams B repair the activity or requirement after investigating the contradiction, then update trace links C add a use-case actor D hide the alternate flow | **B.** Cross-model validation should expose and resolve contradictions with rationale. | C1 pp. 33–37 |

**Cognitive coverage:** remembering 3; understanding 4; applying 5; analysing 4; evaluating 2. These are author-created, source-mapped formative drafts rather than lecturer-approved answers. A full-bank review remains necessary before final assessment implementation.

---

## 11. Subjective examination-practice seed — four questions

### M6-S01 — Layering and deployment rationale (10 marks)

**Prompt:** Propose a layered design and four-node deployment outline for an online registration system that integrates with an external payment capability. Name the responsibility of each layer/node, one communication path, and two constraints/assumptions that should be stated.

<details><summary>Reveal model answer and marking guide</summary>

A defensible design separates presentation/UI; domain/application services for prerequisite/clearance/registration coordination; data management for enrolment/student/course persistence and adapters; and physical/deployment decisions. Example nodes: student browser/device, web/application server, database server, external payment gateway. A path might be browser-to-app HTTPS as a stated transport assumption, plus a documented integration path to the payment provider. Relevant constraints/assumptions may include connectivity, availability, privacy/security, device support, backup/recovery, and external gateway availability. Answers should not claim a real institutional architecture without evidence.

**Marks:** layer responsibilities (3); nodes/artifacts/paths distinction (3); communication path (1); two relevant stated constraints/assumptions (2); reasoned rationale/source integrity (1).
</details>

### M6-S02 — Sequence and communication equivalence (10 marks)

**Prompt:** Describe a normal and alternate sequence for `Register for Courses` where prerequisite failure prevents recording enrolment. Then give the equivalent communication-diagram message numbering for the normal path and explain one consistency check against the class model.

<details><summary>Reveal model answer and marking guide</summary>

Normal example: Student → UI submit; UI → RegistrationService register; service → StudentRecord checkPrerequisites; eligible response; service → PaymentGateway confirmPayment; confirmation; service → Enrollment create; service → UI confirmation. Alternate: ineligible response leads service/UI to explain rejection and no enrolment creation. Communication numbering may be 1 submit, 1.1 register, 1.1.1 checkPrerequisites, 1.2 [eligible] confirmPayment, 1.3 [eligible] create. A consistency check verifies `checkPrerequisites`, `confirmPayment`, and `create` each have a justified receiver/operation/responsibility in the class/service model.

**Marks:** normal flow/order (3); alternate guard/outcome (2); communication links/numbering (3); class-operation consistency explanation (2).
</details>

### M6-S03 — Activity versus state model (8 marks)

**Prompt:** Explain whether an activity diagram or state machine is more appropriate for (a) the end-to-end course-registration workflow involving Student, System, and Payment Gateway and (b) the lifecycle of one Enrollment record. Give a small model outline for each and justify the choice.

<details><summary>Reveal model answer and marking guide</summary>

(a) Activity diagram: swimlanes can distinguish Student/System/external service; actions include select, validate, decision `[eligible]`, confirm payment, record, notify, and rejection alternative. (b) State machine: Enrollment states such as Pending, Confirmed, Rejected, Cancelled; events/guards/actions such as paymentConfirmed `[eligible]` / recordEnrollment. The distinction is multi-party workflow versus lifecycle of a single object.

**Marks:** correct choice for workflow (2); correct choice for object lifecycle (2); valid activity elements/guards/swimlanes (2); valid state/event/guard/action explanation (2).
</details>

### M6-S04 — Cross-model validation repair (10 marks)

**Prompt:** FR-05 says payment must be confirmed before enrolment recording. A use-case description contains the step; a sequence diagram calls `PaymentGateway.confirm()`; the class model has no payment responsibility; the component model has no payment interface; the deployment diagram contains only browser/app/database nodes. Identify four inconsistencies or missing links and propose a coherent repair path.

<details><summary>Reveal model answer and marking guide</summary>

Issues include: absent class/service owner for confirmation; absent required/provided payment contract; no payment adapter/external integration component; no deployment artifact/node/path for the external interaction; potential message naming mismatch; no stated availability/security assumptions. Repair may assign `confirmPayment()` to RegistrationService or a PaymentService, add required `IPayment` and a Payment Adapter/provider, reflect adapter/artifact and external gateway communication path in deployment, update sequence recipients/messages, and record constraints/assumptions. Requirement/use-case trace links should be retained and artefacts reviewed together.

**Marks:** four valid gaps (4); coherent responsibility/operation repair (2); interface/component repair (2); deployment/constraint and traceability repair (2).
</details>

---

## 12. Phase 4 Module 6 review

### Completed

- Six source-labelled lessons linking architecture/design decisions to deployment, interactions, workflow, object lifecycle, and consistency checks.
- Four original accessible textual UML visuals and a Case Studio design/behaviour package.
- Nine future visual/model-lab specifications.
- 18 MCQ drafts and four subjective prompts with hidden/revealable model answers and marking guides.

### Assessment milestone and limits

- The reviewed source-mapped draft seed across Modules 1–6 is now **106 MCQs and 24 subjective prompts**, exceeding the numerical minimums of 100 MCQs and 20 subjective questions.
- This is **not** a complete, validated assessment engine: drafts must still receive final course-wide duplication, answer-correctness, source-mapping, cognitive-balance, and session-mode review before they are made available as scored app assessments.
- No lecturer answer key/rubric was supplied, so no answer/model guide is represented as lecturer-approved.

### Other deferrals

- Freeform diagram drawing, automatic model validation, durable portfolio storage, app-wide resource search, timed/mixed assessment delivery, XP/mastery evidence, dashboard analytics, export/import, and final QA are not implemented by this content package.
- Applied deployment/lifecycle examples state assumptions and must not be interpreted as evidence of a real institution’s policy or infrastructure.

## 13. Approval gate

Approve or request changes to Module 6 content. Approval authorises Phase 5 implementation of the architecture, deployment, behavioural-model, and cross-model consistency labs in the existing standalone HTML app; it does not yet authorise final integration or completion claims.
