# Governance State Machine v1

> **Schema ID:** `governance-state-machine-v1`
> **Schema Version:** v1
> **Status:** Stable
> **Owned by:** agent-organization-framework

---

```yaml
schema_version: v1
schema_id: governance-state-machine-v1
status: Stable
```

---

## 1. Purpose

This schema defines the Finite State Machine (FSM) contract for governance state
transitions in a running `.agent-org/` project. It is the authoritative reference for:

- Which states the Orchestrator can be in
- Which events cause transitions between states
- What recovery queue behavior is valid
- When deadlock conditions are triggered

The FSM controls the **control plane** of the governance framework. It does not replace
skill judgment — it formalizes which transitions are valid after a skill produces its
output. Every state change the Orchestrator makes must correspond to a legal transition
in §4.

---

## 2. State Definitions

### EXECUTING

**Description:** Normal execution mode. The Orchestrator is directing agents to perform
task work. No recovery action is pending.

**Entry condition:** Initialization, OR a governance cycle resolved successfully
(recovery state → EXECUTING via `pop_queue_or_EXECUTING` with empty queue).

**Exit via:** `severity_moderate`, `severity_major`, `mission_completed`

---

### REVIEW_REQUIRED

**Description:** A checkpoint trigger condition has been met. The Orchestrator must run
`checkpoint-review` before execution can resume. This state is transient — it exists
only while the checkpoint-review skill is executing.

**Entry condition:** `checkpoint-review` escalation with `severity: moderate` or
`severity: major` (from EXECUTING), or severity re-assessment during review.

**Exit via:** `severity_minor` (clear finding, resume), `severity_moderate`
(enter plan recovery), `severity_major` (enter plan recovery with human queue),
`team_issue_blocking`, `team_issue_nonblocking`

---

### PLAN_RECOVERY_REQUIRED

**Description:** A replanning action is needed. The Orchestrator must run the
`replanning` skill before execution can resume. The current execution plan is
insufficient or invalid given the checkpoint findings.

**Entry condition:** Checkpoint review determined that the execution plan requires
adjustment (moderate or major severity, no blocking team issue), OR human mission
revision authorized.

**Exit via:** `replanning_plan_revised`, `replanning_minor_adjustment`,
`replanning_mission_revision_candidate`, `replanning_rejected`

---

### TEAM_RECOVERY_REQUIRED

**Description:** A team evolution action is needed. The Orchestrator must run the
`team-evolution` skill before execution can resume. A blocking capability gap in the
current team prevents safe continuation.

**Entry condition:** Checkpoint review identified `blocking_capability_gap = true`.

**Exit via:** `team_evolution_applied`, `team_evolution_no_change_recommended`,
`team_evolution_proposal_human_required`, `team_evolution_stopped_mission`,
`team_evolution_stopped_governance`, `team_evolution_deferred`

---

### HUMAN_DECISION_REQUIRED

**Description:** The Orchestrator cannot resolve the current governance situation
autonomously. A human operator must make an explicit decision before the project can
proceed.

**Entry condition:** A skill outcome requires human judgment — mission revision
candidate, governance boundary violation, role deprecation, or consecutive recovery
failures.

**Exit via:** `human_approved`, `human_rejected`, `human_mission_revised`,
`human_mission_abandoned`

---

### COMPLETED

**Description:** Terminal state. The mission deliverables have been fully accepted by
the Verifier and the Orchestrator has declared the project complete. No further
transitions are allowed from this state.

**Entry condition:** `mission_completed` event from EXECUTING.

**Exit via:** None (terminal)

---

### ABORTED

**Description:** Terminal state. The project has been explicitly terminated — either by
human rejection after a mission revision candidate or by human abandonment. No further
transitions are allowed from this state.

**Entry condition:** `human_rejected` or `human_mission_abandoned` from
HUMAN_DECISION_REQUIRED.

**Exit via:** None (terminal)

---

## 3. Governance Event Definitions

Events are produced by skill outputs. Each event maps to a specific field/value in the
producing skill's output record.

### Events from checkpoint-review outputs

| Event | Produced by |
|-------|-------------|
| `severity_minor` | `escalation.severity: minor` |
| `severity_moderate` | `escalation.severity: moderate` |
| `severity_major` | `escalation.severity: major` |
| `team_issue_blocking` | `team_issue_detected: true` AND `blocking_capability_gap: true` |
| `team_issue_nonblocking` | `team_issue_detected: true` AND `blocking_capability_gap: false` |

