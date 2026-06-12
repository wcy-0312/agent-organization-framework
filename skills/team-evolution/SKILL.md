---
name: team-evolution
description: >
  Evaluate and apply a roster change after checkpoint-review or replanning detects
  a team capability issue. Use this skill when checkpoint-review or replanning
  outputs team_issue_detected = true. Also triggers when the user says "run team
  evolution", "the team needs to change", "we have a capability gap", or "apply
  roster change". Do NOT use this skill in response to a human_request (MVP
  limitation — human_request is not a valid trigger_source_type). Do NOT use this
  skill without a source report — all invocations must reference a triggering
  checkpoint-review or replanning output via trigger_source_file.
---

# Team Evolution Skill v0.1

You answer one question: given what the checkpoint or replanning discovered about the
team, does the roster need to change, and if so, how?

You are not a replanning skill. You are not a checkpoint closer. You do not execute
tasks. You diagnose team capability gaps, propose or apply roster patches, and record
the decision.

Read `schemas/team-evolution-v1.md` before proceeding. That document is the
authoritative contract for all outputs this skill produces.
Read `schemas/team-evolution-artifacts-v1.md` for the format contract of all
artifacts this skill generates.

---

## Read Before Starting

Before executing any workflow step, read all of the following:

- `.agent-org/team-roster.md`
- `.agent-org/team-evolution-rules.md`
- `.agent-org/mission-contract.md`
- `.agent-org/current/handoff-package.md`
- Triggering report (path from `trigger_source_file`)
- `schemas/team-evolution-v1.md`
- `schemas/team-evolution-artifacts-v1.md`

Do not proceed to Phase 1 until all files have been read.

---

## Responsibility Boundary

**This skill MAY:**
- Validate trigger legitimacy
- Diagnose capability gap
- Evaluate structural change necessity
- Run boundary checks
- Propose a roster patch
- Apply an approved patch (with the correct approval gate)
- Generate `team-evolution-report.md`
- Generate `team-context-patch.md` (conditional — see Phase 7 and §10)
- Append `memory/decision-log.md`

**This skill MUST NOT:**
- Modify `governance-rules.md`
- Modify `review-protocol.md`
- Modify `replanning-rules.md`
- Modify `team-evolution-rules.md`
- Modify `mission-contract.md`
- Perform replanning — that is the `replanning` skill
- Close checkpoints — that is the `checkpoint-review` skill
- Execute tasks described in the adjusted roster

---

## Outputs

All outputs conform to `schemas/team-evolution-artifacts-v1.md`.

| Outcome | Files produced |
|---------|----------------|
| `rejected_invalid_trigger` | `archive/checkpoint-N/team-evolution-rejection.md` |
| `no_change_recommended` | `archive/checkpoint-N/team-evolution-report.md` |
| `deferred_insufficient_evidence` | `archive/checkpoint-N/team-evolution-report.md` |
| `stopped_mission_impact` | `archive/checkpoint-N/team-evolution-escalation.md` |
| `stopped_governance_impact` | `archive/checkpoint-N/team-evolution-escalation.md` |
| `proposal_ready` | `archive/checkpoint-N/team-evolution-report.md`, `archive/checkpoint-N/team-roster.patch.md` |
| `applied` | `team-roster.md` (updated), `archive/checkpoint-N/team-roster.snapshot.md`, `archive/checkpoint-N/team-evolution-application.md`, `current/team-context-patch.md` (conditional) |
| `rolled_back` | `team-roster.md` (restored), `archive/checkpoint-N/team-evolution-rollback.md` |

---

## File Access Policy

**Read:** `team-roster.md`, `team-evolution-rules.md`, `mission-contract.md`,
`governance-rules.md`, `current/handoff-package.md`, triggering report,
`memory/decision-log.md`

**Write:** `team-roster.md` (apply/rollback only), `current/team-context-patch.md`
(conditional), `archive/checkpoint-N/*`, `memory/decision-log.md` (append only)

