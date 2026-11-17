# Phase 4 — Module 7 Content: Revision, Examination Practice, Final Challenge, and Capstone Integration

**Course:** INFT 255 — System Analysis & Design
**Module position:** Weeks 12–13
**Status:** Content complete for review. Assessment-session delivery, timed mode, scoring, persistence, and capstone storage are deferred to Phase 5/later approved phases.

---

## 1. Source boundaries and module outcome

| Learner-facing label | Source | Use in this module |
|---|---|---|
| Lecturer material | C1 pp. 38–41; all prior C1 sections | revision comparisons, final case expectations, integrated model/package practice. |
| Supplementary academic explanation | previously verified OMG UML 2.5, Kruchten 4+1, IEEE requirements record, NISTIR 7499, CMU SEI guide | only to clarify prior module vocabulary; no new source claim replaces the supplied course sequence. |
| Applied example | continuing course-registration/payment scenario | creates a coherent synthetic revision case; all scenario facts are labelled assumptions, not stakeholder evidence. |

### Module outcome

Learners can diagnose near-neighbour SAD concept errors; repair cross-model inconsistencies; plan a defensible timed or untimed case response; explain a calculation/model rationale; assemble an integrated SAD package with traceable naming; and self-assess against an author-created, non-official marking guide.

### Required artefacts

1. Concept-bridge / misconception repair record.
2. Mid-course model-quality repair record for planning, requirements, DFD, and ERD.
3. UML/architecture clinic record with linked corrections.
4. Final case plan: scope, assumptions, time allocation, model order, and validation checklist.
5. Integrated SAD package / presentation outline.

---

## 2. Assessment integrity and feedback policy

C1 includes revision/exam practice but no accessible official answer key or marking rubric was supplied. Therefore:

- All app-produced answers, hints, scoring criteria, and model responses are **author-created** and source-mapped—not lecturer-approved.
- A model answer must be hidden until the learner chooses **Reveal model answer and marking guide**.
- Timed practice must display the time remaining, allow a deliberate submit, and retain no false claim that the outcome is an official grade.
- Every objective question needs a correct-answer explanation and a misconception/review pointer. Subjective feedback should evaluate observable elements, stated assumptions, and reasoning—not pretend to verify an unseen diagram or stakeholder fact.
- A learner must not receive completion, XP, or badge credit merely for opening a model answer. Later progress rules must require demonstrated responses/repairs.

---

## 3. Lesson M7.1 — Concept bridge: choose the model by the question it answers

**Primary source:** C1 pp. 38–39; all prior module sources.

| Concepts often confused | Precise distinction | Revision prompt |
|---|---|---|
| Analysis / design | analysis establishes needed outcomes/constraints; design chooses justified implementation/architecture | Is “respond within three seconds” a need, or a decision to use three servers? |
| Incremental / iterative | incremental delivers usable slices; iterative revisits/refines; a method can use both | Does the scenario stress staged release, repeated refinement, or both? |
| DFD / flowchart | DFD models data movement/transformation/storage; flowchart expresses control/logic steps | Does the visual need named data flows and stores or program-control branches? |
| ERD / class diagram | ERD models persistent data/keys/relationships; class diagram adds responsibilities/operations/OO relationships | Is the question about stored data structure or behavioural responsibility? |
| `«include»` / `«extend»` | include is required reused behaviour; extend is conditional additional behaviour | Would the base goal still be complete without the added path? |
| Aggregation / composition | aggregation is weak whole-part; composition claims lifecycle-dependent part ownership | Can the part meaningfully exist after the whole is gone? |
| Association / dependency | association is structural link (solid line); dependency is temporary use (dashed arrow) | Does the model need to claim persistent connection or only a use relationship? |
| Sequence / communication | same interaction semantics; sequence emphasizes time, communication emphasizes links/numbering | Can every participant, guard, and order be converted? |
| Activity / state machine | activity models multi-participant workflow; state machine models one object lifecycle | Are we following work across roles or state changes of one object? |

### Revision rule

Do not memorize a diagram name first. State the stakeholder question, the evidence required, and what the model deliberately omits. This discourages drawing a familiar notation where a different model is needed.

