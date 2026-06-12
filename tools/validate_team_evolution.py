#!/usr/bin/env python3
"""
validate_team_evolution.py — Validate a team-evolution record against
the team-evolution-v1 schema contract.

Usage:
    python tools/validate_team_evolution.py <path-to-record.yaml|md>

Supports YAML front matter (--- delimited) or plain YAML input.

Exit codes:
    0  — all rules passed
    1  — one or more rules failed
"""

import argparse
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("Error: pyyaml is required. Install it with:")
    print("    pip install pyyaml")
    print("Or install all dependencies:")
    print("    pip install -r requirements.txt")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_STATUSES = {
    "rejected_invalid_trigger",
    "no_change_recommended",
    "deferred_insufficient_evidence",
    "stopped_mission_impact",
    "stopped_governance_impact",
    "proposal_ready",
    "applied",
    "rolled_back",
}

VALID_RECOMMENDED_FOLLOWUP = {
    "none",
    "reroute_to_replanning",
    "collect_additional_evidence",
    "wait_until_next_checkpoint",
    "human_review",
}

OUTCOME_MATRIX = {
    "rejected_invalid_trigger": {
        "patch_generated": False,
        "roster_modified": False,
        "snapshot_available": False,
        "rollback_applied": False,
        "active_files_modified": [],
        "archive_files_created": ["team-evolution-rejection.md"],
        "archive_files_referenced": [],
    },
    "no_change_recommended": {
        "patch_generated": False,
        "roster_modified": False,
        "snapshot_available": False,
        "rollback_applied": False,
        "active_files_modified": [],
        "archive_files_created": ["team-evolution-report.md"],
        "archive_files_referenced": [],
    },
    "deferred_insufficient_evidence": {
        "patch_generated": False,
        "roster_modified": False,
        "snapshot_available": False,
        "rollback_applied": False,
        "active_files_modified": [],
        "archive_files_created": ["team-evolution-report.md"],
        "archive_files_referenced": [],
    },
    "stopped_mission_impact": {
        "patch_generated": False,
        "roster_modified": False,
        "snapshot_available": False,
        "rollback_applied": False,
        "active_files_modified": [],
        "archive_files_created": ["team-evolution-escalation.md"],
        "archive_files_referenced": [],
    },
    "stopped_governance_impact": {
        "patch_generated": False,
        "roster_modified": False,
        "snapshot_available": False,
        "rollback_applied": False,
        "active_files_modified": [],
        "archive_files_created": ["team-evolution-escalation.md"],
        "archive_files_referenced": [],
    },
    "proposal_ready": {
        "patch_generated": True,
        "roster_modified": False,
        "snapshot_available": False,
        "rollback_applied": False,
        "active_files_modified": [],
        "archive_files_created": ["team-evolution-report.md", "team-roster.patch.md"],
        "archive_files_referenced": [],
    },
    "applied": {
        "patch_generated": True,
        "roster_modified": True,
        "snapshot_available": True,
        "rollback_applied": False,
        "active_files_modified": ["team-roster.md"],
        "archive_files_created": ["team-roster.snapshot.md", "team-evolution-application.md"],
        "archive_files_referenced": ["team-evolution-report.md", "team-roster.patch.md"],
    },
    "rolled_back": {
        "patch_generated": True,
        "roster_modified": True,
        "snapshot_available": True,
        "rollback_applied": True,
        "active_files_modified": ["team-roster.md"],
        "archive_files_created": ["team-evolution-rollback.md"],
        "archive_files_referenced": [
            "team-evolution-report.md",
            "team-roster.patch.md",
            "team-roster.snapshot.md",
            "team-evolution-application.md",
        ],
    },
}

ALLOWED_ACTIVE_FILES = {"team-roster.md"}

STATUSES_REQUIRING_EMPTY_ACTIVE = {
    "rejected_invalid_trigger",
    "no_change_recommended",
    "deferred_insufficient_evidence",
    "stopped_mission_impact",
    "stopped_governance_impact",
    "proposal_ready",
}

FORBIDDEN_ACTIVE_FILES = {
    "mission-contract.md",
    "governance-rules.md",
    "review-protocol.md",
    "replanning-rules.md",
    "team-evolution-rules.md",
}

