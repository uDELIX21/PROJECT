# Phase 4 — Module 1 Content: Systems Thinking and the Role of SAD

**Course:** INFT 255 — System Analysis & Design
**Module position:** Week 1; prerequisite for every later module
**Status:** Content complete for review. No learner-facing lesson engine, interaction, scoring, or assessment persistence has been implemented in this phase.

---

## 1. Content provenance and scope

| Content label | Primary support | How it is used in this module |
|---|---|---|
| **Lecturer material** | C1 pp. 2–5; L1 pp. 2–27 | Core definitions, system elements/properties/types, analyst roles, constraints, examples and project brief. |
| **Supplementary academic explanation** | None required for the core module | Used only where an explanation clarifies a supplied concept without changing scope. |
| **Standards/legal context** | Ghana Data Protection Act, 2012 (Act 843), verified in Phase 1 | A contextual example of a legal/privacy constraint; not legal advice. |
| **Applied example** | Original teaching scenarios consistent with supplied UENR/hostel/clinic contexts | Used to make concepts observable; clearly marked as illustrative. |
| **Accuracy note** | Phase 1 source-integrity review | Corrects overgeneralisation: a machine is not automatically non-adaptive; classification depends on stated behaviour and context. |

### Module outcome

By the end of Module 1, a learner should be able to describe a system purposefully, locate its boundary and environment, identify inputs/processes/outputs/feedback/controls, distinguish analysis from design, identify constraints and system properties, classify systems with justification, and assign basic SAD roles to a project.

### Required prior knowledge

None. Learners need only familiarity with an everyday service (course registration, hostel booking, clinic appointment, mobile-money service, library lending, etc.).

### Evidence that unlocks Module 2

1. A concise system description with stated purpose and users.
2. An IPO-feedback-control-boundary map with a written rationale.
3. Six relevant constraints and at least one design implication.
4. A short explanation distinguishing analysis from design in the learner’s own case.

---

## 2. Lesson M1.1 — What makes something a system?

**Estimated guided-study time:** 18 minutes
**Primary source:** Lecturer material — C1 p. 2; L1 pp. 7, 14–15
**Core terms:** system, information system, component, goal, input, process, output.

### Learning objectives

- Define a system as interrelated components organised to achieve a purpose.
- Explain why a list of unrelated things is not necessarily a system.
- Identify inputs, a transformation process, and outputs in a familiar service.
- Distinguish a general system from an information system.

### Explanation from first principles

A **system** is not simply a collection of parts. Its parts are connected in an organised way and contribute to a shared purpose. A university, a registration service, a clinic, and a payroll service can all be viewed as systems because each has components that interact to produce outcomes.

A useful first question is therefore not “What technology is used?” but **“What purpose does this system achieve?”** Purpose guides the analyst’s choice of relevant components. For a course-registration system, the purpose is not “to contain a database.” It is to support valid course enrolment and produce reliable records for students, lecturers, and the institution.

A simplified system cycle is:

```text
Input → Process / transformation → Output
```

- **Input** is the data, material, request, or event entering the system.
- **Process** changes input into a more useful result.
- **Output** is the result delivered to a user, another system, or the environment.

An **information system (IS)** collects, processes, stores, and distributes data/information to support operations, management, and decision-making. A paper registration form can be part of an information system; an IS does not mean “a web app only.”

### Lecturer-supported worked example — online course registration

| System element | Example |
|---|---|
| Purpose | Enrol eligible students in valid courses and maintain reliable enrolment records. |
| Inputs | Student ID, selected courses, semester, payment evidence. |
| Process | Verify identity, prerequisites, credit load, and fee clearance; create enrolment. |
| Outputs | Registration slip, updated record, class list. |
| Storage | Student records, course offerings, payment/enrolment records. |

### Applied example — clinic appointment service

> **Applied example:** A clinic receives an appointment request (input), checks practitioner availability and patient details (process), and sends an appointment confirmation or alternative slot (output). The system may be partly manual, partly digital, or fully digital; the systems-thinking analysis remains useful in all three cases.