---

## 4. Lesson M7.2 — Foundational repair before integrated practice

**Primary source:** C1 pp. 38–39; Weeks 1–5 content.

The final case cannot be coherent if its foundation is defective. Use this repair order:

1. **Scope/purpose/boundary:** identify the system under study, external actors, constraints, and assumptions.
2. **Business need and feasibility:** distinguish feature from value; show economic/schedule work and qualify its assumptions.
3. **Requirements:** give stable IDs and separate FRs, NFRs, interface requirements, and design choices.
4. **DFD:** check noun/verb naming, valid input/output, store/entity/process rules, and level balancing.
5. **ERD:** identify PK/FK/cardinality and resolve M:N with an associative entity when relationship facts need storage.

### Repair example

If `Payment confirmation` is both shown as a DFD process and the name of a class, do not merely rename one item. Decide what it represents in each model: likely a **data flow** in a DFD, a **message/result** in a sequence, perhaps an operation in a service, and not necessarily a persistent class. Record the rationale and keep terms related but distinguishable.

---

## 5. Lesson M7.3 — UML and architecture model clinic

**Primary source:** C1 pp. 39–40; Weeks 7–11 content.

Review an integrated package in this order:

```text
FR / NFR
  → use-case goal and textual scenario
  → class responsibility / operation
  → sequence + communication messages
  → component interface
  → deployed artifact/node/path
  → activity workflow and state rule where appropriate
```

**Accessible text alternative:** A requirement or non-functional constraint should link to a use case and written scenario. The scenario calls named class/service responsibilities. Those responsibilities receive sequence/communication messages and are exposed through component interfaces. Components/artifacts must be plausible on deployment nodes/paths. Activity and state views must agree with scenario conditions and object lifecycle rules.

### Model-clinic checklist

- Does every important use-case step have a responsible receiver/operation?
- Does the class model represent data already required by ERD/requirements without duplicating unrelated attributes?
- Does an `«include»` point from base to required sub-use-case and does an `«extend»` point from conditional extension to base?
- Does a component require/provide a compatible interface?
- Does every needed external integration have a deployment path and stated availability/security/connectivity assumption?
- Do `alt`/activity guards/state guards express the same policy condition with consistent words?
- Are changed names updated through the trace links?

A failed check is useful evidence: label the gap, state an assumption, repair the model, and record why.

---

## 6. Lesson M7.4 — Plan an examination case before drawing

**Primary source:** C1 pp. 40–41; applied assessment workflow.

Read the prompt twice. On the first pass, underline business goal, stakeholders, data nouns, behaviour verbs, constraints, uncertainty, and requested deliverables. On the second pass, build a response plan.

| Planning step | What to write or draw | Avoid |
|---|---|---|
| 1. Scope and assumptions | boundary, actors, definitions, explicit unknowns | inventing policy/facts and presenting them as supplied |
| 2. Requirement extract | numbered FR/NFR/interface statements | calling technical choices requirements without explaining constraint |
| 3. Model order | use case → class/ERD → behavioural scenario → architecture/deployment | drawing disconnected diagrams in arbitrary order |
| 4. Time box | allocate time proportional to marks and reserve validation time | spending all time perfecting one diagram |
| 5. Validation sweep | names, multiplicities, guards, operations, trace links, assumptions | assuming a neat-looking diagram is correct |

### Timed-practice protocol planned for the app

A future timed simulation should: announce duration/sections before start; save answers locally during the session; mark only submitted or auto-submitted responses; provide the learner a review flag; disclose that author-created feedback is not official grading; and reveal subjective guides only after the learner asks. The timed mode must reuse the same reviewed question/item data as untimed practice rather than introduce a lower-quality shadow bank.

---

## 7. Lesson M7.5 — Assemble the final SAD package, not a diagram collection

**Primary source:** C1 pp. 40–41; integrated course artefact spine.

A coherent package presents evidence in a reviewable order:

1. Executive summary: business need, scope, proposed value, major constraints, and stated assumptions.
2. System request/feasibility/project approach: sponsor/need/value, methodology rationale, schedule/risk considerations.
3. Requirements and traceability: SRS extract, IDs, FR/NFR/interface requirements.
4. Process/data analysis: context/levelled DFDs, ERD, key validation notes.
5. Functional/structural OO: use case descriptions, CRC/class/object/component models.
6. Architecture/physical/behavioural design: layers, deployment, normal/alternate sequence, communication conversion, activity, and state model where useful.
7. Consistency record: repaired gaps, open assumptions, risks, and next validation activities.
8. Presentation outline: one problem/value message, selected evidence, limitation/assumption disclosure, and reasoned recommendations.

### Final Package quality rubric preview

| Dimension | Evidence of quality | Common weak pattern |
|---|---|---|
| Scope/source integrity | clear boundary and assumptions; no invented stakeholder quote/policy | plausible but unsupported facts presented as evidence |
| Technical accuracy | valid naming, notation, calculation/model rules, correct relationship/order claims | diagram symbols used decoratively or contradictions hidden |
| Traceability | FR → use case → responsibility/message → component/deployment evidence | individual diagrams look acceptable but do not connect |
| Constraint reasoning | methodology/design/deployment/risk choice tied to stated condition | universal “best” method or architecture claim |
| Communication | legible labels, text alternative, concise rationale, logical structure | unexplained visual complexity or no readable narrative |

This is an author-created learning rubric—not an official INFT 255 marking scheme.

---

## 8. Final Challenge — Integrated registration-and-payment case

**Source label:** Applied example using lecturer-supported registration concepts.
**Scenario status:** Simulated. It does not report real university policy, infrastructure, costs, or stakeholder statements.

> A university wants to reduce registration delays and duplicate enrolments. Students select courses online. The system must check prerequisites and fee-clearance status before recording enrolment. Payment confirmation comes from an external payment capability. The project team has a fixed registration-period deadline, variable student connectivity, and a need to protect student information. Details not given must be labelled as assumptions.

### Challenge tasks

1. State scope, two actors, three explicit assumptions, two FRs, two NFRs, and one interface requirement.
2. Choose and justify a development approach using requirement certainty, deadline, user availability, risk, and feedback needs.
3. Produce a context/Level-0 DFD outline and ERD fragment. Explain one balancing rule and resolve the Student–Course M:N relationship.
4. Produce a use-case description plus class/service responsibilities for `Register for Courses`.
5. Explain normal and alternate payment/prerequisite behaviour in both a sequence and activity outline; convert normal flow to numbered communication messages.
6. Allocate components/artifacts to a plausible deployment outline and state two constraints/assumptions.
7. Run a traceability and consistency sweep. Identify one possible contradiction and a repair.

### Challenge review path

A high-quality answer need not assume a particular cloud provider, payment protocol, institutional approval policy, numerical budget, or precise response-time target. It must instead make assumptions visible, choose a model appropriate to each question, and maintain consistent names/ordering throughout.

---

## 9. Future Module 7 revision, assessment, and capstone interactions

| Interaction | Learner task | Feedback requirement |
|---|---|---|
| Concept bridge sorter | discriminate nine near-neighbour SAD/UML concepts | state the model question and why the rejected term is wrong |
| Foundational repair triage | diagnose a scope/requirement/DFD/ERD defect in a mini-case | identify rule violated and minimal corrected representation |
| UML model-clinic inspector | trace a phrase across use-case/class/component/deployment/behaviour views | expose mismatch/orphan with a repair rationale |
| Case-reading planner | extract actors, nouns, verbs, constraints, unknowns, and requested outputs | distinguish supplied fact from labelled assumption |
| Timebox planner | allocate a stated exam duration/mark split and reserve review | show why a solution needs validation time |
| Topic checkpoint | complete an untimed source-mapped topic set and receive misconception-linked feedback | report evidence by outcome, not simply raw score |
| Mixed revision set | combine calculation, terminology, modelling, and scenario items across modules | recommend a specific prerequisite lesson/model lab for a weak outcome |
| Timed exam simulation | answer a reviewed mixed set with visible timer/review/submit state | disclose author-created, non-official scoring and show feedback after submission |
| Subjective response studio | draft answer first, then choose to reveal model guide/marking criteria | model answers remain hidden until learner request; compare observable elements, not invented facts |
| Final challenge review | assemble and validate an integrated package/plan | award later progress only for demonstrated evidence/repairs, not opening content |

