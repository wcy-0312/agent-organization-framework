# Governance Control Plane

> **Document type:** Human-readable explanation
> **Companion schema:** `schemas/governance-state-machine-v1.md`
> **Status:** Stable (v0.5)

---

## 1. Why This Document Exists

Before v0.5, the governance framework had a gap: each skill (`checkpoint-review`,
`replanning`, `team-evolution`) defined its own inputs and outputs, but nothing
specified what state the Orchestrator was *in* between skill invocations, or what
transitions were *valid* as a result of a skill's output.

This created a silent assumption: the Orchestrator "just knows" which skill to invoke
next. In practice, that means governance logic was scattered across skill descriptions,
not centralized anywhere, and impossible to validate mechanically.

The **Governance Control Plane** closes this gap. It defines:

1. A **Finite State Machine (FSM)** that formalizes which states the Orchestrator can
   be in and which transitions are valid (defined in `schemas/governance-state-machine-v1.md`)
2. A **policy layer** that governs when the Orchestrator enters `REVIEW_REQUIRED` — the
   condition that drives the entire recovery cycle

With these two layers, governance state is explicit, auditable, and mechanically
verifiable. The validator (`tools/validate_governance_state.py`) can check that every
recorded transition conforms to the Transition Table.

---

## 2. Architecture: Two Layers

### FSM Layer

The FSM layer is defined in `schemas/governance-state-machine-v1.md`. It answers:
"Given the current state and a skill output event, what is the next valid state?"

The FSM does not decide *when* to trigger a checkpoint or *which* skill to invoke. It
only validates that the resulting transition is legal. Think of it as the rules engine
for governance state, not the executor.

**States (7):**

| State | Role |
|-------|------|
| `EXECUTING` | Normal task execution — no recovery pending |
| `REVIEW_REQUIRED` | Checkpoint trigger met; `checkpoint-review` must run |
| `PLAN_RECOVERY_REQUIRED` | Execution plan needs adjustment via `replanning` |
| `TEAM_RECOVERY_REQUIRED` | Blocking capability gap; `team-evolution` must run |
| `HUMAN_DECISION_REQUIRED` | Human operator input required before proceeding |
| `COMPLETED` | Terminal — mission accepted and complete |
| `ABORTED` | Terminal — project explicitly terminated |

**Files:**
- Live state: `.agent-org/current/governance-state.md`
- Transition history (per checkpoint): `.agent-org/archive/checkpoint-N/governance-history.md`

### Policy Layer

The policy layer governs when the Orchestrator enters `REVIEW_REQUIRED`. This is NOT
a list of specific trigger conditions — those live in `.agent-org/review-protocol.md`.
The policy layer is the set of principles that determine whether a situation constitutes
a decision point.

The key principle: **checkpoints bind to decisions, not to task completions.** The
Orchestrator enters `REVIEW_REQUIRED` when a decision must be made, not when a step
is finished.

---

## 3. Checkpoint Trigger Principles

Checkpoint trigger conditions are enumerated in `.agent-org/review-protocol.md` for
each specific project. However, all valid triggers derive from three underlying
principles:

**Principle 1 — New information changes what is possible.**
A trigger is warranted when the team has learned something that materially changes
the feasibility, scope, or method of the current execution plan. The information must
be new — confirming what was already known is not a trigger.

**Principle 2 — A decision point has been reached that cannot be deferred.**
When the project has arrived at a fork where different paths lead to meaningfully
different outcomes, and the choice cannot be made by any individual agent within their
responsibility boundary, a checkpoint is required. Deferring the decision past this
point creates compounding ambiguity.

**Principle 3 — A risk has crossed the threshold from acceptable to unacceptable.**
When a risk that was previously within acceptable bounds has been realized or
significantly elevated — by new evidence, a failed artifact, or a discovered
constraint — the Orchestrator must assess before proceeding. Proceeding under
elevated risk without assessment is a governance violation, not a judgment call.

What is NOT a valid trigger by itself: task step completion, time elapsed, subagent
finished work, phase label changed. These may coincide with a decision point, but
they do not create one.

---

## 4. How to Read governance-state.md and governance-history.md

### governance-state.md (current live state)

Located at `.agent-org/current/governance-state.md`. Updated by each skill after it
completes. The format is a YAML front matter block:

```yaml
---
fsm_version: v1
checkpoint_id: checkpoint-3
current_state: PLAN_RECOVERY_REQUIRED
pending_queue:
  - HUMAN_DECISION_REQUIRED
last_transition:
  from: REVIEW_REQUIRED
  to: PLAN_RECOVERY_REQUIRED
  event: severity_major
  timestamp: 2026-06-12T14:23:00Z
---
```

**Fields:**
- `current_state` — the FSM state the project is currently in
- `pending_queue` — states waiting to be entered after the current recovery resolves
  (max 2 entries, FIFO). Empty when `current_state = EXECUTING`.
- `last_transition` — the most recent transition: from/to/event/timestamp

