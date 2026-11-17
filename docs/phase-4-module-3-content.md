# Phase 4 — Module 3 Content: Project Initiation, Feasibility, Scheduling, and Risk Management

**Course:** INFT 255 — System Analysis & Design
**Module position:** Week 4; applies Module 1 constraints and Module 2 lifecycle/method choice
**Status:** Content complete for review. Calculation/model simulations, durable assessment sessions, and project persistence are not yet implemented.

---

## 1. Source boundaries and outcomes

| Label | Source | Use in this module |
|---|---|---|
| Lecturer material | C1 pp. 12–15; L4 pp. 1–34 | system request, feasibility, ROI/payback/NPV, WBS/Gantt/CPM, estimation, staffing, risks and responses. |
| Supplementary academic explanation | CMU SEI *Continuous Risk Management Guidebook*; NISTIR 7499 | continuous risk practice and structured lifecycle planning context. |
| Standards/legal context | Ghana Act 843 only as a privacy-constraint example | illustrates a legal/privacy consideration, not legal advice. |
| Accuracy note | Phase 1 source review | unify L4’s overlapping risk terms into the transparent four-step cycle: identify → analyse → response-plan → monitor/control. |

### Module outcome

Learners can write a system request, distinguish technical/economic/organisational feasibility, calculate and interpret simple ROI/payback/NPV, build dependency-aware schedules, identify critical path/slack, create a prioritised risk register, and justify a response rather than merely naming one.

### Required artefacts

- System request and feasibility snapshot.
- ROI/payback/NPV working sheet.
- WBS with owners, durations, dependencies, and deliverables.
- Network/Gantt interpretation with critical path and slack.
- Risk register with probability, impact, response, trigger, owner, and contingency.

---

## 2. Lesson M3.1 — Turn a need into a system request and feasibility question

**Primary source:** C1 p. 12; L4 pp. 3–9
**Key terms:** sponsor, business need, business value, special issues, technical feasibility, economic feasibility, organisational feasibility.

A project begins when a stakeholder identifies an opportunity or problem, not when a team chooses a technology. The **system request** records the early case for work:

| Element | What it should make visible |
|---|---|
| Sponsor | person/role who champions or authorises the work |
| Business need | observable problem/opportunity rather than a preferred technology |
| Business requirements | high-level capability/value needed |
| Business value | tangible outcomes (cost/time/revenue) and intangible outcomes (trust/satisfaction/image) |
| Special issues | deadlines, regulations, policy, risk, integrations, constraints |

**Feasibility asks “Should we do this?”**

- **Technical feasibility:** Can the organisation build/acquire and integrate it with available technology, skills, scale, and existing systems?
- **Economic feasibility:** Are expected benefits likely to justify development/operating costs and timing of cash flows?
- **Organisational feasibility:** Does the work align with strategy, have sponsor/user support, and fit the people/processes expected to use it?

A project can be technically feasible but organisationally weak; it can have positive financial indicators but lack staffing/management support. Feasibility is a decision aid, not a promise of project success.

### Applied request repair

Weak: “Buy an expensive hostel system.”

Improved: “The hostel manager reports duplicate bookings, delayed confirmations, and difficulty producing an auditable room-allocation record. The proposed project should support student requests, staff availability checks, and reliable confirmations before the next allocation period. The sponsor is the hostel manager; special issues include allocation timing, privacy of student details, staff training, and inconsistent connectivity.”

---

## 3. Lesson M3.2 — Economic feasibility: calculate, then interpret

**Primary source:** C1 pp. 12–13
**Key terms:** cost-benefit analysis, net cash flow, ROI, payback, discount rate, present value, NPV.

### Core measures

| Measure | Course formula / meaning | Interpretation caution |
|---|---|---|
| ROI | `(total benefits − total costs) ÷ total costs` | compares net gain to cost over a stated horizon; show assumptions/horizon. |
| Payback | point/year when cumulative net benefits recover initial cost | a shorter payback can be attractive but ignores later benefits and time value unless extended. |
| NPV | sum of discounted future net cash flows minus initial cost | positive NPV under the stated rate/horizon suggests economic attractiveness; it is not certainty. |

### Lecturer-supported registration example

Development cost is GH₵80,000 in Year 0. Operating cost is GH₵10,000/year. Benefits are GH₵50,000/year for three years. Net cash flow is therefore −80,000 in Year 0 and +40,000 in Years 1–3.