When `team_issue_detected = true`, the team issue event (`team_issue_blocking` or
`team_issue_nonblocking`) governs the FSM transition from REVIEW_REQUIRED. The severity
event is still recorded in the review report but does not determine the FSM path.

### Events from replanning outputs

| Event | Produced by |
|-------|-------------|
| `replanning_plan_revised` | `result.status: adjusted` (scope_type: checkpoint_plan_adjustment) |
| `replanning_minor_adjustment` | `result.status: adjusted` (severity: minor — no file writes) |
| `replanning_mission_revision_candidate` | `result.status: pending_human_approval` |
| `replanning_rejected` | `result.status: blocked` |

### Events from team-evolution outputs

| Event | Produced by |
|-------|-------------|
| `team_evolution_applied` | `outcome.status: applied` |
| `team_evolution_no_change_recommended` | `outcome.status: no_change_recommended` |
| `team_evolution_proposal_human_required` | `human_approval_required: true` AND `outcome.status: proposal_ready` |
| `team_evolution_stopped_mission` | `outcome.status: stopped_mission_impact` |
| `team_evolution_stopped_governance` | `outcome.status: stopped_governance_impact` |
| `team_evolution_deferred` | `outcome.status: deferred_insufficient_evidence` |

### Events from human decision

| Event | Meaning |
|-------|---------|
| `human_approved` | Human explicitly approves the pending action (proposal, mission revision draft, etc.) |
| `human_rejected` | Human explicitly rejects and does not provide an alternative path |
| `human_mission_revised` | Human approves a mission revision; replanning must proceed to apply it |
| `human_mission_abandoned` | Human explicitly terminates the project |

### Lifecycle events

| Event | Meaning |
|-------|---------|
| `initialization` | `.agent-org/` has just been created by `create-agent-organization`; FSM starts |
| `mission_completed` | Orchestrator declares mission complete after Verifier acceptance |

---

## 4. Transition Table

The following block is machine-readable and is used by `tools/validate_governance_state.py`
(Rule 4) to validate that every transition recorded in `governance-history.md` is legal.

**Special value: `pop_queue_or_EXECUTING`** — if `pending_queue` is non-empty, transition
to `queue[0]` and remove it; otherwise transition to EXECUTING. In recorded history, the
concrete resolved state appears as the `to` value.

**Queue push side effects** (applied at transition time; recorded in
`governance-state.md` but not as separate history entries):
- `REVIEW_REQUIRED + severity_major` pushes `HUMAN_DECISION_REQUIRED` to the queue
- `REVIEW_REQUIRED + team_issue_blocking` pushes `PLAN_RECOVERY_REQUIRED` to the queue
- `REVIEW_REQUIRED + team_issue_nonblocking` pushes `TEAM_RECOVERY_REQUIRED` to the queue