### Common misconceptions

| Misconception | Correction |
|---|---|
| “A system is always software.” | A system may be manual, technical, social, or a human-machine combination. An information system can include people, rules, forms, and technology. |
| “Every item connected to an organisation belongs to the system.” | The analyst decides a boundary based on the purpose being studied. Some connected actors/systems remain in the environment. |
| “Output is whatever appears on a screen.” | Outputs can be records, confirmations, reports, decisions, services, notifications, or a physical change. |

### Micro-practice

For a hostel-booking system, label each item as input, process, or output:

1. A student submits preferred dates and room type.
2. The system checks availability and reserves a room.
3. The student receives a booking reference.

**Answer with reasoning:** 1 is input; 2 is process; 3 is output. The distinction is based on the item’s role in the transformation, not on whether it is digital.

### Exam-writing pattern

When asked “What is a system?”, use a three-part answer:

1. State the definition: interrelated components organised for a common purpose.
2. Name the transformation: it accepts inputs and produces outputs through a process.
3. Give a case-specific example with one input/process/output chain.

---

## 3. Lesson M1.2 — Boundary, environment, control, and feedback

**Estimated guided-study time:** 22 minutes
**Primary source:** Lecturer material — C1 pp. 2–3; L1 pp. 13, 16–19
**Core terms:** boundary, environment, interface, control, feedback, subsystem.

### Learning objectives

- Define and place a system boundary for a stated analysis purpose.
- Distinguish the environment from an internal subsystem.
- Explain the different jobs of control and feedback.
- Identify a feedback loop in a service scenario.

### Explanation

A system boundary is a purposeful analytic line. It identifies what is inside the system currently being studied and what is outside it. The boundary does **not** claim that outside actors are irrelevant; they may constrain or exchange data with the system. It simply helps the analyst control the scope of the model.

The **environment** includes external actors, organisations, regulations, technologies, conditions, and systems that influence the studied system or receive its outputs. An **interface** is the point where systems or components interact across a boundary.

**Control** guides or constrains how the system operates. Examples include academic regulations, authorisation rules, credit limits, and required validation checks. It is a rule or decision mechanism that shapes the process.

**Feedback** is information about system performance or results that is returned so the system can be adjusted or corrected. A lecturer reporting that a registered student is missing from a class list is feedback: it reveals a result that may require correction. A registration slip sent to a student is normally an output, not feedback, unless the learner’s response is used to adjust operation.

### Lecturer-supported case map — course registration

```text
Outside / environment: Students, lecturers, bank, education requirements
             │
             │ requests, payment confirmation, reports
             ▼
+-------------------------------------------------------------+
| Registration System boundary                                |
|                                                             |
| Inputs → validation and enrolment processes → outputs       |
|          ↑                         │                        |
|          │                         └── class lists/slips    |
| Controls: prerequisites, fee rules, credit limits            |
| Feedback: lecturer reports missing class-list student        |
+-------------------------------------------------------------+
```

**Accessible linear description:** Students and a bank are external. They send registration and payment information across the boundary. Inside, the system validates and enrols. It produces slips and class lists. Academic rules control the validation. A lecturer can report a missing class-list entry, producing feedback that triggers a correction.

### Boundary decision activity

**Question:** Is the bank inside or outside the registration system?

**Reasoned answer:** Usually outside if the studied system is the university registration application. The bank is an external system that sends payment confirmation through an interface. If the project were instead analysing a combined university-and-bank payment platform, the boundary might be drawn differently. Boundaries depend on the stated purpose and scope.

### Common misconceptions

| Misconception | Correction |
|---|---|
| “Environment means the physical room where computers are located.” | Environment includes relevant external people, systems, policies, competition, legal requirements, and conditions — not only physical surroundings. |
| “Control and feedback are synonyms.” | Control sets/guides acceptable operation; feedback reports a result/performance condition so control or processing can respond. |
| “A subsystem is outside the system.” | A subsystem is an internal smaller system within the chosen boundary, such as Fees or Results within a Student Information System. |
| “The boundary is fixed forever.” | A boundary is selected for a specific analysis purpose. It must be stated consistently, but a different study can legitimately use a different scope. |