**Do Not Write:** `mission-contract.md`, `governance-rules.md`, `review-protocol.md`,
`replanning-rules.md`, `team-evolution-rules.md`, `current/staging-buffer.md`,
`current/handoff-package.md`, `artifact-manifest.md`, `artifact-backend.md`

---

## Workflow

### Phase 1 — Trigger Validation (§2)

Verify that the trigger is legitimate before proceeding. Check all of the following:

1. `trigger_source_type` must be `checkpoint_escalation`, `replanning_output`, or
   `repeated_finding`. `human_request` is not valid in MVP — reject immediately.
2. `trigger_source_file` must reference an existing report.
3. Read the triggering report and confirm a team capability issue is flagged
   (e.g. `team_issue_detected = true` or an escalation signal). If absent, reject.
4. `trigger_finding_id` must reference an identifiable finding in the source report.

If any check fails:
- Set `outcome.status = rejected_invalid_trigger`
- Write `archive/checkpoint-N/team-evolution-rejection.md`
- Set `recommended_followup` and stop

Record `trigger_legitimacy_confirmed` and `trigger_legitimacy_basis` before
continuing.

---

### Phase 2 — Evidence Review (§3)

Read the triggering report in full. Assess:

- `observed_failure_pattern` — what specific failure or gap was observed
- `affected_roles` — which roles are implicated
- `recurrence_count` — how many times has this pattern appeared
- `supporting_archive_paths` — what archive evidence supports the finding
- `confidence` — assess as `low`, `medium`, or `high`

Record `evidence_scope = triggering_checkpoint_only` unless the trigger explicitly
references multiple checkpoints.

---

### Phase 3 — Diagnosis (§4)

Determine whether the observed failure is structural or non-structural.

**Evidence insufficiency path — check this first:**
If available evidence is insufficient to determine `structural_change_required` with
confidence, do not force a determination. Set `outcome.status =
deferred_insufficient_evidence` and skip Phases 4–7, jumping directly to Phase 8
(Recommended Followup).

Typical indicators for insufficient evidence:
- `confidence = low`
- `supporting_archive_paths = []`
- Evidence is indirect, stale, or contradictory
- `recurrence_count` too low to distinguish temporary spike from structural gap

For `deferred_insufficient_evidence`, the `team-evolution-report.md` body must
document what evidence was available, why it is insufficient, and what specific
evidence is required before the proposal can be re-evaluated.

**Diagnosis routing (when evidence is sufficient):**

| `diagnosis_type` | Next step |
|---|---|
| `temporary_spike` / `execution_mistake` / `plan_flaw` | `structural_change_required = false` → `no_change_recommended` |
| `mission_mismatch` | Route to boundary check → `stop_mission` |
| `role_overload` / `missing_expertise` / `ambiguous_responsibility` / `obsolete_role` | `structural_change_required = true` → proceed to Phase 4 |

Consider non-structural alternatives before concluding `structural_change_required =
true`. Record alternatives considered in `non_structural_alternatives_considered`.

---

### Phase 4 — Boundary Checks (§5)

Assess potential impacts across all governance boundaries:

- `mission_contract_impact` — would this change require modifying `mission-contract.md`?
- `governance_impact` — would this change affect `governance-rules.md` or other
  governance files? Record specific targets in `governance_impact_targets`.
- `team_evolution_rules_impact` — would this change violate `team-evolution-rules.md`?
- `archive_integrity_impact` — would this change create inconsistencies in the archive?
- `cross_checkpoint_dependency` — does this change depend on state from a prior
  checkpoint?

**Boundary routing:**

| `boundary_check_result` | Outcome |
|---|---|
| `stop_mission` | `stopped_mission_impact` — write escalation, no patch |
| `stop_governance` / `stop_team_evolution_rules` | `stopped_governance_impact` — write escalation, no patch |
| `stop_archive_integrity` | `stopped_governance_impact` — write escalation, no patch |
| `pass` | Proceed to Phase 5 |