To understand what happened, read `last_transition.event` and look it up in the
Transition Table in `schemas/governance-state-machine-v1.md §4`.

### governance-history.md (per-checkpoint transition log)

Located at `.agent-org/archive/checkpoint-N/governance-history.md`. Created during
the checkpoint archive step and then append-only. Records every FSM transition that
occurred during checkpoint N's lifecycle.

```yaml
---
fsm_version: v1
checkpoint_id: checkpoint-3
---

## Transition Log

- timestamp: 2026-06-12T12:00:00Z
  from: null
  to: EXECUTING
  event: initialization

- timestamp: 2026-06-12T14:20:00Z
  from: EXECUTING
  to: REVIEW_REQUIRED
  event: severity_major

- timestamp: 2026-06-12T14:23:00Z
  from: REVIEW_REQUIRED
  to: PLAN_RECOVERY_REQUIRED
  event: severity_major
```

To audit the governance history: read the log in order. Each entry must correspond to
a legal transition in the Transition Table. Run `tools/validate_governance_state.py`
against this file to verify mechanically.

---

## 5. Authority Boundary with OQ-001 (Organization Manager)

OQ-001 asks: should there be a persistent Organization Manager skill that drives the
full lifecycle, rather than a human Orchestrator?

The Governance Control Plane is explicitly designed with OQ-001 in mind:

**Control Plane = defines WHAT transitions are valid (policy)**

`schemas/governance-state-machine-v1.md` and this document define *which* state
transitions are legal and *what conditions* trigger them. This is policy — it does not
change based on how the Orchestrator is implemented.

**Organization Manager (v1.0) = decides WHEN to execute them (executor)**

An Organization Manager skill, if built, would read `current/governance-state.md`,
determine which skill to invoke next based on `current_state`, invoke it, and then
update the state file with the resulting transition. The transition must still conform
to the Transition Table — the Manager is an executor of policy, not a redesigner of it.

**This document is designed to be readable by the Organization Manager.** The
structured YAML in `schemas/governance-state-machine-v1.md` (especially the
`yaml governance-transitions` block) is machine-parseable so a future skill can
consume it programmatically without re-encoding the rules.

---

## 6. Example FSM Walk-throughs

### Happy Path — Moderate Finding Resolved

```
Initial state: EXECUTING (pending_queue: [])

[Checkpoint trigger condition met]

Transition: EXECUTING + severity_moderate → REVIEW_REQUIRED
  checkpoint-review runs
  → finds execution plan adjustment needed (no team issue)
  → escalation.severity: moderate
  → event: severity_moderate

Transition: REVIEW_REQUIRED + severity_moderate → PLAN_RECOVERY_REQUIRED
  replanning runs
  → adjusts current execution plan
  → result.status: adjusted (checkpoint_plan_adjustment)
  → event: replanning_plan_revised

Transition: PLAN_RECOVERY_REQUIRED + replanning_plan_revised
  → pop_queue_or_EXECUTING (queue empty → EXECUTING)
  State: EXECUTING (pending_queue: [])

[Execution continues... mission deliverables accepted]

Transition: EXECUTING + mission_completed → COMPLETED
  State: COMPLETED (terminal)
```

### Escalation Path — Blocking Team Issue with Queued Recovery

```
Initial state: EXECUTING (pending_queue: [])

[Critical finding at checkpoint]

Transition: EXECUTING + severity_major → REVIEW_REQUIRED
  checkpoint-review runs
  → identifies team blocking issue (Python expert missing for next phase)
  → team_issue_detected: true, blocking_capability_gap: true
  → event: team_issue_blocking

Transition: REVIEW_REQUIRED + team_issue_blocking
  → TEAM_RECOVERY_REQUIRED
  → queue_push: PLAN_RECOVERY_REQUIRED
  State: TEAM_RECOVERY_REQUIRED (pending_queue: [PLAN_RECOVERY_REQUIRED])

  team-evolution runs
  → proposes DEPRECATE_ROLE, requires human approval
  → outcome.status: proposal_ready, human_approval_required: true
  → event: team_evolution_proposal_human_required

Transition: TEAM_RECOVERY_REQUIRED + team_evolution_proposal_human_required
  → HUMAN_DECISION_REQUIRED
  State: HUMAN_DECISION_REQUIRED (pending_queue: [PLAN_RECOVERY_REQUIRED])

  Human reviews roster change and approves
  → event: human_approved

Transition: HUMAN_DECISION_REQUIRED + human_approved
  → pop_queue_or_EXECUTING (queue: [PLAN_RECOVERY_REQUIRED] → pop → PLAN_RECOVERY_REQUIRED)
  State: PLAN_RECOVERY_REQUIRED (pending_queue: [])

  replanning runs
  → adjusts execution plan for new team structure
  → result.status: adjusted
  → event: replanning_plan_revised

Transition: PLAN_RECOVERY_REQUIRED + replanning_plan_revised
  → pop_queue_or_EXECUTING (queue empty → EXECUTING)
  State: EXECUTING (pending_queue: [])

[Execution resumes with updated team and plan]
```