```yaml governance-transitions
transitions:
  - from: null
    event: initialization
    to: EXECUTING

  - from: EXECUTING
    event: severity_minor
    to: EXECUTING

  - from: EXECUTING
    event: severity_moderate
    to: REVIEW_REQUIRED

  - from: EXECUTING
    event: severity_major
    to: REVIEW_REQUIRED

  - from: EXECUTING
    event: mission_completed
    to: COMPLETED

  - from: REVIEW_REQUIRED
    event: severity_minor
    to: EXECUTING

  - from: REVIEW_REQUIRED
    event: severity_moderate
    to: PLAN_RECOVERY_REQUIRED

  - from: REVIEW_REQUIRED
    event: severity_major
    to: PLAN_RECOVERY_REQUIRED
    queue_push: HUMAN_DECISION_REQUIRED

  - from: REVIEW_REQUIRED
    event: team_issue_blocking
    to: TEAM_RECOVERY_REQUIRED
    queue_push: PLAN_RECOVERY_REQUIRED

  - from: REVIEW_REQUIRED
    event: team_issue_nonblocking
    to: PLAN_RECOVERY_REQUIRED
    queue_push: TEAM_RECOVERY_REQUIRED

  - from: PLAN_RECOVERY_REQUIRED
    event: replanning_plan_revised
    to: pop_queue_or_EXECUTING

  - from: PLAN_RECOVERY_REQUIRED
    event: replanning_minor_adjustment
    to: pop_queue_or_EXECUTING

  - from: PLAN_RECOVERY_REQUIRED
    event: replanning_mission_revision_candidate
    to: HUMAN_DECISION_REQUIRED

  - from: PLAN_RECOVERY_REQUIRED
    event: replanning_rejected
    to: HUMAN_DECISION_REQUIRED

  - from: TEAM_RECOVERY_REQUIRED
    event: team_evolution_applied
    to: pop_queue_or_EXECUTING

  - from: TEAM_RECOVERY_REQUIRED
    event: team_evolution_no_change_recommended
    to: pop_queue_or_EXECUTING

  - from: TEAM_RECOVERY_REQUIRED
    event: team_evolution_proposal_human_required
    to: HUMAN_DECISION_REQUIRED

  - from: TEAM_RECOVERY_REQUIRED
    event: team_evolution_stopped_mission
    to: HUMAN_DECISION_REQUIRED

  - from: TEAM_RECOVERY_REQUIRED
    event: team_evolution_stopped_governance
    to: HUMAN_DECISION_REQUIRED

  - from: TEAM_RECOVERY_REQUIRED
    event: team_evolution_deferred
    to: HUMAN_DECISION_REQUIRED

  - from: HUMAN_DECISION_REQUIRED
    event: human_approved
    to: pop_queue_or_EXECUTING

  - from: HUMAN_DECISION_REQUIRED
    event: human_rejected
    to: ABORTED

  - from: HUMAN_DECISION_REQUIRED
    event: human_mission_revised
    to: PLAN_RECOVERY_REQUIRED

  - from: HUMAN_DECISION_REQUIRED
    event: human_mission_abandoned
    to: ABORTED
```

---

## 5. Recovery Queue Rules

```yaml
recovery_queue:
  max_length: 2
  type: ordered list, FIFO
  entry_structure: state name only (no metadata)
  pop_behavior: >
    pop_queue_or_EXECUTING: if queue is non-empty, transition to queue[0] and
    remove it from the queue; else transition to EXECUTING.
```

**Queue constraints:**
- Maximum 2 entries at any time
- Only valid, non-terminal FSM state names may be enqueued
- Queue is consumed FIFO — first pushed is first popped
- Queue pushes occur as side effects of specific REVIEW_REQUIRED transitions (see §4)
- The queue is persisted in `current/governance-state.md` under `pending_queue`

---

## 6. Deadlock Definition

```yaml
deadlock_condition:
  description: >
    3 consecutive governance cycles fail to return to EXECUTING or COMPLETED.
    A cycle is defined as: a recovery state exits to a non-EXECUTING,
    non-COMPLETED destination. If HUMAN_DECISION_REQUIRED is reached 3 or more
    consecutive times without any intervening return to EXECUTING or COMPLETED,
    the FSM is considered deadlocked.
  trigger: HUMAN_DECISION_REQUIRED
  validator_rule: Rule 6
  resolution: >
    Human operator must manually inspect governance-state.md and
    governance-history.md, determine the root cause, and either reset
    governance state or invoke human_mission_abandoned.
```

---

## 7. Terminal Conditions

```yaml
terminal_conditions:
  COMPLETED:
    description: >
      Mission deliverables are fully accepted by the Verifier Lead, and the
      Orchestrator explicitly declares project completion.
    entry_event: mission_completed
    from_state: EXECUTING
    reversible: false

  ABORTED:
    description: >
      Human explicitly terminates the project, OR human rejects a mission
      revision candidate without providing an alternative path forward.
    entry_events:
      - human_rejected        # from HUMAN_DECISION_REQUIRED
      - human_mission_abandoned  # from HUMAN_DECISION_REQUIRED
    reversible: false
```

---

## 8. File Locations

```yaml
active_state_file:    .agent-org/current/governance-state.md
history_file:         .agent-org/archive/checkpoint-N/governance-history.md
template_state:       templates/governance-state.md
template_history:     templates/governance-history.md
validator:            tools/validate_governance_state.py
```

`governance-state.md` reflects the current live FSM state and is updated by each
skill after it completes. `governance-history.md` in each checkpoint archive records
the complete transition log for that checkpoint period and is append-only.
