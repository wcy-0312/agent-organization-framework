# Team Evolution Record v1
# All paths in this schema are relative to .agent-org/ unless explicitly absolute.
#
# Patch revision notes (session 2):
# - Added deferred_insufficient_evidence to outcome status
# - Added recommended_followup field
# - Replaced mode-based human approval with impact-based approval
# - Removed human_request from trigger_source_type (MVP)
# - Added replanning loop prevention constraint
# - Added team-context-patch.md reference in outcome section
# - Aligned with Decision Summary v1 from design session

## 1. Metadata
schema_version: "team-evolution-v1"
record_id: <uuid>
checkpoint_id: <checkpoint-N>
created_at: <ISO 8601 timestamp>
created_by: <agent or human identifier>
skill_version: <team-evolution skill version>

## 2. Trigger
trigger_source_type: checkpoint_escalation | replanning_output | repeated_finding
# human_request is NOT valid in MVP.
# repeated_finding must reference a checkpoint archive path as trigger_source_file.
trigger_source_file: <path to triggering report>
trigger_finding_id: <finding ID from source report>
trigger_finding_summary: <brief description>
trigger_legitimacy_confirmed: true | false
trigger_legitimacy_basis: <reasoning or reference>
requested_mode: evaluate_only | propose_patch | apply_approved_patch | rollback
# requested_mode controls the execution phase, not the approval gate.
# Approval gate is determined by change impact (see § 7).

## 3. Evidence
observed_failure_pattern: <description>
affected_roles: []
recurrence_count: <integer, provided by upstream checkpoint-review>
supporting_archive_paths: []
confidence: low | medium | high
evidence_scope: triggering_checkpoint_only

## 4. Diagnosis
diagnosis_type: role_overload | missing_expertise | ambiguous_responsibility
               | obsolete_role | temporary_spike | execution_mistake
               | plan_flaw | mission_mismatch
structural_change_required: true | false
structural_issue_summary: <description>
non_structural_alternatives_considered: <description>
structural_change_rationale: <why roster change is needed>

# Diagnosis routing rules:
# temporary_spike / execution_mistake / plan_flaw
#   → structural_change_required: false → outcome: no_change_recommended
# mission_mismatch
#   → boundary_check_result: stop_mission → outcome: stopped_mission_impact
# role_overload / missing_expertise / ambiguous_responsibility / obsolete_role
#   → structural_change_required: true → proceed to Boundary Checks
#
# Evidence insufficiency routing:
# If available evidence is insufficient to justify EITHER:
#   (a) structural_change_required = true, OR
#   (b) structural_change_required = false,
# then outcome = deferred_insufficient_evidence (see § 11).
# Skip Boundary Checks and Proposed Change.
#
# Typical indicators (sufficient signal, not exhaustive necessary conditions):
#   - confidence = low
#   - supporting_archive_paths = []
#   - evidence is indirect, stale, or contradictory
#   - evidence supports symptom but not structural responsibility gap
#   - recurrence_count too low to distinguish temporary spike from structural gap

## 5. Boundary Checks
mission_contract_impact: false
governance_impact: false
governance_impact_targets: []
team_evolution_rules_impact: false
archive_integrity_impact: false
cross_checkpoint_dependency: false
boundary_check_result: pass | stop_mission | stop_governance | stop_team_evolution_rules | stop_archive_integrity

# Boundary check routing rules:
# stop_mission → outcome: stopped_mission_impact, no patch produced
# stop_governance / stop_team_evolution_rules → outcome: stopped_governance_impact, no patch produced
# archive_integrity_impact: true / cross_checkpoint_dependency: true
#   → boundary_check_result: stop_archive_integrity → outcome: stopped_governance_impact
#   → no patch produced
# pass → proceed to Proposed Change

## 6. Proposed Change
change_type: NONE | ADD_ROLE | MODIFY_ROLE | SPLIT_ROLE | DEPRECATE_ROLE
change_subtype: none | responsibility_clarification | capability_adjustment
               | authority_adjustment | workload_split | specialist_addition
               | role_deprecation
