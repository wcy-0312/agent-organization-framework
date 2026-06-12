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
    "stopped_mission_impact",
    "stopped_governance_impact",
    "proposal_ready",
    "applied",
    "rolled_back",
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


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate(record, path, base_dir, skip_filesystem=False):
    """Run all rules. Returns (results, status)."""
    outcome = record.get("outcome") or {}
    metadata = record.get("metadata") or {}
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