BOOL_FIELDS = {"patch_generated", "roster_modified", "snapshot_available", "rollback_applied"}
LIST_FIELDS = {"active_files_modified", "archive_files_created", "archive_files_referenced"}


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def load_record(path):
    """Load a YAML record from a plain YAML file or a Markdown file with YAML front matter.

    Returns the parsed dict, or raises ValueError with a descriptive message.
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Detect YAML front matter (--- delimited)
    stripped = content.lstrip()
    if stripped.startswith("---"):
        lines = stripped.splitlines()
        # Find the closing ---
        close_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                close_idx = i
                break
        if close_idx is not None:
            front_matter = "\n".join(lines[1:close_idx])
            record = yaml.safe_load(front_matter)
            if isinstance(record, dict):
                return record

    # Try parsing the entire content as YAML
    record = yaml.safe_load(content)
    if isinstance(record, dict):
        return record

    raise ValueError("File does not parse to a YAML mapping (checked front matter and plain YAML).")


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------

def basenames(paths):
    """Return the set of basenames for a list of file paths."""
    return {os.path.basename(p) for p in (paths or [])}


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def rule1_valid_status(outcome):
    """Check that outcome.status is a known valid value."""
    status = outcome.get("status")
    if status not in VALID_STATUSES:
        return [f"INVALID_STATUS — '{status}' is not a valid outcome.status; "
                f"expected one of: {', '.join(sorted(VALID_STATUSES))}"]
    return []


def rule2_outcome_matrix(outcome):
    """Check that outcome field values match the matrix for the given status."""
    status = outcome.get("status")
    if status not in OUTCOME_MATRIX:
        return []  # Rule 1 already flagged this; skip matrix check

    expected = OUTCOME_MATRIX[status]
    errors = []

    for field in BOOL_FIELDS:
        actual = outcome.get(field)
        exp = expected[field]
        if actual != exp:
            errors.append(
                f"OUTCOME_FIELD_MISMATCH — {field}: expected {exp}, got {actual!r}"
            )

    for field in LIST_FIELDS:
        actual_bases = basenames(outcome.get(field) or [])
        exp_bases = set(expected[field])
        if actual_bases != exp_bases:
            errors.append(
                f"OUTCOME_FIELD_MISMATCH — {field}: expected basenames {sorted(exp_bases)}, "
                f"got {sorted(actual_bases)}"
            )

    return errors


def rule3_active_files(outcome):
    """Check that active_files_modified respects authorization boundaries."""
    status = outcome.get("status")
    active = outcome.get("active_files_modified") or []
    active_bases = basenames(active)
    errors = []

    if status in STATUSES_REQUIRING_EMPTY_ACTIVE and active:
        errors.append(
            f"UNAUTHORIZED_ACTIVE_MUTATION — active_files_modified must be empty "
            f"for status '{status}', got: {sorted(active_bases)}"
        )

    forbidden_found = active_bases & FORBIDDEN_ACTIVE_FILES
    for f in sorted(forbidden_found):
        errors.append(f"FORBIDDEN_FILE_MODIFIED — {f} found in active_files_modified")

    if status in {"applied", "rolled_back"}:
        unexpected = active_bases - ALLOWED_ACTIVE_FILES - FORBIDDEN_ACTIVE_FILES
        for f in sorted(unexpected):
            errors.append(
                f"UNEXPECTED_ACTIVE_FILE — {f} found in active_files_modified "
                f"but is not in the allowed set for status '{status}'"
            )

    return errors


def rule4_archive_artifacts(outcome):
    """Check that archive_files_created and archive_files_referenced match the matrix."""
    status = outcome.get("status")
    if status not in OUTCOME_MATRIX:
        return []

    expected = OUTCOME_MATRIX[status]
    errors = []

    for field in ("archive_files_created", "archive_files_referenced"):
        actual_bases = basenames(outcome.get(field) or [])
        exp_bases = set(expected[field])

        missing = exp_bases - actual_bases
        for f in sorted(missing):
            errors.append(f"MISSING_ARCHIVE_ARTIFACT — {f} required in {field} for status '{status}'")

        unexpected = actual_bases - exp_bases
        for f in sorted(unexpected):
            errors.append(f"UNEXPECTED_ARCHIVE_ARTIFACT — {f} found in {field} but not expected for status '{status}'")

    return errors


def rule5_checkpoint_scope(outcome, metadata):
    """Check that snapshot_path and rollback_source stay within the same checkpoint."""
    status = outcome.get("status")
    if status not in {"applied", "rolled_back"}:
        return []

    checkpoint_id = (metadata or {}).get("checkpoint_id", "")
    snapshot_path = outcome.get("snapshot_path") or ""
    errors = []

    # snapshot_path is required for applied and rolled_back
    if not snapshot_path:
        errors.append(
            f"MISSING_REQUIRED_FIELD — snapshot_path must be non-empty "
            f"for status '{status}'"
        )
        return errors  # skip further checks if snapshot_path is missing

    if checkpoint_id:
        path_parts = snapshot_path.replace("\\", "/").split("/")
        if checkpoint_id not in path_parts:
            errors.append(
                f"CROSS_CHECKPOINT_REFERENCE — snapshot_path '{snapshot_path}' "
                f"does not contain checkpoint_id '{checkpoint_id}' as a path segment"
            )

    if status == "rolled_back":
        rollback_source = outcome.get("rollback_source") or ""

        # rollback_source is required for rolled_back
        if not rollback_source:
            errors.append(
                f"MISSING_REQUIRED_FIELD — rollback_source must be non-empty "
                f"for status 'rolled_back'"
            )
        elif rollback_source != snapshot_path:
            errors.append(
                f"CROSS_CHECKPOINT_REFERENCE — rollback_source '{rollback_source}' "
                f"does not match snapshot_path '{snapshot_path}'"
            )

    return errors


def resolve_artifact_path(filename, base_dir, checkpoint_id):
    """Build the canonical path for an artifact file within a checkpoint archive."""
    return os.path.join(base_dir, ".agent-org", "archive", checkpoint_id, filename)


def _find_archive_file(filename, outcome, base_dir, checkpoint_id):
    """Locate a file by basename in archive_files_created or archive_files_referenced.

    Falls back to resolve_artifact_path if the filename is not found in either list.
    """
    all_files = list(outcome.get("archive_files_created") or []) + \
                list(outcome.get("archive_files_referenced") or [])
    agent_org_dir = os.path.join(base_dir, ".agent-org")
    for path in all_files:
        if os.path.basename(path) == filename:
            normalised = path.replace("\\", "/")
            if normalised.startswith(".agent-org/"):
                return os.path.join(base_dir, normalised)
            else:
                return os.path.join(agent_org_dir, normalised)
    return resolve_artifact_path(filename, base_dir, checkpoint_id)


def _extract_machine_change_block(content):
    """Find and parse the fenced block with marker 'yaml team-evolution-changes'.

    Returns the changes list (possibly empty) on success, or None if the block
    is absent or appears more than once.
    """
    pattern = r'```yaml team-evolution-changes\r?\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    if len(matches) != 1:
        return None
    try:
        parsed = yaml.safe_load(matches[0])
        if not isinstance(parsed, dict):
            return None
        changes = parsed.get("changes")
        return changes if changes is not None else []
    except yaml.YAMLError:
        return None


def rule6_referenced_artifacts_exist(outcome, metadata, base_dir):
    """Check that every file in archive_files_referenced actually exists on disk.

    Paths are resolved relative to base_dir/.agent-org/ (or base_dir if
    .agent-org/ is already part of the path).
    """
    status = outcome.get("status")
    if status not in {"applied", "rolled_back"}:
        return []

    referenced = outcome.get("archive_files_referenced") or []
    if not referenced:
        return []

    errors = []
    agent_org_dir = os.path.join(base_dir, ".agent-org")

    for ref_path in referenced:
        # Normalise separators
        normalised = ref_path.replace("\\", "/")

        # If path already starts with .agent-org/, resolve from base_dir
        if normalised.startswith(".agent-org/"):
            full_path = os.path.join(base_dir, normalised)
        else:
            full_path = os.path.join(agent_org_dir, normalised)

        if not os.path.isfile(full_path):
            errors.append(
                f"DANGLING_ARTIFACT_REFERENCE — referenced file does not exist: {ref_path}"
            )

    return errors


def rule7_hash_fields(outcome, base_dir, metadata):
    """Check that mandatory hash fields are present in state artifacts.

    Triggered when outcome.status is 'applied' or 'rolled_back'.
    For 'applied': verifies patch_sha256, snapshot_sha256, applied_roster_sha256
                   in team-evolution-application.md.
    For 'rolled_back': verifies restored_from_snapshot_sha256, current_roster_sha256
                       in team-evolution-rollback.md.
    """
    status = outcome.get("status")
    if status not in {"applied", "rolled_back"}:
        return []

    checkpoint_id = (metadata or {}).get("checkpoint_id", "")
    errors = []

    if status == "applied":
        path = resolve_artifact_path("team-evolution-application.md", base_dir, checkpoint_id)
        try:
            artifact = load_record(path)
        except (FileNotFoundError, ValueError, yaml.YAMLError):
            return []
        for field in ("patch_sha256", "snapshot_sha256", "applied_roster_sha256"):
            if not artifact.get(field):
                errors.append(
                    f"MISSING_HASH_FIELD — {field} is required for status 'applied'"
                )

    elif status == "rolled_back":
        path = resolve_artifact_path("team-evolution-rollback.md", base_dir, checkpoint_id)
        try:
            artifact = load_record(path)
        except (FileNotFoundError, ValueError, yaml.YAMLError):
            return []
        for field in ("restored_from_snapshot_sha256", "current_roster_sha256"):
            if not artifact.get(field):
                errors.append(
                    f"MISSING_HASH_FIELD — {field} is required for status 'rolled_back'"
                )

    return errors


def rule8_rollback_hash(outcome, base_dir, metadata):
    """Check cross-artifact hash consistency for rollback records.

    Triggered when outcome.status is 'rolled_back'.
    Verifies:
    1. rollback.restored_from_snapshot_sha256 == application.snapshot_sha256
    2. rollback.current_roster_sha256 == rollback.restored_from_snapshot_sha256
    """
    status = outcome.get("status")
    if status != "rolled_back":
        return []

    checkpoint_id = (metadata or {}).get("checkpoint_id", "")
    errors = []

    app_path = _find_archive_file("team-evolution-application.md", outcome, base_dir, checkpoint_id)
    rollback_path = resolve_artifact_path("team-evolution-rollback.md", base_dir, checkpoint_id)

    try:
        application = load_record(app_path)
    except (FileNotFoundError, ValueError, yaml.YAMLError):
        return []

    try:
        rollback = load_record(rollback_path)
    except (FileNotFoundError, ValueError, yaml.YAMLError):
        return []

    app_snapshot_sha256 = application.get("snapshot_sha256") or ""
    rollback_restored_sha256 = rollback.get("restored_from_snapshot_sha256") or ""
    rollback_current_sha256 = rollback.get("current_roster_sha256") or ""

    if app_snapshot_sha256 and rollback_restored_sha256:
        if rollback_restored_sha256 != app_snapshot_sha256:
            errors.append(
                "HASH_MISMATCH — rollback.restored_from_snapshot_sha256 does not match "
                "application.snapshot_sha256"
            )

    if rollback_restored_sha256 and rollback_current_sha256:
        if rollback_current_sha256 != rollback_restored_sha256:
            errors.append(
                "HASH_MISMATCH — rollback.current_roster_sha256 does not match "
                "rollback.restored_from_snapshot_sha256"
            )

    return errors


def rule9_changes_count(outcome, base_dir, metadata):
    """Check that front matter changes_count matches the Machine Change Block length.

    Triggered when outcome.status is 'proposal_ready', 'applied', or 'rolled_back'.
    """
    status = outcome.get("status")
    if status not in {"proposal_ready", "applied", "rolled_back"}:
        return []

    checkpoint_id = (metadata or {}).get("checkpoint_id", "")

    patch_path = _find_archive_file("team-roster.patch.md", outcome, base_dir, checkpoint_id)
    if not os.path.isfile(patch_path):
        return []

    with open(patch_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        front_matter = load_record(patch_path)
    except (ValueError, yaml.YAMLError):
        return []

    declared_count = front_matter.get("changes_count")

    changes = _extract_machine_change_block(content)
    if changes is None:
        return [
            "MISSING_MACHINE_CHANGE_BLOCK — team-roster.patch.md must contain "
            "exactly one fenced block with marker 'yaml team-evolution-changes'"
        ]

    actual_count = len(changes)
    if declared_count != actual_count:
        return [
            f"CHANGES_COUNT_MISMATCH — front matter declares {declared_count} changes but "
            f"Machine Change Block contains {actual_count}"
        ]

    return []


def rule10_operation_legality(outcome, base_dir, metadata):
    """Check that each change entry in the Machine Change Block is well-formed.

    Triggered when outcome.status is 'proposal_ready', 'applied', or 'rolled_back'.
    Validates operation values and fields_modified constraints per operation type.
    """
    status = outcome.get("status")
    if status not in {"proposal_ready", "applied", "rolled_back"}:
        return []

    checkpoint_id = (metadata or {}).get("checkpoint_id", "")

    patch_path = _find_archive_file("team-roster.patch.md", outcome, base_dir, checkpoint_id)
    if not os.path.isfile(patch_path):
        return []

    with open(patch_path, "r", encoding="utf-8") as f:
        content = f.read()

    changes = _extract_machine_change_block(content)
    if changes is None:
        return []  # Rule 9 already flags the missing block

    valid_operations = {"add_agent", "remove_agent", "modify_agent"}
    errors = []

    for i, change in enumerate(changes):
        operation = change.get("operation")
        fields_modified = change.get("fields_modified")

        if operation not in valid_operations:
            errors.append(
                f"INVALID_OPERATION — changes[{i}].operation '{operation}' is not valid"
            )
            continue

        if operation in {"add_agent", "remove_agent"}:
            if fields_modified:
                errors.append(
                    f"INVALID_FIELDS_MODIFIED — changes[{i}]: add_agent/remove_agent "
                    f"must have empty fields_modified"
                )
        elif operation == "modify_agent":
            if not fields_modified:
                errors.append(
                    f"INVALID_FIELDS_MODIFIED — changes[{i}]: modify_agent requires "
                    f"non-empty fields_modified"
                )

    return errors


def rule11_team_context_patch(outcome, base_dir, metadata):
    """Check team_context_patch_generated consistency.

    - If status = applied and team_context_patch_generated = true:
        active_files_modified must contain current/team-context-patch.md.
    - If status = rolled_back and the application record has
        team_context_patch_generated = true:
        the rollback record must have team_context_patch_removed = true.
    """
    status = outcome.get("status")
    errors = []

    if status == "applied":
        tcp_generated = outcome.get("team_context_patch_generated")
        if tcp_generated is True:
            active = outcome.get("active_files_modified") or []
            found = any("team-context-patch.md" in str(p) for p in active)
            if not found:
                errors.append(
                    "TEAM_CONTEXT_PATCH_MISSING — team_context_patch_generated = true "
                    "but current/team-context-patch.md not found in active_files_modified"
                )

    if status == "rolled_back":
        checkpoint_id = (metadata or {}).get("checkpoint_id", "")
        app_path = resolve_artifact_path(
            "team-evolution-application.md", base_dir, checkpoint_id
        )
        try:
            application = load_record(app_path)
        except (FileNotFoundError, ValueError, yaml.YAMLError):
            return errors

        if application.get("team_context_patch_generated") is True:
            rollback_path = resolve_artifact_path(
                "team-evolution-rollback.md", base_dir, checkpoint_id
            )
            try:
                rollback = load_record(rollback_path)
            except (FileNotFoundError, ValueError, yaml.YAMLError):
                return errors

            if rollback.get("team_context_patch_removed") is not True:
                errors.append(
                    "TEAM_CONTEXT_PATCH_NOT_REMOVED — application.team_context_patch_generated = true "
                    "but rollback.team_context_patch_removed is not true"
                )

    return errors


def rule12_recommended_followup(record):
    """Check recommended_followup field validity and loop prevention.

    - Value must be in VALID_RECOMMENDED_FOLLOWUP.
    - If trigger_source_type = replanning_output, value must not be
      reroute_to_replanning (loop prevention).
    """
    # recommended_followup may live at record root or under a "recommended_followup" section key.
    # Support both access patterns.
    section = record.get("recommended_followup")
    if isinstance(section, dict):
        followup = section.get("recommended_followup")
    else:
        followup = section

    if followup is None:
        return []  # Field absent — not enforced as mandatory here

    errors = []

    if followup not in VALID_RECOMMENDED_FOLLOWUP:
        errors.append(
            f"INVALID_RECOMMENDED_FOLLOWUP — '{followup}' is not a valid value; "
            f"expected one of: {', '.join(sorted(VALID_RECOMMENDED_FOLLOWUP))}"
        )

    trigger = record.get("trigger") or {}
    trigger_source_type = trigger.get("trigger_source_type")
    if trigger_source_type == "replanning_output" and followup == "reroute_to_replanning":
        errors.append(
            "LOOP_PREVENTION_VIOLATION — recommended_followup = reroute_to_replanning "
            "is forbidden when trigger_source_type = replanning_output"
        )

    return errors


def rule13_human_approval_required(record):
    """Check human_approval_required is set correctly for high-impact changes.

    - change_type = DEPRECATE_ROLE → human_approval_required must be true.
    - requested_mode = rollback → human_approval_required must be true.
    """
    trigger = record.get("trigger") or {}
    proposed_change = record.get("proposed_change") or {}
    human_approval = record.get("human_approval") or {}

    change_type = proposed_change.get("change_type")
    requested_mode = trigger.get("requested_mode")
    human_approval_required = human_approval.get("human_approval_required")

    errors = []

    if change_type == "DEPRECATE_ROLE" and human_approval_required is not True:
        errors.append(
            "APPROVAL_REQUIRED_MISSING — change_type = DEPRECATE_ROLE requires "
            "human_approval_required = true"
        )

    if requested_mode == "rollback" and human_approval_required is not True:
        errors.append(
            "APPROVAL_REQUIRED_MISSING — requested_mode = rollback requires "
            "human_approval_required = true"
        )

    return errors


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate(record, path, base_dir, skip_filesystem=False):
    """Run all rules. Returns (results, status)."""
    outcome = record.get("outcome") or {}
    metadata = record.get("metadata") or {}
    # Note: rule12 and rule13 receive the full record to access trigger/proposed_change/human_approval sections.
    status = outcome.get("status", "<missing>")

    rule_results = []

    def run(rule_num, label, errors):
        if errors:
            for msg in errors:
                rule_results.append(("FAIL", rule_num, label, msg))
        else:
            rule_results.append(("PASS", rule_num, label, None))

    run(1, "outcome.status is valid", rule1_valid_status(outcome))
    run(2, "outcome field matrix", rule2_outcome_matrix(outcome))
    run(3, "active_files_modified authorization", rule3_active_files(outcome))
    run(4, "archive artifact completeness", rule4_archive_artifacts(outcome))
    run(5, "snapshot/rollback checkpoint scope", rule5_checkpoint_scope(outcome, metadata))

    if skip_filesystem:
        rule_results.append(("SKIP", 6, "referenced artifact existence (skipped)", None))
    else:
        run(6, "referenced artifact existence", rule6_referenced_artifacts_exist(outcome, metadata, base_dir))

    run(7, "state artifact hash fields", rule7_hash_fields(outcome, base_dir, metadata))

    if skip_filesystem:
        rule_results.append(("SKIP", 8, "rollback hash consistency (skipped)", None))
    else:
        run(8, "rollback hash consistency", rule8_rollback_hash(outcome, base_dir, metadata))

    run(9, "patch changes_count consistency", rule9_changes_count(outcome, base_dir, metadata))
    run(10, "patch operation legality", rule10_operation_legality(outcome, base_dir, metadata))
    run(11, "team_context_patch consistency", rule11_team_context_patch(outcome, base_dir, metadata))
    run(12, "recommended_followup validity", rule12_recommended_followup(record))
    run(13, "human_approval_required for high-impact changes", rule13_human_approval_required(record))

    return rule_results, status


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_report(path, status, rule_results):
    """Print the validation report to stdout."""
    print("=== Team Evolution Validator ===")
    print(f"File: {path}")
    print(f"Status: {status}")
    print()

    error_count = 0
    warning_count = 0
    skipped_count = 0

    for tag, rule_num, label, msg in rule_results:
        if tag == "PASS":
            print(f"[PASS] Rule {rule_num}: {label}")
        elif tag == "SKIP":
            print(f"[SKIP] Rule {rule_num}: {label}")
            skipped_count += 1
        else:
            print(f"[FAIL] Rule {rule_num}: {msg}")
            error_count += 1

    print()
    print("---")
    print(f"Result: {error_count} error(s), {warning_count} warning(s), {skipped_count} rule(s) skipped")
    return error_count


# ---------------------------------------------------------------------------
# Repository root detection
# ---------------------------------------------------------------------------

def find_repo_root(start_path):
    """Find the repository root by walking upward until .agent-org/ exists."""
    current = os.path.abspath(os.path.dirname(start_path))

    while True:
        if os.path.isdir(os.path.join(current, ".agent-org")):
            return current

        parent = os.path.dirname(current)
        if parent == current:
            raise ValueError("Could not find repository root containing .agent-org/")

        current = parent


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate a team-evolution record against the team-evolution-v1 schema."
    )
    parser.add_argument("record", help="Path to the record file (.yaml or .md)")
    parser.add_argument(
        "--skip-filesystem-checks",
        action="store_true",
        help="Skip Rule 6 filesystem existence checks (schema-only validation mode).",
    )
    args = parser.parse_args()
    path = args.record
    skip_filesystem = args.skip_filesystem_checks

    try:
        record = load_record(path)
        base_dir = find_repo_root(path)
    except FileNotFoundError:
        print(f"✗ File not found: {path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"✗ Failed to parse YAML: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"✗ {e}")
        sys.exit(1)
    rule_results, status = validate(record, path, base_dir, skip_filesystem=skip_filesystem)
    error_count = print_report(path, status, rule_results)
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