At a 10% discount rate, supplied notes show approximate present values of +36,364, +33,058, and +30,052 for Years 1–3. Their total is 99,474, so NPV is 99,474 − 80,000 = **GH₵19,474**. Payback is 80,000 ÷ 40,000 = **2 years**. Total benefits are 150,000 and total costs are 110,000, so ROI is `(150,000 − 110,000) ÷ 110,000 = 36.4%`.

### Common errors

- Adding gross benefits rather than **net** cash flows when a question supplies operating cost separately.
- Treating positive NPV as proof that users will adopt the system; organisational feasibility is still separate.
- Forgetting that payback uses cumulative recovery and that some costs/benefits may occur later.
- Hiding assumptions about horizon, benefit estimate, and discount rate.

---

## 4. Lesson M3.3 — Make time/dependencies visible: WBS, Gantt, network, critical path

**Primary source:** C1 p. 13; L4 pp. 6–9
**Key terms:** WBS, dependency, duration, Gantt chart, network diagram, PERT/CPM, critical path, slack/float.

A **work breakdown structure (WBS)** is a hierarchical decomposition of project work. A usable task entry states an owner, duration, deliverable, and predecessor/dependency. It makes hidden work—reviews, testing, migration, training, support preparation—visible.

A **Gantt chart** shows tasks across calendar time and makes schedule/progress legible. It is weaker at revealing complex dependency logic. A **network diagram** makes predecessors and alternative paths visible.

The **critical path** is the longest-duration dependency path from start to finish. A delay to a critical-path task delays the completion date unless another change offsets it. **Slack** is how long a non-critical task may slip without changing the project end date.

### Worked course example

| ID | Task | Days | Depends on |
|---|---|---:|---|
| A | Gather requirements | 3 | — |
| B | Design database | 4 | A |
| C | Design user interface | 2 | A |
| D | Write code | 5 | B, C |
| E | Test system | 2 | D |

Paths: A→B→D→E = `3 + 4 + 5 + 2 = 14` days. A→C→D→E = `3 + 2 + 5 + 2 = 12` days. The critical path is A→B→D→E. Task C has 2 days slack under these assumptions.

### Applied challenge

If Task C changes from 2 to 6 days, path A→C→D→E becomes 16 days. It is now longer than A→B→D→E and becomes critical. The earliest possible project finish becomes 16 days, assuming all other conditions remain unchanged.

---

## 5. Lesson M3.4 — Estimates, scope, staffing, and monitoring are connected

**Primary source:** C1 pp. 14–15; L4 pp. 4–9
**Key terms:** analogy, function points, COCOMO-type estimation, timeboxing, scope creep, change control, staffing plan, Brooks’ Law.

Early estimates are less certain because the team knows less about the scope, requirements, technology, and dependencies. Estimates should be refined as evidence improves; changing an estimate is not automatically failure if the basis is transparent.

The course introduces several approaches:

- **Analogy/rule of thumb:** use comparable prior work cautiously.
- **Function points:** estimate by counting externally meaningful inputs, outputs, inquiries, files, and interfaces with weights.
- **COCOMO-type models:** relate effort to size using a model such as `effort = a × (size)^b`; the constants/context matter.
- **Timeboxing:** fix a deadline and adjust scope rather than continually moving the date.

**Scope creep** is uncontrolled expansion/change to agreed scope. It is controlled by visible change requests, impact review, prioritisation, and agreed decisions—not by refusing every legitimate change.

A staffing plan considers roles, skills, workload, trust, motivation, conflict, and training. The course cites Brooks’ Law: adding people to a late project can make it later because coordination, onboarding, and communication have costs.

---

## 6. Lesson M3.5 — Manage uncertain risk continuously

**Primary source:** C1 pp. 14–15; L4 pp. 10–34; CMU SEI resource verified in Phase 1
**Key terms:** risk, issue, probability, impact, exposure, response, trigger, contingency, monitor/control.

A **risk** is an uncertain event/condition that may affect project objectives. An **issue** is a problem that is already happening. “We have not hired the required developer” is an issue; “the key developer may leave” is a risk.

### Four transparent activities

