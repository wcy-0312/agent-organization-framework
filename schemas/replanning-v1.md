# Replanning Schema v1

> **Schema ID:** `replanning-v1`
> **Status:** Stable
> **Owned by:** agent-organization-framework

---

## 1. Purpose

This schema defines the interface contract for the `replanning` skill.

`replanning` is an **execution plan adjustment skill**. It responds to escalation
signals from `checkpoint-review` and adjusts the execution plan — the scope,
method, or mission framing — so the project can proceed on a sound basis.

It is not a governance editor. It does not touch governance rules, review protocols,
or team structure. It is not a mission editor by default — mission changes are a
last resort available only at Major severity with explicit human approval. It is not
a task executor — it adjusts plans, not work.

The authority for initiating a replanning session comes from a checkpoint escalation.
`replanning` cannot be invoked without an escalation source. Ad-hoc replanning
(without a `review-report.md` escalation block) is outside the scope of this schema.

---

## 2. Lifecycle Position

```
Orchestrator executes tasks
Agents write to staging-buffer.md
        │
        ▼
checkpoint-review
        │
        ├── escalation.status = none
        │         │
        │         └──→ execution resumes (no replanning)
        │
        └── escalation.status ≠ none
                  │
                  ▼
            replanning  ◄── (this schema)
                  │
                  ├── Minor severity
                  │         └──→ exit, no writes, Executor self-adjusts
                  │
                  ├── Moderate severity
                  │         └──→ checkpoint_plan_adjustment
                  │               update current/handoff-package.md
                  │               write archive/checkpoint-N/replanning-report.md
                  │               execution resumes
                  │
                  └── Major severity
                            └──→ mission_revision_candidate
                                  human gate 1: permission_to_draft
                                  human gate 2: approval_to_apply
                                  conditional update to mission-contract.md
                                  execution resumes or halts pending human decision
```

---

## 3. Intake Source

The authoritative intake for `replanning` is the `escalation` block inside
`archive/checkpoint-N/review-report.md`.

```yaml
escalation:
  status: replanning_candidate | team_evolution_candidate | mission_change_candidate
  severity: minor | moderate | major
  description: "<string>"
  requires_human_approval: true | false
  recommended_next_skill: replanning | team-evolution | human-review | null
```

The entire `review-report.md` serves as supporting context — the
`classification_summary`, `entries_classified`, and `open_items` sections provide
the evidence base for replanning decisions. The `escalation` block alone determines
scope and severity; the rest of the report informs the revision content.

`replanning` must not accept a verbal description of an escalation as its intake.
If no `archive/checkpoint-N/review-report.md` with a valid escalation block exists,
halt and ask the Orchestrator to run `checkpoint-review` first.

---

## 4. Severity Dispatch

`replanning` dispatches to different behaviors based on `escalation.severity`:

### Minor

No replanning action is taken by this skill.

- Exit without writing any files.
- Inform the Orchestrator:
  > "Severity is minor. No replanning is needed. The Executor should self-adjust
  > within the existing plan and continue."
- Do not produce a replanning report for Minor findings.

### Moderate

Initiate a `checkpoint_plan_adjustment`:

- Adjust the execution plan within the current checkpoint scope.
- Allowed changes: scope refinement, method substitution, risk mitigation steps,
  constraint adjustments within the mission boundary.
- Update `current/handoff-package.md` to reflect the adjusted plan.
- Write `archive/checkpoint-N/replanning-report.md`.
- No human approval gate is required for Moderate severity.

### Major

Initiate a `mission_revision_candidate` with two human approval gates (see §6):

- Gate 1 (`permission_to_draft`): human authorizes drafting a revision to
  `mission-contract.md`. Drafting alone does not modify any file.
- Gate 2 (`approval_to_apply`): human reviews the draft and authorizes applying it.
  Only after this gate may `mission-contract.md` be modified.
- If either gate is denied, halt and record the decision in the replanning report.

---

## 5. Replanning Scope Schema

```yaml
replanning_scope:
  severity: "moderate | major"                  # must match escalation.severity
  scope_type: "checkpoint_plan_adjustment | mission_revision_candidate"
  allowed_files:                                # files this replanning session may write
    - "<path>"
  forbidden_files:                              # files explicitly off-limits
    - "<path>"
```

**Scope type maps to severity:**

| severity | scope_type |
|----------|-----------|
| `moderate` | `checkpoint_plan_adjustment` |
| `major` | `mission_revision_candidate` |

**Allowed files by scope type:**

| scope_type | allowed_files |
|-----------|--------------|
| `checkpoint_plan_adjustment` | `current/handoff-package.md`, `archive/checkpoint-N/replanning-report.md`, `memory/decision-log.md` |
| `mission_revision_candidate` | All of the above, plus `mission-contract.md` (conditional on `approval_to_apply = confirmed`) |

---

## 6. Human Approval Gates (Major Only)

Major severity replanning requires explicit human authorization at two distinct points:

```yaml
human_approval:
  required: true                          # always true for major severity
  permission_to_draft: "confirmed | denied | not_requested"
  approval_to_apply: "confirmed | denied | pending"
```

### Gate 1 — `permission_to_draft`

Authorizes drafting a proposed revision to `mission-contract.md`.

- This gate must be cleared **before** any revision draft is written.
- A `confirmed` value here means: "you may prepare a revision proposal."
- It does **not** mean: "you may apply the revision."
- If `denied`, halt replanning. Record the denial in the replanning report and
  surface to the Orchestrator.