### Knowledge check

A hostel manager reports that the system confirmed a room that was already marked unavailable. This report is best classified as:

- A. Input
- B. Control
- C. Feedback
- D. Boundary

**Correct answer: C — feedback.** It reports an outcome/performance problem that should trigger investigation or correction. The occupancy rule itself is a control.

---

## 4. Lesson M1.3 — Analysis asks “what”; design asks “how”

**Estimated guided-study time:** 20 minutes
**Primary source:** Lecturer material — C1 pp. 2–4; L1 pp. 2–6
**Core terms:** system analysis, system design, requirements, technical solution, stakeholder, value.

### Learning objectives

- Distinguish the purpose, primary question, activities, and outputs of analysis and design.
- Detect premature technical design in a requirement statement.
- Explain why a technically impressive system can still fail.
- Place a sample activity/output in analysis or design.

### Explanation

**System analysis** studies an existing or proposed system to understand its purpose, problems, stakeholders, and requirements. Its central concern is **what the system must do** and in what context. It asks who uses it, what data/actions are needed, where and when it operates, what problems exist, and what constraints matter.

**System design** uses analysis results to decide **how the system will work**. It considers architecture, database structure, interfaces, programs/classes, hardware, security mechanisms, deployment, and technology choices.

The distinction is not a claim that activities never inform each other. It protects the project from deciding a technology before it understands the problem. If an analyst begins with “we need a mobile app,” they may overlook whether users need offline capability, whether a process is unnecessary, or whether a policy change would solve the actual problem.

| Dimension | System analysis | System design |
|---|---|---|
| Main question | What must the system do, and why? | How will the solution achieve it? |
| Focus | business problem, users, requirements, current/future work | technical/operational solution |
| Typical activities | interview, observe, model requirements and problem domain | architecture, database/UI/component/deployment design |
| Typical outputs | SRS, use cases, DFDs, problem-domain class model | system specification, screens, design class/sequence/deployment models |
| Key audience | users, sponsor, business stakeholders | programmers and technical team, alongside stakeholders |

### Example: separate a requirement from a design choice

| Statement | Classification | Why |
|---|---|---|
| “A student must be prevented from registering without the required prerequisite.” | Analysis requirement | States needed behaviour, not implementation. |
| “The system will use a PostgreSQL trigger to enforce prerequisites.” | Design choice | Specifies one possible technical mechanism. |
| “The registration page should respond within three seconds for 95% of requests.” | Non-functional requirement | States an observable quality target; design will determine how to meet it. |
| “Deploy three cloud servers.” | Design / deployment choice | Specifies a solution architecture. |

### Why value matters

C1 emphasises that an analyst’s purpose is to create organisational value, not merely a technically “wonderful” system. A fast and secure system can still be rejected if it conflicts with staff work, does not solve the priority problem, is unaffordable, excludes users, or violates policy. This is why the course later connects requirements, organisational feasibility, change management, and user involvement.

### Applied exercise — correct premature design

Rewrite this statement as an analysis requirement:

> “Build an Android app with facial recognition and a MongoDB database so patients can book appointments.”

**One strong rewrite:** “Patients must be able to request, view, change, or cancel appointments through a service accessible on their available devices. The service must protect patient information and show available appointment slots.”

The rewrite keeps the required capability and constraints. It does not assume a particular operating system, biometric method, or database.

### Common misconceptions

- **“Analysis contains no models.”** Analysis uses models such as DFDs, ERDs, use cases, and analysis class diagrams to understand and communicate requirements.
- **“Design means visual screen design only.”** Interface design is one part; architecture, components, data storage, deployment, security, and performance decisions are also design.
- **“What and how can never overlap.”** They influence one another, especially under constraints. The teaching distinction identifies the primary intent and decision level.