---

## 10. Formative assessment seed — 18 integrated MCQs

| ID | Level | Prompt | Correct answer and explanation | Source |
|---|---|---|---|---|
| M7-Q01 | Remember | Which statement is primarily an analysis requirement rather than a design decision? A Deploy three servers B Use a database trigger C Respond within three seconds for 95% of requests D Use React | **C.** It states a measurable quality need; design chooses how to meet it. | C1 pp. 2–3, 16, 31 |
| M7-Q02 | Remember | The main question answered by an ERD is: A how data is stored/related B which user goal is achieved C which server runs an artifact D which message occurs first | **A.** ERDs model entities, attributes/keys, and relationships. | C1 pp. 18–19 |
| M7-Q03 | Understand | A project releases course search first, then registration, then reporting; each release adds usable scope. This most directly illustrates: A incremental delivery B a DFD level C composition D state transition | **A.** Incremental work delivers functional slices over releases. | C1 pp. 8–11 |
| M7-Q04 | Understand | Why is a DFD not a flowchart? A DFD cannot use nouns B DFD focuses on data movement/transformation/storage, while a flowchart focuses on control/logic sequence C DFD has no processes D flowcharts require actors | **B.** The modelling questions differ. | C1 pp. 17–18 |
| M7-Q05 | Understand | Which statement correctly contrasts a class diagram and ERD? A both only show nodes B a class diagram can show operations/responsibilities; ERD is data/key/relationship-centred C ERD replaces a use case D class diagram must have no attributes | **B.** Their nouns may relate, but their responsibilities differ. | C1 pp. 18–19, 27–29 |
| M7-Q06 | Understand | `Request Override` happens only if normal registration eligibility fails. It should generally: A be included by Register for Courses B extend Register for Courses C compose Register for Courses D be a data store | **B.** Conditional extra behaviour extends the base goal. | C1 pp. 24–26 |
| M7-Q07 | Apply | A `RegistrationService` calls a payment capability for one confirmation request and retains no structural domain link. Best UML relationship: A dependency B composition C aggregation D actor association | **A.** Temporary use is a dependency. | C1 pp. 23–24, 29–30 |
| M7-Q08 | Apply | A part must be destroyed when its owning whole is destroyed under the stated lifecycle rule. Best relationship claim: A association B dependency C composition D realisation | **C.** Composition expresses strong ownership/lifecycle dependence. | C1 pp. 23–24 |
| M7-Q09 | Apply | A sequence diagram shows an eligible payment path. Its communication conversion should preserve: A only object colours B participants, guarded message ordering, and links C database PKs only D screen layout | **B.** The views differ in emphasis but must preserve interaction semantics. | C1 pp. 33–35 |
| M7-Q10 | Apply | A model asks how Student, System, and Payment Gateway work through registration; a separate model asks how one Enrollment changes from Pending to Confirmed. Best pairing: A state then activity B activity then state C ERD then DFD DFD then ERD | **B.** Activity models multi-party workflow; state models one object lifecycle. | C1 pp. 35–37 |
| M7-Q11 | Analyse | A methodology recommendation says only “Agile is best.” What is the principal repair? A add an actor B compare conditions such as requirement certainty, risk, deadline, team/user availability, and feedback needs C draw a DFD D add an FK | **B.** Method selection is a criteria-based trade-off, not a universal label. | C1 pp. 8–11 |
| M7-Q12 | Analyse | A feasibility report shows positive NPV but staff reject the proposed workflow and training is absent. Strongest conclusion? A project is automatically feasible B economic evidence is positive under assumptions, but organisational feasibility needs investigation C delete NPV D it is a class-diagram error | **B.** Economic feasibility does not prove organisational readiness. | C1 pp. 12–15 |
| M7-Q13 | Analyse | A context diagram shows Bank → payment confirmation → System, but the Level-0 DFD omits that flow. What is wrong? A incorrect multiplicity B missing parent/child balancing C missing deployment node D lack of inheritance | **B.** Child decomposition must retain parent boundary inputs/outputs. | C1 pp. 17–18 |
| M7-Q14 | Analyse | Grade is stored on Student, but grade differs for every Course and Semester. Best integrated repair? A put Grade in ENROLLMENT/association entity and check class/ERD consistency B make Grade an actor C remove Course D call it a message | **A.** Grade is relationship-specific data. | C1 pp. 18–19, 27–29 |
| M7-Q15 | Evaluate | FR-05 requires payment confirmation before recording enrolment, but the activity model records first while the sequence orders payment first. Best response? A keep both B investigate, repair ordering, and update trace links C remove FR-05 D replace all diagrams with text | **B.** Contradictions must be resolved transparently. | C1 pp. 33–37 |
| M7-Q16 | Evaluate | A final package has attractive diagrams but no requirement IDs, assumptions, or links between models. Highest-value improvement? A add colours B create traceability and source/assumption record, then repair orphaned artefacts C use more aggregation D omit limitations | **B.** Traceability and transparent assumptions make an integrated package reviewable. | C1 pp. 16–19, 24–37 |
| M7-Q17 | Evaluate | In a 60-minute case question, a learner spends 50 minutes drawing one class diagram and submits no explanation/validation. Best strategy improvement? A remove time limit B timebox deliverables by marks and reserve a validation sweep C write more code D skip assumptions | **B.** A defensible answer needs proportionate coverage and review time. | C1 pp. 40–41 |
| M7-Q18 | Evaluate | A final case omits an external gateway availability assumption while claiming the payment design will always work. Best feedback? A claim is acceptable B state the assumption/constraint, model alternate/recovery behaviour, and qualify the recommendation C add a primary key D call the gateway an internal class | **B.** Uncertain external integration must be treated as an explicit constraint/risk/design condition. | C1 pp. 14–15, 32–37 |