| Activity | What the team does |
|---|---|
| Identify | use checklists, brainstorming, past projects, stakeholder/expert input to record meaningful risks |
| Analyse | estimate probability and impact; rank/prioritise exposure rather than pretending to know an exact future |
| Response-plan | choose avoid, mitigate/reduce, transfer, or accept; name owner, trigger, contingency, and monitoring need |
| Monitor/control | review signals/triggers, update risk status/score/response as the project changes |

This four-step view reconciles L4’s separate identification/analysis/control/planning/monitoring labels with C1’s clearer process. It does not erase the detailed activities; it organises them.

### Risk categories and scoring

The material includes project (schedule/cost/resources/customer), technical (requirements/implementation/interface/testing), business, technology, people, organisational, tool, requirement, and estimation risks. Probability can be described by bands or a simple ordinal scale. A common course prioritisation is:

```text
Risk exposure / priority = probability × impact
```

If a campus connectivity risk has probability 4 and impact 5 on a 1–5 scale, its score is 20. The score helps prioritise discussion; it is not a physical measurement of exact loss.

### Responses

| Response | Meaning | Course-consistent example |
|---|---|---|
| Avoid | change plan/scope/approach to remove the threat | negotiate smaller scope before a fixed deadline |
| Mitigate / reduce | lower probability or impact | offline-tolerant design, backup power plan, early prototype |
| Transfer | shift specified financial/operational exposure through contract/vendor/insurance | SLA with a payment provider |
| Accept | consciously tolerate a low/controlled risk while watching it | accept a minor UI delay with recorded rationale |

A good register states the risk, probability, impact, score, response, owner, trigger, and contingency. “Be careful” is not a response plan.

---

## 7. Case Studio — planning package scaffold

For the selected system, prepare:

1. system request (need, sponsor, high-level requirements/value, special issues);
2. technical/economic/organisational feasibility evidence;
3. WBS with 12 or more tasks, owners, durations, dependencies, and deliverables;
4. Gantt/network explanation identifying critical path and slack;
5. six-risk register with response, owner, trigger, and contingency.

**Consistency questions:** Does the stated schedule respect known constraints? Do economic assumptions match the stated solution scope? Do high-ranked risks have actions rather than labels? Does the selected methodology from Module 2 fit the plan/risk profile?

---

## 8. Future Module 3 simulations and practical demonstrations

| Interaction | Learner task | Required feedback |
|---|---|---|
| System-request composer | identify missing sponsor/need/value/special issue elements | explain why a request is incomplete or prematurely technical |
| Feasibility triage | classify scenario evidence as technical/economic/organisational | explain that feasibility types complement one another |
| ROI/payback/NPV calculator | enter/review cash flows and rate; show working | reveal formula, intermediate values, units, assumptions, and interpretation |
| Dependency network simulator | change task duration/dependency; see critical path/slack change | explain the longest-path rule and not just highlight a bar |
| WBS completion exercise | add owner/duration/deliverable/dependency to missing task details | show hidden work and dependency gaps |
| Risk register prioritiser | set probability/impact, sort, choose response, trigger, owner, contingency | flag risk-versus-issue confusion and weak “be careful” responses |
| Response trade-off cards | compare avoid/mitigate/transfer/accept under one scenario | explain why transfer does not erase a risk |

---

## 9. Formative assessment seed — 18 MCQs