target_roles: []
proposed_roster_patch_path: "archive/checkpoint-N/team-roster.patch.md"
proposed_roster_patch_summary: <brief human-readable description of the patch>
expected_benefit: <description>
risks: <description>
rollback_plan_summary: <brief description referencing snapshot>

# change_type: NONE is used when outcome is rejected_invalid_trigger,
# no_change_recommended, stopped_mission_impact, stopped_governance_impact,
# or deferred_insufficient_evidence.

## 7. Human Approval
# Approval gate is determined by change impact, not requested_mode.
#
# human_approval_required = true when ANY of the following:
#   - change_type = DEPRECATE_ROLE
#   - change_type = SPLIT_ROLE
#   - change_type = MERGE_ROLE (future)
#   - change affects responsibility boundaries of multiple existing roles
#   - change affects Orchestrator coordination model
#   - change requires mission-contract modification
#   - requested_mode = rollback
#
# human_approval_required = false when ALL of the following:
#   - change_type = ADD_ROLE
#   - no existing role's responsibility boundary is changed
#   - Orchestrator coordination model is unaffected
#   → Orchestrator approval sufficient
#
human_approval_required: true | false
approver: <identifier>
approval_status: pending | approved | rejected
approval_timestamp: <ISO 8601 timestamp>
approval_notes: <optional>
approval_record_path: <path to approval record>

## 8. Application
applied_at: <ISO 8601 timestamp>
applied_by: <identifier>
approval_reference: <path to approval record>
patch_reference: "archive/checkpoint-N/team-roster.patch.md"
snapshot_reference: "archive/checkpoint-N/team-roster.snapshot.md"
pre_apply_hash: <sha256 of team-roster.md before patch>
post_apply_hash: <sha256 of team-roster.md after patch>
patch_hash: <sha256 of patch file>
snapshot_hash: <sha256 of snapshot file>
approval_status_at_application: approved
application_mode: apply_approved_patch | none
validator_status: passed | failed | skipped
application_record_path: "archive/checkpoint-N/team-evolution-application.md"

# Application sequence:
# 1. human_approval_required confirmed (or Orchestrator approval if not required)
# 2. snapshot team-roster.md → archive/checkpoint-N/team-roster.snapshot.md
# 3. apply patch → team-roster.md
# 4. produce team-evolution-application.md
# 5. status = applied
# 6. if handoff team assumptions became stale → produce current/team-context-patch.md

## 9. Rollback
rollback_requested: false
rollback_at: <ISO 8601 timestamp>
rollback_by: <identifier>
rollback_approval_status: pending | approved | rejected
rollback_approval_reference: <path>
rollback_source: "archive/checkpoint-N/team-roster.snapshot.md"
pre_rollback_hash: <sha256 of team-roster.md before rollback>
post_rollback_hash: <sha256 of team-roster.md after rollback>
rollback_validator_status: passed | failed | skipped
rollback_record_path: "archive/checkpoint-N/team-evolution-rollback.md"

# Rollback constraints:
# rollback_source must be within the same checkpoint-N archive
# cross-checkpoint rollback is not permitted in MVP
# rollback always requires human approval (see § 7)

## 10. Outcome
status: rejected_invalid_trigger | no_change_recommended | stopped_mission_impact
        | stopped_governance_impact | deferred_insufficient_evidence
        | proposal_ready | applied | rolled_back
active_files_modified: []
archive_files_created: []
archive_files_referenced: []
patch_generated: false
roster_modified: false
snapshot_available: false
snapshot_path: null
rollback_applied: false
rollback_source: null
team_context_patch_generated: false
team_context_patch_path: null