---

## 5. Lesson M1.4 — Constraints, properties, and classification

**Estimated guided-study time:** 26 minutes
**Primary source:** Lecturer material — C1 pp. 3–4; L1 pp. 8, 10–12, 20–27
**Core terms:** constraint, organisation, interaction, interdependence, integration, central objective, adaptability, deterministic, probabilistic, open, closed.

### Learning objectives

- Identify a constraint and explain its effect on solution choices.
- Explain key system properties using a relevant example.
- Classify a system on more than one dimension and justify the choice.
- Avoid treating system categories as absolute labels where context matters.

### Constraints: limits that shape feasible solutions

A **constraint** is a limit within which a system must be built or operated. It does not tell the whole story of what the system should do; it limits the acceptable solution space.

| Constraint category | Question to ask | Registration-system example | Design implication |
|---|---|---|---|
| Budget / cost | What resources can be spent? | The faculty has a limited project budget. | Prioritise essential capability and avoid unsupported tooling. |
| Time / schedule | What deadline cannot move? | Must be ready before registration opens. | Sequence work, protect critical tasks, manage scope. |
| Technology | What existing devices, networks, skills, or integrations exist? | Learners may use low-end devices and unreliable connectivity. | Design for small screens, low bandwidth, and recovery where appropriate. |
| Legal / regulatory | What laws or rules govern operation? | Personal student data is handled. | Treat privacy/data-handling obligations as requirements/constraints. |
| Organisational / policy | What approval rules or work practices apply? | Only authorised staff may approve late registration. | Model role-based responsibility and authorisation. |
| Human / skills | What training, capacity, and willingness are available? | Clerks have varied IT experience. | Make workflows learnable; plan training/support. |
| Quality / performance | What measurable quality is required? | Many students may register in a short period. | Define response/capacity expectations before architecture choices. |

> **Standards/legal context:** The supplied notes use Ghana’s Data Protection Act, 2012 (Act 843) as a legal-constraint example. This module uses it only to illustrate why personal-data handling belongs in system constraints; it does not give legal advice or assert a complete compliance interpretation.

### System properties

- **Organisation:** components have a structure/order, for example registration, fee clearance, and results functions.
- **Interaction:** components exchange data or services; the registration service interacts with payment confirmation.
- **Interdependence:** one component’s result is required by another. A failure in fee status may block valid enrolment.
- **Integration:** components act together toward the overall purpose rather than as unrelated tools.
- **Central objective:** the system’s purpose guides decisions and prevents local optimisations that harm overall value.
- **Boundary and environment:** distinguish what is studied internally from external influences/interactions.
- **Adaptability:** the capability to respond meaningfully to relevant environmental change.

### Classification is an argument, not a memorisation trick

A system can be classified along several independent dimensions:

| Dimension | Categories | Careful example / explanation |
|---|---|---|
| Origin | natural / man-made | ecosystem / payroll system |
| Openness | open / relatively closed | online shop exchanges information with its environment; completely closed systems are rare in practice |
| Predictability | deterministic / probabilistic | a fixed payroll calculation can be deterministic given correct inputs/rules; weather prediction is probabilistic |
| Physical nature | physical / abstract | network hardware / a process model or formula |
| Organisational function | TPS, MIS, DSS, ESS, expert system | POS transaction processing; management report; pricing “what-if” analysis |
| Adaptation | adaptive / non-adaptive | state the feedback/learning mechanism before assigning this label |

> **Accuracy note:** L1 gives “machines” as examples of non-adaptive systems. This must not be taught as a universal rule. A thermostat, control system, or ML-enabled service may adapt to feedback under a meaningful definition. State the behaviour and the classification criterion.

### Classification activity

Classify a university registration service in at least three ways and justify each:

- **Man-made:** it is designed and operated by people/organisations.
- **Open:** it exchanges information with students, banks, lecturers, and regulations in its environment.
- **Human-machine system:** people use and administer the service while technical components process/store information.
- **Mostly deterministic in specific validation rules:** given reliable records and fixed rules, prerequisite/credit checks should reach consistent results; this does not mean every operational outcome is certain.

---

## 6. Lesson M1.5 — Analyst roles, skills, and value

**Estimated guided-study time:** 18 minutes
**Primary source:** Lecturer material — C1 pp. 4–5; L2 pp. 33–37
**Core terms:** business analyst, systems analyst, infrastructure analyst, change-management analyst, project manager, stakeholder, value, ethics.

### Learning objectives

- Match common SAD project roles to responsibilities.
- Explain why technical, business, interpersonal, and ethical skills are all necessary.
- Identify when a role should involve a stakeholder.
- Explain why user fit and organisational value matter to success.

### Role map

| Role | Main contribution | Example question for a registration project |
|---|---|---|
| Business analyst | Clarifies business value, processes, policies, and stakeholder needs. | Which registration delays cost time or cause errors, and why do they matter? |
| Systems analyst | Connects process/requirements to an information-system solution; models the system and standards. | What information and rules must the registration service support? |
| Infrastructure analyst | Assesses hardware, networks, platform/integration standards. | Can expected users connect reliably and can the service integrate with payment? |
| Change-management analyst | Plans user transition, communication, training, and adoption support. | Who will change their work and what training/communication is needed? |
| Project manager | Coordinates scope, people, schedule, budget, risks, and communication. | What work is critical, who owns it, and which risks threaten the deadline? |

Small projects may have one person doing several roles. That does not remove the responsibilities; it makes omissions more likely unless the team addresses them deliberately.

### Skill set

- **Analytical:** separate symptoms from causes; compare options; recognise dependencies.
- **Technical:** understand capabilities/limits sufficiently to ask sound questions and create feasible specifications.
- **Business:** relate system features to organisational objectives and policies.
- **Interpersonal/communication:** listen, facilitate, negotiate, explain models, resolve conflict, and make assumptions visible.
- **Management:** plan, monitor, prioritise, manage change and risk.
- **Ethical:** handle information responsibly, represent evidence honestly, respect affected users, and avoid misrepresenting a model as validated when it is not.

### Scenario: technically strong, organisationally weak

A team delivers an application that technically automates results processing. It requires lecturers to export data in a format none of their existing tools produce, provides no training, and releases during the busiest marking period. The database is reliable, but lecturers return to spreadsheets.

**Analysis:** the failure is not necessarily technical. The design failed to fit work practices, change readiness, timing, and user support. This illustrates why analyst roles and organisational feasibility matter.

### Practical activity — project charter seed

For the chosen Case Studio context, write:

1. Purpose in one sentence.
2. Primary users and external stakeholders.
3. A provisional boundary/environment statement.
4. Six constraints, including at least one organisational or legal/privacy constraint.
5. A role/responsibility table for a five-person group.

**Self-check:** Does every constraint state a limit and an effect? Does every role have a distinct responsibility? Are user and sponsor concerns visible, not assumed?

---

## 7. Module visual and interaction inventory for later implementation

The following content objects are ready to be implemented only after Module 1 content is approved. They are not falsely described as functional features in this phase.

| Object | Learning purpose | Accessible equivalent |
|---|---|---|
| System boundary explorer | Drag/select candidate elements inside/outside a stated system boundary and explain scope. | Ordered element list with inside/outside controls and rationale field. |
| IPO-feedback/control mapper | Place supplied case statements in input/process/output/feedback/control slots. | Keyboard-selectable labelled rows. |
| Analysis vs design sorter | Categorise statements, then revise premature design assumptions. | Button list with explanation panel. |
| Constraint impact matrix | Pair a constraint with affected requirement/design consequence. | Table/radio selection with text feedback. |
| Classification debate cards | Choose and defend several classifications for the same system. | Text prompt, selectable labels, rationale reveal. |
| Role hand-off scenario | Match project concerns to roles and identify missing responsibility. | Selectable role table with written feedback. |