**Cognitive coverage:** remembering 2; understanding 4; applying 4; analysing 4; evaluating 4. These author-created drafts support integrated retrieval/diagnosis; the final bank selection must still remove any cross-module redundancy and independently recheck answer correctness.

---

## 11. Subjective examination-practice seed — four integrated questions

### M7-S01 — Timed final-case plan (12 marks)

**Prompt:** You have 60 minutes to answer an integrated case requesting a scope statement, requirements, use-case/ERD/class/sequence/activity/deployment outlines, and assumptions. Produce a time plan and answer order. Explain how you will protect consistency and what you will do with missing facts.

<details><summary>Reveal model answer and marking guide</summary>

A strong plan reads/extracts the case first; states scope/actors/assumptions; drafts linked requirements; establishes use case plus ERD/class nouns; develops behavioural sequence/activity; allocates deployment only after interfaces/constraints are known; reserves validation time. A defensible allocation might reserve 5–8 minutes for reading/plan, proportionate blocks based on marks, and 8–10 minutes for checking names, multiplicities, guards, ordering, and trace links. Missing facts must be labelled assumptions, not stated as stakeholder evidence. Specific timing can vary if justified.

**Marks:** structured time plan (3); logical model/order rationale (3); cross-model validation plan (3); transparent assumptions/source integrity (2); proportionality to marks (1).
</details>

### M7-S02 — Mixed model-repair case (12 marks)

**Prompt:** A proposed registration package says “the system shall be fast”; its DFD labels `Check Prerequisite` as a data flow; its ERD has direct Student–Course M:N with Grade on Student; its use-case diagram labels `Click Submit`; its sequence creates enrolment before payment confirmation. Identify five defects and propose corrections that keep names consistent.

<details><summary>Reveal model answer and marking guide</summary>

Potential repairs: make performance measurable in a scoped NFR; make `Check Prerequisite` a process and use noun/data label for data flow; add ENROLLMENT associative entity and put relationship-specific Grade there; rename use case to goal-level `Register for Courses`; confirm payment before create/record enrolment or investigate/rewrite requirement if the policy differs. Use the same names, e.g., Enrollment/Payment Confirmation, across SRS/DFD/ERD/use case/sequence. Other accurate identified defects/corrections earn credit.