| ID | Level | Prompt | Correct answer and explanation | Source |
|---|---|---|---|---|
| M3-Q01 | Remember | Which item belongs in a system request? A final class diagram B project sponsor and business need C completed user training D unit-test log | **B.** A request records early sponsor/need/value/special issues, not detailed later artefacts. | C1 p. 12 |
| M3-Q02 | Understand | Technical feasibility asks primarily: A will people use it? B can it be built/acquired/integrated with available capability? C is NPV positive? D who enters marks? | **B.** It examines technology/application familiarity, size, integration, and capability. | C1 p. 12 |
| M3-Q03 | Understand | Why is a project with positive ROI not automatically approved? A ROI prevents planning. B organisational fit, resources, risks, and strategic priorities still matter. C ROI means no costs. D only technical feasibility matters. | **B.** Feasibility dimensions and project selection are broader than one calculation. | C1 pp. 12–13 |
| M3-Q04 | Apply | Total benefits are 130,000 and total costs are 100,000. ROI is: A 30% B 23.1% C 130% D −30% | **A.** `(130,000 − 100,000) ÷ 100,000 = 0.30`, or 30%. | C1 p. 13 formula |
| M3-Q05 | Apply | Initial cost is 80,000 and net benefit is 40,000 each year. Simple payback is: A 0.5 year B 2 years C 3 years D 120,000 years | **B.** `80,000 ÷ 40,000 = 2` years under the stated simple assumptions. | C1 p. 13 |
| M3-Q06 | Analyse | A learner calculates NPV by adding future cash flows without discounting although a discount rate is supplied. What is missing? A a system boundary B time value adjustment/present values C a stakeholder map D a data store | **B.** NPV discounts future cash flows to today’s value at the stated rate. | C1 pp. 12–13 |
| M3-Q07 | Remember | A WBS is best described as: A a chart of database tables B a hierarchical decomposition of project work C an external system interface D a risk response | **B.** It lists work/tasks in a structured way. | C1 p. 13 |
| M3-Q08 | Understand | Why is a network diagram often stronger than a Gantt chart for critical-path reasoning? A It removes durations. B It makes dependencies/path alternatives explicit. C It never needs tasks. D It replaces feasibility. | **B.** Critical path depends on dependency paths. | C1 p. 13 |
| M3-Q09 | Apply | Given paths A→B→D→E = 14 days and A→C→D→E = 12 days, the critical path is: A the 12-day path B both paths C the 14-day path D no path | **C.** The longest dependency path determines earliest project duration. | C1 p. 13 |
| M3-Q10 | Apply | A task has 2 days slack. This means: A it is removed from the project B it may slip two days without delaying completion under current assumptions C it must finish two days before starting D it is always critical | **B.** Slack is allowable delay before the end date changes. | C1 p. 13 |
| M3-Q11 | Analyse | Task C has 2 days slack and takes 2 days. If it now takes 6 days in the worked example, what is the new earliest duration? A 12 B 14 C 16 D 18 | **C.** A→C→D→E becomes 3+6+5+2 = 16 days. | C1 p. 13–14 |
| M3-Q12 | Understand | Timeboxing means: A fixing every feature regardless of date B fixing the deadline and adjusting scope where necessary C avoiding estimates D transferring all risk | **B.** The approach protects the time boundary by prioritising scope. | C1 p. 14 |
| M3-Q13 | Evaluate | Why can adding developers to a late project make it later? A developers never communicate B onboarding/coordination can add work and delay existing contributors C staffing never affects schedule D it removes dependencies | **B.** This reflects the coordination insight associated with Brooks’ Law. | C1 p. 14 |
| M3-Q14 | Remember | Which statement is a risk rather than an issue? A Key developer has already resigned. B Payment gateway might fail at launch. C The team has no test environment today. D The schedule is already overdue. | **B.** It is uncertain and may occur; the others describe current problems. | C1 p. 14; L4 pp. 10–12 |
| M3-Q15 | Apply | Probability 4 and impact 5 on a 1–5 scale give exposure: A 9 B 20 C 45 D 1 | **B.** Exposure/priority = probability × impact. | C1 p. 14 |
| M3-Q16 | Analyse | “Buy insurance/SLA with a vendor” is primarily which response? A avoid B mitigate C transfer D accept | **C.** The plan transfers specified exposure/obligation; monitoring remains needed. | C1 p. 14; L4 p. 30 |
| M3-Q17 | Evaluate | A risk register says, “Internet may fail — be careful.” What is the strongest improvement? A delete it because it is uncertain B add probability, impact, response, owner, trigger, and contingency C call it an output D convert it to a class diagram | **B.** A usable register supports prioritisation and response/monitoring. | C1 pp. 14–15 |
| M3-Q18 | Analyse | A project has familiar technology, positive NPV, but staff strongly oppose the new process and management offers no training. Which feasibility area is weakest? A technical B economic C organisational D physical | **C.** Adoption/support/strategic fit are organisational feasibility concerns. | C1 pp. 12–13 |

**Cognitive coverage:** remembering 3; understanding 4; applying 5; analysing 4; evaluating 2. Several assessment tasks draw on multiple operations; later course-wide review will normalise categories and remove duplication.

---

## 10. Subjective examination-practice seed — four questions

### M3-S01 — Feasibility decision (8 marks)

**Prompt:** A university wants a mobile appointment system. It has a willing sponsor, an existing server, a proposed development cost of GH₵60,000, expected annual benefit of GH₵35,000, and staff who fear the service will replace their roles. Analyse technical, economic, and organisational feasibility. State what additional evidence is needed before a go/no-go decision.