---

### Phase 5 — Proposed Change (§6)

Draft the roster change proposal. Specify:

- `change_type` — `ADD_ROLE`, `MODIFY_ROLE`, `SPLIT_ROLE`, or `DEPRECATE_ROLE`
- `change_subtype` — specific subtype from the schema
- `target_roles` — which roles are affected
- `proposed_roster_patch_path` — `archive/checkpoint-N/team-roster.patch.md`
- `proposed_roster_patch_summary` — human-readable description
- `expected_benefit` — why this change helps
- `risks` — what could go wrong
- `rollback_plan_summary` — how to revert if needed

If `requested_mode = evaluate_only` or `propose_patch`: set `outcome.status =
proposal_ready`, write the report and patch files, and stop. Do not proceed to Phase
6 unless `requested_mode = apply_approved_patch`.

---

### Phase 6 — Human Approval Gate (§7)

Approval gate is **impact-based**, not mode-based.

`human_approval_required = true` when ANY of the following:
- `change_type = DEPRECATE_ROLE`
- `change_type = SPLIT_ROLE`
- Change affects responsibility boundaries of multiple existing roles
- Change affects the Orchestrator coordination model
- Change requires `mission-contract.md` modification
- `requested_mode = rollback`

`human_approval_required = false` when ALL of the following:
- `change_type = ADD_ROLE`
- No existing role's responsibility boundary is changed
- Orchestrator coordination model is unaffected
→ Orchestrator approval is sufficient

Present the proposed change and wait for explicit approval. Do not proceed to Phase 7
until `approval_status = approved`.

If `approval_status = rejected`: record the rejection in the report and stop. The
proposal stands in the archive but is not applied.

---

### Phase 7 — Application (§8)

Execute the application sequence in strict order:

1. Confirm `approval_status = approved`
2. Snapshot `team-roster.md` → `archive/checkpoint-N/team-roster.snapshot.md`
3. Apply the patch → `team-roster.md`
4. Write `archive/checkpoint-N/team-evolution-application.md` (include all hash fields
   and `team_context_patch_generated`)
5. Set `outcome.status = applied`
6. Determine whether to produce `current/team-context-patch.md`

**`team-context-patch.md` decision:**

Generate it when ANY of the following is true:
- `handoff-package.md` assigns next-phase work to a role that was removed, split,
  renamed, or materially modified
- `handoff-package.md` describes responsibility routing that changed after roster
  application
- A newly added role should participate in the immediate next execution phase
- Prior handoff assumptions about verifier/executor/orchestrator routing are no
  longer accurate

Do NOT generate it when:
- The added role is optional or future-facing with no next-phase involvement
- The change only affects long-term roster clarity with no routing impact
- No next-phase routing or responsibility assumption in `handoff-package.md` is
  affected

Set `team_context_patch_generated = true` in `team-evolution-application.md` if
generated. If generated, include `current/team-context-patch.md` in
`active_files_modified`.

---

### Phase 8 — Rollback (§9)

Triggered only when `requested_mode = rollback`.

Rollback always requires human approval (`human_approval_required = true` — see §7).

Rollback sequence:
1. Confirm `rollback_approval_status = approved`
2. Read `archive/checkpoint-N/team-roster.snapshot.md`
3. Restore `team-roster.md` from snapshot
4. If `team-evolution-application.md` records `team_context_patch_generated = true`,
   remove `current/team-context-patch.md` and set `team_context_patch_removed = true`
5. Write `archive/checkpoint-N/team-evolution-rollback.md` (include all hash fields
   and `team_context_patch_removed`)
6. Set `outcome.status = rolled_back`

Rollback constraints:
- `rollback_source` must be within the same checkpoint-N archive
- Cross-checkpoint rollback is not permitted in MVP

---

### Phase 9 — Recommended Followup (§11)

After determining the final outcome, set `recommended_followup`:

| Typical outcome | Typical `recommended_followup` |
|---|---|
| `no_change_recommended` (diagnosis = `plan_flaw`) | `reroute_to_replanning` |
| `no_change_recommended` (diagnosis = `temporary_spike`) | `none` |
| `deferred_insufficient_evidence` | `collect_additional_evidence` |
| `stopped_mission_impact` | `human_review` |
| `applied` | `none` |

**Loop prevention constraint:** If `trigger_source_type = replanning_output`,
`recommended_followup` MUST NOT be `reroute_to_replanning`. Use `human_review` or
`collect_additional_evidence` instead. This prevents a replanning → team-evolution →
replanning loop.

Record `recommended_followup_rationale` with a brief explanation.

---

## Hard Constraints

- Never modify `mission-contract.md`, `governance-rules.md`, `review-protocol.md`,
  `replanning-rules.md`, or `team-evolution-rules.md`.
- Never invoke `replanning` or close checkpoints.
- Do not proceed to application without explicit approval when
  `human_approval_required = true`.
- `trigger_source_type = human_request` is always rejected in MVP.
- Do not invoke without a source report — ad-hoc calls without `trigger_source_file`
  are rejected.
- If `trigger_source_type = replanning_output`, `recommended_followup` must not be
  `reroute_to_replanning`.
- Rollback is cross-checkpoint-prohibited: `rollback_source` must be within the same
  `checkpoint-N`.

---

## Completion Message

After the final phase completes, report:

- Outcome status (e.g. "applied", "proposal_ready", "deferred_insufficient_evidence")
- Files written (list)
- Change summary (what changed and why, or why no change was made)
- Human approval status (if `human_approval_required = true`)
- `team_context_patch_generated` (if `status = applied`)
- `recommended_followup` and rationale
- Next recommended action for the Orchestrator

---

## Governance State Machine Integration

This section governs how `team-evolution` updates the Governance State Machine defined
in `schemas/governance-state-machine-v1.md`.

### After Skill Completes (Final Phase)

After all artifact writes are complete, derive the FSM event from the skill outcome:

| `outcome.status` | Condition | FSM event |
|------------------|-----------|-----------|
| `applied` | — | `team_evolution_applied` |
| `no_change_recommended` | — | `team_evolution_no_change_recommended` |
| `proposal_ready` | `human_approval_required: true` | `team_evolution_proposal_human_required` |
| `stopped_mission_impact` | — | `team_evolution_stopped_mission` |
| `stopped_governance_impact` | — | `team_evolution_stopped_governance` |
| `deferred_insufficient_evidence` | — | `team_evolution_deferred` |
| `rejected_invalid_trigger` | — | `team_evolution_deferred` |
| `rolled_back` | — | `team_evolution_applied` |

Look up `(TEAM_RECOVERY_REQUIRED, <event>)` in the Transition Table in
`schemas/governance-state-machine-v1.md §4` to determine the next state.

For `pop_queue_or_EXECUTING`: read `pending_queue` from
`.agent-org/current/governance-state.md`. If the queue is non-empty, the next state
is `queue[0]` and that entry is removed. If the queue is empty, the next state is
`EXECUTING`.

### Updating governance-state.md

Update `.agent-org/current/governance-state.md`:

- Set `current_state` to the resolved next state
- Update `pending_queue` (remove popped entry if applicable)
- Update `last_transition` with `from: TEAM_RECOVERY_REQUIRED`, resolved `to`, `event`,
  and current ISO 8601 timestamp

Do not update `governance-state.md` before all artifact writes are complete.

### Appending governance-history.md

After updating `governance-state.md`, append the transition to
`.agent-org/archive/checkpoint-N/governance-history.md`. If the file does not exist
for this checkpoint, create it from `templates/governance-history.md` first.

Append format:

```yaml
- timestamp: <ISO8601>
  from: TEAM_RECOVERY_REQUIRED
  to: <resolved next state>
  event: <event name>
```

`governance-history.md` is append-only. Never overwrite existing entries.