---

## 8. Formative assessment seed — 16 non-repetitive MCQs

These questions are module-specific drafts for later Phase 6 review and implementation. They have reasoning feedback now, but they are not yet in a functional assessment engine and are not lecturer-approved answer keys.

| ID | Cognitive level | Question and options | Correct answer and explanation | Source basis |
|---|---|---|---|---|
| M1-Q01 | Remember | Which statement best defines a system? A. Any collection of computer hardware. B. Interrelated components organised to achieve a common objective. C. A database that stores records. D. A program written in one language. | **B.** A system is purposeful and its components are related. Software/database may be components, but neither alone defines every system. | C1 p. 2; L1 p. 7 |
| M1-Q02 | Understand | In a course-registration service, a student’s selected courses are best described as: A. output B. control C. input D. feedback | **C.** Course selections enter the system to be processed, so they are input. | C1 p. 2; L1 p. 14 |
| M1-Q03 | Apply | Which item is the clearest process in an appointment-booking system? A. Appointment confirmation B. Patient details C. Check practitioner availability D. Clinic records | **C.** A process transforms information and is named as an action. The other options are output/input/data store. | C1 p. 2; applied example |
| M1-Q04 | Understand | A lecturer reports that an enrolled student is missing from a class list. In systems terms, this report is primarily: A. feedback B. a boundary C. an input to enrolment D. an output | **A.** It reports a result/performance condition so the system can be corrected; that is feedback. | C1 p. 2; L1 p. 17 |
| M1-Q05 | Apply | For a university registration application, which is most reasonably outside the system boundary when the study focuses on the university’s own registration software? A. Enrolment validation rule B. Course-offering record C. External bank payment gateway D. Registration slip generator | **C.** The bank gateway is an external system that interacts through an interface. Boundaries depend on the defined study scope. | C1 p. 2; L1 pp. 18–19 |
| M1-Q06 | Analyse | Which pairing correctly distinguishes a control from feedback? A. Credit limit = feedback; lecturer’s missing-name report = control. B. Credit limit = control; lecturer’s missing-name report = feedback. C. Both are outputs. D. Both are boundaries. | **B.** The credit limit guides valid behaviour; the report provides information about a result that may trigger correction. | C1 pp. 2–3; L1 pp. 16–17 |
| M1-Q07 | Remember | “The service must be available before September registration opens” is primarily a: A. schedule constraint B. physical system type C. feedback loop D. data output | **A.** It sets a time/deadline limit on the work and operation. | C1 p. 3 |
| M1-Q08 | Apply | A requirement that only authorised registrar staff can approve late registration is most directly shaped by which constraint category? A. organisational/policy B. natural origin C. feedback D. probabilistic behaviour | **A.** It expresses an institutional rule about authority and process. | C1 p. 3 |
| M1-Q09 | Understand | When the fee-clearance subsystem’s result is required before enrolment can be completed, this most clearly demonstrates: A. interdependence B. physicality C. closedness D. annotation | **A.** One subsystem’s output is required by another, so they are interdependent. | C1 p. 3; L1 p. 11 |
| M1-Q10 | Analyse | A team states, “The system is open because students, banks, and lecturers exchange information with it.” What is the strongest evaluation? A. Correct; interaction with external entities is evidence of openness. B. Incorrect; only hardware can be open. C. Incorrect; all online systems are closed. D. Correct only if it has no database. | **A.** An open system interacts with its environment; the stated exchanges are relevant evidence. | C1 p. 4; L1 p. 22 |
| M1-Q11 | Understand | Why should “machines” not automatically be classified as non-adaptive systems? A. Machines cannot have objectives. B. Some engineered systems respond to feedback or changed conditions. C. Only natural systems use inputs. D. Classification never needs justification. | **B.** Adaptability depends on the behaviour/criterion, not merely whether something is a machine. | Accuracy note based on L1 p. 23 |
| M1-Q12 | Apply | Which statement is an analysis requirement rather than a design decision? A. Use a PostgreSQL trigger for prerequisites. B. Deploy three cloud servers. C. Prevent enrolment when a prerequisite has not been passed. D. Build an Android application. | **C.** It states required behaviour without choosing a technical mechanism. | C1 pp. 2–3 |
| M1-Q13 | Analyse | A project produces a fast, secure application, but staff cannot fit it into their approved work process and users receive no training. Which conclusion is strongest? A. It cannot be a failure because it is technically sound. B. It may fail organisationally despite technical quality. C. Training is part of coding only. D. The issue is a system boundary. | **B.** Value, organisational fit, adoption, and change support are part of systems success. | C1 pp. 3–4; L2 pp. 34–35 |
| M1-Q14 | Remember | Which role focuses most directly on planning user training and adoption support? A. Infrastructure analyst B. Change-management analyst C. Database administrator only D. External actor | **B.** The change-management analyst develops and executes change/training planning. | C1 p. 4; L2 p. 35 |
| M1-Q15 | Evaluate | A learner calls a weather forecast “deterministic” because it uses computer calculations. Which response is best? A. Correct; all computation is deterministic. B. Incorrect; a forecast concerns uncertain outcomes even if calculations are systematic. C. Correct; weather has no inputs. D. Incorrect; only physical systems can be deterministic. | **B.** The classification concerns predictability/certainty of outcomes, not whether a computer is used. | C1 p. 4; L1 p. 26 |
| M1-Q16 | Apply | Which project statement best links a constraint to a likely design implication? A. “The project has a budget, so it is an open system.” B. “Low-end phones and unreliable connectivity mean the solution must consider small-screen and recovery needs.” C. “Students are inputs, so they must be stored as data stores.” D. “A report is feedback, so no validation is needed.” | **B.** It connects a technology/context constraint to an appropriate solution consideration without prematurely fixing a tool. | C1 p. 3; applied explanation |