<details><summary>Reveal model answer and marking guide</summary>

Technical feasibility is provisionally favourable if the existing server/integration/skills/capacity suit the service; further evidence includes security, mobile/connectivity, capacity, and integration assessment. Economic feasibility may be promising but requires operating costs, benefit horizon, discount rate, and cash-flow timing before ROI/payback/NPV. Organisational feasibility is a concern because staff resistance indicates adoption/change-management risk; engage staff, clarify roles, plan training, and assess management support.

**Marks:** technical reasoning/evidence (2); economic reasoning/missing data (2); organisational reasoning/change response (3); cautious decision statement (1).
</details>

### M3-S02 — Network and critical path (8 marks)

**Prompt:** Tasks are A=2 days; B=3 days after A; C=4 days after A; D=2 days after B and C. Draw/describe paths, identify critical path and duration, and state slack for the non-critical branch.

<details><summary>Reveal model answer and marking guide</summary>

Paths: A→B→D = 2+3+2 = 7 days; A→C→D = 2+4+2 = 8 days. Critical path is A→C→D; duration 8 days. B branch is one day shorter, so B has one day slack under these assumptions.

**Marks:** dependencies/paths (2); correct path calculations (2); critical path/duration (2); slack interpretation (2).
</details>

### M3-S03 — Risk register response (10 marks)

**Prompt:** For a campus registration launch, select four plausible risks from connectivity, changing requirements, developer departure, payment-gateway failure, and minor UI delay. Create a compact register with probability/impact, response, owner, trigger, and contingency. Justify one response choice.

<details><summary>Reveal model answer and marking guide</summary>

Answers vary if consistent. Example: unstable connectivity: 4×5=20, mitigate, infrastructure lead, trigger repeated outage/load failure, contingency offline-tolerant/extended window/backup plan. Changing requirements: 4×3=12, mitigate, project manager/business analyst, trigger new unapproved change requests, contingency change-control board/timeboxed release. Developer departure: 2×4=8, mitigate, project manager, trigger resignation/availability signal, contingency documentation/pairing/recruitment. Gateway failure: 2×4=8, transfer/mitigate, integration lead, trigger failed confirmation/error rate, contingency SLA/manual reconciliation/fallback. Minor UI delay: 3×1=3, accept, product owner, trigger delayed low-priority screen, contingency reschedule.

**Marks:** four plausible risks/ratings (4); suitable responses (2); owner/trigger/contingency evidence (3); one justified response trade-off (1).
</details>

### M3-S04 — Economic working (6 marks)

**Prompt:** A project costs GH₵100,000 initially. It produces net cash inflows of GH₵45,000 per year for three years. Calculate simple payback and state what additional information is needed to calculate NPV. Explain why neither result alone proves organisational feasibility.

<details><summary>Reveal model answer and marking guide</summary>

Payback occurs after two full years (90,000 recovered) plus 10,000/45,000 of Year 3, approximately 2.22 years. NPV requires a discount rate and discounting of each future cash flow (and any additional timing/operating-cost assumptions if not already net). Economic measures do not establish sponsor support, user adoption, training/process fit, or strategic alignment.

**Marks:** working/payback result (3); NPV information/discounting explanation (2); organisational-feasibility distinction (1).
</details>

---

## 11. Phase 4 Module 3 review

### Completed

- Five source-labelled lessons and worked calculations/scheduling/risk examples.
- Explicit accuracy note for the risk process and score interpretation.
- Planning-package Case Studio scaffold.
- Seven future simulations/practical demonstrations mapped to actual syllabus tasks.
- Eighteen MCQs and four subjective prompts with reasoning/model guides.

### Limitations / deferrals

- These calculations, diagrams, risk registers, and question prompts are not yet executable in the app; no calculator/scheduler/risk-prioritiser has been claimed.
- Across Modules 1–3, the reviewed content seed is 52 MCQs and 12 subjective prompts, still below the full 100/20 target and not yet a functional bank.
- NPV examples must always reveal rate/horizon/net-cash-flow assumptions; the application must not silently manufacture inputs.

## 12. Approval gate

Approve or request changes to Module 3 content. On approval, Phase 5 will add its source-backed feasibility, scheduling, and risk simulations to the same standalone HTML file before a later module’s content begins.