**Marks:** five correct defect diagnoses (5); technically valid corrections (5); naming/traceability consistency (2).
</details>

### M7-S03 — Final challenge package (15 marks)

**Prompt:** For the simulated registration-and-payment case in this module, provide two FRs, two NFRs, one interface requirement, a methodology rationale, a DFD/ERD outline, and an FR-to-use-case-to-operation-to-interface-to-deployment trace for payment confirmation. State three assumptions.

<details><summary>Reveal model answer and marking guide</summary>

Example FRs: check prerequisites before recording enrolment; record valid enrolment and give confirmation after payment confirmation. NFRs should be measurable/scoped where possible (performance/access/reliability conditions), not vague “secure/fast” claims. Interface requirement: exchange a named confirmation/request with the external payment capability via an agreed interface. Method rationale compares uncertainty/risk/deadline/user feedback instead of declaring an absolute winner. DFD can show Student/Bank boundary flows and Verify/Confirm/Enrol processes; ERD needs STUDENT, COURSE, ENROLLMENT with Student/Course links and relationship facts. Trace: FR-05 → Register for Courses/Confirm Payment step → suitable service operation → required/provided IPayment interface → adapter/artifact/external path. Assumptions must be marked, such as gateway availability rule or specific response target not supplied.

**Marks:** requirements/interface quality (4); methodology rationale (2); valid DFD/ERD outline (3); complete trace path (4); transparent assumptions (2).
</details>

### M7-S04 — Capstone review and presentation (10 marks)

**Prompt:** Design an author-created review checklist and a five-minute presentation outline for an integrated SAD package. Include technical accuracy, traceability, constraint reasoning, communication/accessibility, and one unresolved issue to disclose.

<details><summary>Reveal model answer and marking guide</summary>

A checklist can test boundary/assumptions, FR/NFR testability, DFD balancing, ERD keys/cardinality, goal-level use cases, operation/message ownership, component interfaces, deployment nodes/artifacts/paths, activity/state/sequence consistency, trace links, and accessible labels/text alternatives. Presentation can cover problem/value/scope; selected requirements/models; rationale for methodology/architecture; validation evidence; constraints/assumptions/risk; recommendation/next steps. An unresolved assumption such as external gateway availability or policy for overrides should be disclosed with a validation plan, not hidden.

**Marks:** review checklist breadth and accuracy (4); coherent presentation flow (3); constraint/assumption disclosure (2); accessible communication/limitation clarity (1).
</details>

---

## 12. Phase 4 Module 7 review

### Completed

- Five source-labelled revision/capstone lessons, concept comparisons, repair order, exam-planning method, package rubric, and an explicit simulated final challenge.
- Ten future interaction specifications covering untimed/topic/mixed/timed practice, subjective reveal, model clinic, and capstone validation.
- 18 MCQ drafts and four subjective prompts with hidden/revealable model answers/marking guides.

### Assessment status and limitations

- The course-wide reviewed draft seed is **124 MCQs and 28 subjective prompts** across Modules 1–7. This is above the numeric target but is **not** yet the final app bank: Phase 6 must perform item-level correctness, duplication, source, cognitive-level, answer-explanation, and mode-suitability review before inclusion.
- No official past paper, marking rubric, or answer key was supplied. Model answers/marking guides are author-created and must remain labelled non-official.
- A future timed mode must not be called an official exam; it is an author-created learning simulation.

### Other deferrals

- No interactive assessment sessions, timer, question randomisation, completion scoring, subjective-response storage, competency dashboard, XP/badge reward, persistence/export/import, or final visual/accessibility/link QA is implemented by this content package.
- The final challenge is a simulated teaching case. Its explicit assumptions must not be mistaken for real university information.

## 13. Approval gate

Approve or request changes to Module 7 content. Approval authorises Phase 5 implementation of revision/model-clinic/case-planning interactions in the standalone HTML application. Course-wide assessment modes, dashboard, persistence, resource library, gamification, import/export, and final integration remain later phased work.