### Assessment distribution check

- Remember: 3 items
- Understand: 4 items
- Apply: 5 items
- Analyse: 3 items
- Evaluate: 1 item

Items intentionally overlap in complexity where an applied or analytic response also requires recall. The later course-wide bank will rebalance totals across modules; Module 1 alone is not counted as satisfying the 100-MCQ requirement.

---

## 9. Subjective / examination-practice seed — four questions

Model answers and mark guides are written for future reveal-on-demand behaviour. They are not displayed to a learner by default in a future assessment implementation.

### M1-S01 — System map (8 marks)

**Prompt:** A university exams office receives marks from lecturers, checks them, produces student results, and responds when a lecturer reports a missing or incorrect result. For this results-processing system, identify one input, one process, one output, one control, one feedback item, and one boundary/environment distinction. Briefly justify each.

<details>
<summary>Reveal model answer and marking guide</summary>

**Model answer:** Input: lecturer marks submission. Process: validate/compile marks and calculate results. Output: published result or student transcript. Control: academic grading rules/authorisation policy. Feedback: lecturer report of missing/incorrect result, used to investigate/correct. Boundary: results-processing office/software is inside the studied system; lecturers and students are external actors in the environment, although they interact with it.

**Mark guide:** 1 mark each for six correctly identified items (6); 1 mark for a correct boundary/environment distinction; 1 mark for a coherent justification that differentiates control from feedback or input from output.

**Common loss of marks:** calling the policy “feedback”; labelling an external actor as a data input rather than describing the data they supply.
</details>

### M1-S02 — Analysis versus design (6 marks)

**Prompt:** Classify each statement as analysis/requirement or design choice, then justify: (i) “The service shall confirm a booking only if a room is available.” (ii) “The service will use a cloud-hosted relational database.” (iii) “The system shall show a response within three seconds for most booking requests.” (iv) “The user interface will have a green confirmation button.”