### Gate 2 — `approval_to_apply`

Authorizes applying the drafted revision to `mission-contract.md`.

- This gate is presented **after** the human has reviewed the draft.
- A `confirmed` value here means: "apply the revision as drafted."
- `pending` means the human has not yet reviewed or decided.
- If `denied`, the draft is discarded. Record the denial in the replanning report.
- `mission-contract.md` must not be modified unless `approval_to_apply = confirmed`
  and the replanning report records this approval.

The two-gate design prevents a single ambiguous "yes" from authorizing both drafting
and application. Each gate requires a separate, unambiguous human action.

---

## 7. Replanning Report Schema

`archive/checkpoint-N/replanning-report.md` must conform to this structure:

```yaml
source_checkpoint:
  checkpoint_number: <int>                  # N from the source checkpoint
  review_report_path: "<string>"            # e.g. "archive/checkpoint-3/review-report.md"
  escalation_severity: "moderate | major"

replanning_scope:
  severity: "moderate | major"
  scope_type: "checkpoint_plan_adjustment | mission_revision_candidate"

revision_summary:
  problem: "<string>"                       # what the escalation identified as the issue
  decision: "<string>"                      # what was decided in response
  rationale: "<string>"                     # why this decision, not alternatives
  alternatives_considered:                  # list of options that were considered but not chosen
    - "<string>"

changes_applied:
  - file: "<string>"                        # path of the file changed
    change_type: "update | append | create" # what kind of change
    summary: "<string>"                     # what changed and why
    approval_ref: "<string>"                # e.g. "human gate 2 confirmed" or "moderate — no gate required"

handoff_update:
  updated: true | false                     # whether current/handoff-package.md was modified
  summary: "<string>"                       # what changed in the handoff package; empty string if not updated

human_approval:                             # omit this section entirely for Moderate severity
  required: true
  permission_to_draft: "confirmed | denied | not_requested"
  approval_to_apply: "confirmed | denied | pending"

memory_record:
  decision_log_appended: true | false       # whether memory/decision-log.md was updated
  decision_ref: "<string>"                  # ID of the appended decision entry; empty string if not appended

result:
  status: "adjusted | pending_human_approval | blocked"
  next_action: "<string>"                   # what the Orchestrator should do next
```

**`result.status` values:**

| Value | Meaning |
|-------|---------|
| `adjusted` | Replanning complete; execution may resume |
| `pending_human_approval` | Waiting for a human gate; execution is paused |
| `blocked` | A gate was denied or an error occurred; Orchestrator must decide |

---

## 8. File Access Policy

### Read

`replanning` may read:

- `.agent-org/mission-contract.md`
- `.agent-org/replanning-rules.md`
- `.agent-org/review-protocol.md`
- `.agent-org/team-evolution-rules.md`
- `.agent-org/current/handoff-package.md`
- `.agent-org/archive/checkpoint-N/review-report.md`
- `.agent-org/memory/decision-log.md`

### Write

`replanning` may write to:

- `.agent-org/current/handoff-package.md` (update)
- `.agent-org/archive/checkpoint-N/replanning-report.md` (create, once per checkpoint — see §9)
- `.agent-org/memory/decision-log.md` (append only)

### Conditional Write

- `.agent-org/mission-contract.md` — **only when all three conditions hold:**
  1. `escalation.severity = major`
  2. `human_approval.approval_to_apply = confirmed`
  3. The replanning report records this approval in `changes_applied[*].approval_ref`

### Do Not Write

`replanning` must never write to:

- `.agent-org/current/staging-buffer.md`
- `.agent-org/team-roster.md`
- `.agent-org/governance-rules.md`
- `.agent-org/review-protocol.md`
- `.agent-org/replanning-rules.md`
- `.agent-org/team-evolution-rules.md`
- `.agent-org/artifact-backend.md`
- `.agent-org/artifact-manifest.md`
- `.agent-org/archive/checkpoint-N/review-report.md`
- `.agent-org/archive/checkpoint-N/staging-buffer.md`
- `.agent-org/archive/checkpoint-N/handoff-package.md`

---

## 9. Archive Consistency Rules

`archive/checkpoint-N/replanning-report.md` is **append-once** per checkpoint:

- If `archive/checkpoint-N/replanning-report.md` already exists when `replanning`
  is invoked, halt immediately and report:

  ```
  REPLANNING_REPORT_EXISTS_ERROR
  archive/checkpoint-<N>/replanning-report.md already exists.
  v0.1 allows only one replanning-report per checkpoint.
  Manual inspection required before proceeding.
  ```

- Do not overwrite the existing report.
- Do not create a second report under a different filename.
- If a second replanning pass is genuinely needed for the same checkpoint, the
  Orchestrator must decide how to handle it — this schema does not define that path
  in v0.1.

---

## 10. Non-Goals

`replanning` explicitly does not do the following:

| Out of scope | Responsible party |
|-------------|-------------------|
| Executing tasks described in the adjusted plan | Orchestrator + agents |
| Modifying `team-roster.md` | `team-evolution` skill (v0.4 roadmap) |
| Modifying `review-protocol.md` | Human operator only |
| Modifying `governance-rules.md` | Human operator only |
| Automatically applying mission revisions without human approval | Prohibited by design |
| Writing to `current/staging-buffer.md` | Only `checkpoint-review` resets the buffer |
