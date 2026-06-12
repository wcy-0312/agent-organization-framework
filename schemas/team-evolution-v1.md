# Team Evolution Record v1
# All paths in this schema are relative to .agent-org/ unless explicitly absolute.

## 1. Metadata
schema_version: "team-evolution-v1"
record_id: <uuid>
checkpoint_id: <checkpoint-N>
created_at: <ISO 8601 timestamp>
created_by: <agent or human identifier>
skill_version: <team-evolution skill version>

## 2. Trigger
trigger_source_type: checkpoint_escalation | replanning_output | human_request | repeated_finding
trigger_source_file: <path to triggering report>
trigger_finding_id: <finding ID from source report>
trigger_finding_summary: <brief description>
trigger_legitimacy_confirmed: true | false
trigger_legitimacy_basis: <reasoning or reference>
requested_mode: evaluate_only | propose_patch | apply_approved_patch | rollback

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
# no_change_recommended, stopped_mission_impact, or stopped_governance_impact.

## 7. Human Approval
required: true | false
# required: true for apply_approved_patch and rollback modes
# required: false for evaluate_only and propose_patch modes
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
# 1. human approval confirmed
# 2. snapshot team-roster.md → archive/checkpoint-N/team-roster.snapshot.md
# 3. apply patch → team-roster.md
# 4. produce team-evolution-application.md
# 5. status = applied

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
# rollback requires explicit human approval

## 10. Outcome
status: rejected_invalid_trigger | no_change_recommended | stopped_mission_impact
        | stopped_governance_impact | proposal_ready | applied | rolled_back
active_files_modified: []
archive_files_created: []
archive_files_referenced: []
patch_generated: false
roster_modified: false
snapshot_available: false
snapshot_path: null
rollback_applied: false
rollback_source: null

# Outcome state constraints:
# rejected_invalid_trigger:
#   active_files_modified: []
#   archive_files_created: [team-evolution-rejection.md]
#   archive_files_referenced: []
#   patch_generated: false, roster_modified: false
#   snapshot_available: false, rollback_applied: false
#
# no_change_recommended:
#   active_files_modified: []
#   archive_files_created: [team-evolution-report.md]
#   archive_files_referenced: []
#   patch_generated: false, roster_modified: false
#   snapshot_available: false, rollback_applied: false
#
# stopped_mission_impact:
#   active_files_modified: []
#   archive_files_created: [team-evolution-escalation.md]
#   archive_files_referenced: []
#   patch_generated: false, roster_modified: false
#   snapshot_available: false, rollback_applied: false
#
# stopped_governance_impact:
#   active_files_modified: []
#   archive_files_created: [team-evolution-escalation.md]
#   archive_files_referenced: []
#   patch_generated: false, roster_modified: false
#   snapshot_available: false, rollback_applied: false
#
# proposal_ready:
#   active_files_modified: []
#   archive_files_created: [team-evolution-report.md, team-roster.patch.md]
#   archive_files_referenced: []
#   patch_generated: true, roster_modified: false
#   snapshot_available: false, rollback_applied: false
#
# applied:
#   active_files_modified: [team-roster.md]
#   archive_files_created: [team-roster.snapshot.md, team-evolution-application.md]
#   archive_files_referenced: [team-evolution-report.md, team-roster.patch.md]
#   patch_generated: true, roster_modified: true
#   snapshot_available: true, rollback_applied: false
#
# rolled_back:
#   active_files_modified: [team-roster.md]
#   archive_files_created: [team-evolution-rollback.md]
#   archive_files_referenced: [team-evolution-report.md, team-roster.patch.md,
#                               team-roster.snapshot.md, team-evolution-application.md]
#   patch_generated: true, roster_modified: true
#   snapshot_available: true, rollback_applied: true