<details>
<summary>Reveal model answer and marking guide</summary>

**Model answer:** (i) analysis/functional requirement: required behaviour. (ii) design choice: implementation/storage architecture. (iii) analysis/non-functional requirement: measurable quality outcome; design decides how it is met. (iv) design choice: a specific interface presentation decision.

**Mark guide:** 1 mark for each correct classification (4); 2 marks for justification that correctly separates required outcome from technical/interface mechanism.

**Common loss of marks:** calling every statement with the word “system” an analysis requirement.
</details>

### M1-S03 — Constraints and value (8 marks)

**Prompt:** A campus hostel-booking project must go live in six weeks, will be used over inconsistent mobile connectivity, handles student identity data, and has staff who have never used a booking system. Identify four constraint categories and give one likely implication for each. Explain why a technically working solution might still fail in this setting.

<details>
<summary>Reveal model answer and marking guide</summary>

**Model answer:** Schedule: six-week deadline, requiring prioritised scope and critical-path control. Technology: inconsistent connectivity, requiring tolerance/recovery/low-bandwidth consideration. Legal/privacy: identity data, requiring lawful/responsible handling and access controls. Human/skills: inexperienced staff, requiring usable workflow, training, and support. A technically working system can fail if staff cannot adopt it, user needs/work practices are not supported, or privacy/operational constraints are ignored.

**Mark guide:** 1 mark for each valid category (4); 1 mark for each suitable implication (up to 3); 1 mark for a clear organisational-value/adoption explanation.

**Common loss of marks:** listing four technical features rather than four constraints; assuming the legal example is a complete legal compliance analysis.
</details>

### M1-S04 — Classification with justification (6 marks)

**Prompt:** Classify a mobile-money agent management service by origin, openness, and organisational/system role. Then state one reason the label “non-adaptive machine system” may be too simple.

<details>
<summary>Reveal model answer and marking guide</summary>

**Model answer:** Origin: man-made. Openness: open, because it exchanges information with customers, agents, payment networks, supervisors, and policies. Organisational role: likely transaction processing for individual agent/customer transactions; it may also support management information through reports. “Non-adaptive machine system” may be too simple because the service includes people and may respond to feedback/rules/conditions; classification depends on the stated system and adaptation definition.

**Mark guide:** 1 mark each for origin, openness, and organisational-role classification (3); 1 mark each for justified reasoning (2); 1 mark for the nuanced adaptive/human-machine observation.

**Common loss of marks:** treating all digital systems as closed or calling an agent/customer a software subsystem without stated scope.
</details>

---

## 10. Module 1 content review

### Completed

- Five complete, source-labelled lessons with definitions, first-principles explanations, lecturer-supported examples, applied examples, misconceptions, practice, and examination patterns.
- Original text diagram specification with accessible linear description for later implementation.
- One practical Case Studio activity and self-check criteria.
- Six future interaction specifications tied to actual M1 learning objectives.
- Sixteen non-repetitive MCQ drafts with explanations and cognitive-level coverage.
- Four subjective examination-practice prompts with hidden/revealable model answers and marking guides.

### Limitations / deliberate deferrals

- The 16 MCQs and four subjective prompts do **not** satisfy the eventual 100-MCQ/20-subjective course target; they form the reviewed Module 1 seed only.
- The questions have not been placed in an app, scored through an assessment engine, or reviewed by a course lecturer. They must not be called official.
- No Model Lab or Case Studio interaction is implemented yet. The prototype contains only a representative visual DFD interaction from Phase 3, not a content-complete Module 1 activity.
- M2 onward content will be developed only after this Module 1 content receives review.

## 11. Phase 5 approval gate

Review Module 1 content for accuracy, depth, case relevance, terminology, and assessment style. Once approved, Phase 5 will implement and test the first **meaningful Module 1 interactions** progressively (system-boundary explorer, IPO/feedback/control mapper, analysis-vs-design sorter, constraint matrix, classification cards, and role scenario) before expanding the next module’s content.