# team_context_patch_generated: true only when:
#   status = applied
#   AND the applied roster change makes current/handoff-package.md team assumptions stale
#
# team-evolution owns the stale-assumption check.
# Generate team-context-patch.md when ANY of the following is true:
#   - handoff-package assigns next-phase work to a role that was removed, split,
#     renamed, or materially modified
#   - handoff-package describes responsibility routing that changed after roster
#     application
#   - newly added role should participate in the immediate next execution phase
#   - prior handoff assumptions about verifier/executor/orchestrator routing are
#     no longer accurate
#
# Do NOT generate team-context-patch.md when:
#   - added role is optional or future-facing with no next-phase involvement
#   - change only affects long-term roster clarity with no routing impact
#   - no next-phase routing or responsibility assumption in handoff is affected
#
# The patch reconciles stale handoff assumptions with the updated roster.
# team-roster.md remains the source of truth; the patch does not override it.

## 11. Recommended Followup
recommended_followup: none | reroute_to_replanning | collect_additional_evidence
                     | wait_until_next_checkpoint | human_review
recommended_followup_rationale: <brief explanation>

# Constraint: if trigger_source_type = replanning_output,
#   recommended_followup must NOT be reroute_to_replanning.
#   Use human_review or collect_additional_evidence instead.
#   Rationale: prevents replanning → team-evolution → replanning loop.
#
# Typical mappings (non-exhaustive):
#   no_change_recommended (diagnosis_type = plan_flaw)     → reroute_to_replanning
#   no_change_recommended (diagnosis_type = temp_spike)    → none
#   deferred_insufficient_evidence                         → collect_additional_evidence
#   stopped_mission_impact                                 → human_review
#   applied                                                → none

# Outcome state constraints:
# rejected_invalid_trigger:
#   active_files_modified: []
#   archive_files_created: [team-evolution-rejection.md]
#   patch_generated: false, roster_modified: false
#   team_context_patch_generated: false
#
# no_change_recommended:
#   active_files_modified: []
#   archive_files_created: [team-evolution-report.md]
#   patch_generated: false, roster_modified: false
#   team_context_patch_generated: false
#
# deferred_insufficient_evidence:
#   active_files_modified: []
#   archive_files_created: [team-evolution-report.md]
#   patch_generated: false, roster_modified: false
#   team_context_patch_generated: false
#   NOTE: report documents what evidence is missing and required followup
#
# stopped_mission_impact:
#   active_files_modified: []
#   archive_files_created: [team-evolution-escalation.md]
#   patch_generated: false, roster_modified: false
#   team_context_patch_generated: false
#
# stopped_governance_impact:
#   active_files_modified: []
#   archive_files_created: [team-evolution-escalation.md]
#   patch_generated: false, roster_modified: false
#   team_context_patch_generated: false
#
# proposal_ready:
#   active_files_modified: []
#   archive_files_created: [team-evolution-report.md, team-roster.patch.md]
#   patch_generated: true, roster_modified: false
#   team_context_patch_generated: false
#
# applied:
#   active_files_modified: [team-roster.md]
#   active_files_modified (conditional): [current/team-context-patch.md]
#   archive_files_created: [team-roster.snapshot.md, team-evolution-application.md]
#   archive_files_referenced: [team-evolution-report.md, team-roster.patch.md]
#   patch_generated: true, roster_modified: true
#   team_context_patch_generated: true | false (conditional)
#
# rolled_back:
#   active_files_modified: [team-roster.md]
#   archive_files_created: [team-evolution-rollback.md]
#   archive_files_referenced: [team-evolution-report.md, team-roster.patch.md,
#                               team-roster.snapshot.md, team-evolution-application.md]
#   patch_generated: true, roster_modified: true
#   team_context_patch_generated: false
#   NOTE: rollback removes team-context-patch.md from current/ if it was generated

## 12. Orchestrator Startup Rule
# Before beginning the next execution phase after team-evolution, Orchestrator MUST read:
#   1. .agent-org/current/handoff-package.md
#   2. .agent-org/team-roster.md
#   3. .agent-org/current/team-context-patch.md  (if present)
#
# team-context-patch.md supplements and reconciles stale team-related assumptions
# in handoff-package.md. It does not replace team-roster.md.
# team-roster.md is always the source of truth for role definitions.
#
# team-context-patch.md is archived at the next checkpoint closure by checkpoint-review.
# checkpoint-review is responsible for archiving and removing it from current/.
