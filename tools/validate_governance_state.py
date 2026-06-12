#!/usr/bin/env python3
"""
validate_governance_state.py — Validate a governance-state.md or governance-history.md
against the governance-state-machine-v1 schema contract.

Usage:
    python tools/validate_governance_state.py <path-to-file>

Supports:
    - governance-state.md  (YAML front matter): checks Rules 1, 2, 3, 5
    - governance-history.md (front matter + Transition Log body): checks Rules 4, 5, 6

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

FSM_VERSION = "v1"

VALID_STATES = {
    "EXECUTING",
    "REVIEW_REQUIRED",
    "PLAN_RECOVERY_REQUIRED",
    "TEAM_RECOVERY_REQUIRED",
    "HUMAN_DECISION_REQUIRED",
    "COMPLETED",
    "ABORTED",
}

TERMINAL_STATES = {"COMPLETED", "ABORTED"}

# For events that resolve via pop_queue_or_EXECUTING, the concrete `to` value
# recorded in history may be any of these states (depending on queue contents).
POP_QUEUE_VALID_TO = {
    "EXECUTING",
    "PLAN_RECOVERY_REQUIRED",
    "TEAM_RECOVERY_REQUIRED",
    "HUMAN_DECISION_REQUIRED",
}

# Transition table: (from_state, event) -> concrete_to OR "pop_queue_or_EXECUTING"
# None as from_state represents the initialization transition (YAML null from).
TRANSITION_TABLE = {
    (None, "initialization"):                                    "EXECUTING",
    ("EXECUTING", "severity_minor"):                             "EXECUTING",
    ("EXECUTING", "severity_moderate"):                          "REVIEW_REQUIRED",
    ("EXECUTING", "severity_major"):                             "REVIEW_REQUIRED",
    ("EXECUTING", "mission_completed"):                          "COMPLETED",
    ("REVIEW_REQUIRED", "severity_minor"):                       "EXECUTING",
    ("REVIEW_REQUIRED", "severity_moderate"):                    "PLAN_RECOVERY_REQUIRED",
    ("REVIEW_REQUIRED", "severity_major"):                       "PLAN_RECOVERY_REQUIRED",
    ("REVIEW_REQUIRED", "team_issue_blocking"):                  "TEAM_RECOVERY_REQUIRED",
    ("REVIEW_REQUIRED", "team_issue_nonblocking"):               "PLAN_RECOVERY_REQUIRED",
    ("PLAN_RECOVERY_REQUIRED", "replanning_plan_revised"):               "pop_queue_or_EXECUTING",
    ("PLAN_RECOVERY_REQUIRED", "replanning_minor_adjustment"):           "pop_queue_or_EXECUTING",
    ("PLAN_RECOVERY_REQUIRED", "replanning_mission_revision_candidate"): "HUMAN_DECISION_REQUIRED",
    ("PLAN_RECOVERY_REQUIRED", "replanning_rejected"):                   "HUMAN_DECISION_REQUIRED",
    ("TEAM_RECOVERY_REQUIRED", "team_evolution_applied"):                "pop_queue_or_EXECUTING",
    ("TEAM_RECOVERY_REQUIRED", "team_evolution_no_change_recommended"):  "pop_queue_or_EXECUTING",
    ("TEAM_RECOVERY_REQUIRED", "team_evolution_proposal_human_required"):"HUMAN_DECISION_REQUIRED",
    ("TEAM_RECOVERY_REQUIRED", "team_evolution_stopped_mission"):        "HUMAN_DECISION_REQUIRED",
    ("TEAM_RECOVERY_REQUIRED", "team_evolution_stopped_governance"):     "HUMAN_DECISION_REQUIRED",
    ("TEAM_RECOVERY_REQUIRED", "team_evolution_deferred"):               "HUMAN_DECISION_REQUIRED",
    ("HUMAN_DECISION_REQUIRED", "human_approved"):                       "pop_queue_or_EXECUTING",
    ("HUMAN_DECISION_REQUIRED", "human_rejected"):                       "ABORTED",
    ("HUMAN_DECISION_REQUIRED", "human_mission_revised"):                "PLAN_RECOVERY_REQUIRED",
    ("HUMAN_DECISION_REQUIRED", "human_mission_abandoned"):              "ABORTED",
}

# Recovery states (non-terminal, non-EXECUTING) — used in deadlock detection.
RECOVERY_STATES = {
    "REVIEW_REQUIRED",
    "PLAN_RECOVERY_REQUIRED",
    "TEAM_RECOVERY_REQUIRED",
    "HUMAN_DECISION_REQUIRED",
}


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def load_front_matter(path):
    """Load YAML front matter and body from a markdown file with --- delimiters.

    Returns (front_matter_dict, body_text).
    Returns ({}, full_content) if no valid front matter is found.
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    stripped = content.lstrip()
    if not stripped.startswith("---"):
        return {}, content

    lines = stripped.splitlines()
    close_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close_idx = i
            break

    if close_idx is None:
        return {}, content

    front_matter_text = "\n".join(lines[1:close_idx])
    body_text = "\n".join(lines[close_idx + 1:])

    try:
        front_matter = yaml.safe_load(front_matter_text)
        if not isinstance(front_matter, dict):
            return {}, content
    except yaml.YAMLError:
        return {}, content

    return front_matter, body_text


def extract_transition_log(body):
    """Extract the YAML transition list from the '## Transition Log' section.

    Returns a list of transition dicts on success, [] if the section is empty,
    or None if the section is absent or malformed.
    """
    match = re.search(r'##\s+Transition Log\s*\n(.*)', body, re.DOTALL)
    if not match:
        return None

    log_text = match.group(1).strip()
    if not log_text:
        return []

    try:
        parsed = yaml.safe_load(log_text)
    except yaml.YAMLError:
        return None

    if isinstance(parsed, list):
        return parsed
    return None


def detect_file_type(path, front_matter):
    """Detect whether the file is a governance-state or governance-history file.

    Uses filename first, then falls back to content heuristics.
    """
    basename = os.path.basename(path)
    if "governance-state" in basename:
        return "state"
    if "governance-history" in basename:
        return "history"
    # Content-based fallback
    if "current_state" in front_matter:
        return "state"
    return "history"


# ---------------------------------------------------------------------------
# Rules — governance-state.md (Rules 1, 2, 3)
# ---------------------------------------------------------------------------

def rule1_valid_current_state(front_matter):
    """Check that current_state is a known valid FSM state."""
    state = front_matter.get("current_state")
    if state is None:
        return [
            "MISSING_FIELD — current_state is absent from governance-state.md front matter"
        ]
    if state not in VALID_STATES:
        return [
            f"INVALID_STATE — current_state '{state}' is not a valid FSM state; "
            f"expected one of: {', '.join(sorted(VALID_STATES))}"
        ]
    return []


def rule2_valid_queue_entries(front_matter):
    """Check that each entry in pending_queue is a valid FSM state."""
    queue = front_matter.get("pending_queue")
    if queue is None:
        return []
    if not isinstance(queue, list):
        return ["INVALID_QUEUE — pending_queue must be a YAML list"]

    errors = []
    for i, entry in enumerate(queue):
        if entry not in VALID_STATES:
            errors.append(
                f"INVALID_QUEUE_ENTRY — pending_queue[{i}] '{entry}' is not a valid FSM state"
            )
    return errors


def rule3_queue_length(front_matter):
    """Check that pending_queue does not exceed the maximum length of 2."""
    queue = front_matter.get("pending_queue") or []
    if not isinstance(queue, list):
        return []  # Rule 2 already flags non-list
    if len(queue) > 2:
        return [
            f"QUEUE_OVERFLOW — pending_queue has {len(queue)} entries; "
            f"maximum allowed is 2 (see schemas/governance-state-machine-v1.md §5)"
        ]
    return []


# ---------------------------------------------------------------------------
# Rules — both file types (Rule 5)
# ---------------------------------------------------------------------------

def rule5_fsm_version(front_matter):
    """Check that fsm_version matches the expected schema version (v1)."""
    version = front_matter.get("fsm_version")
    if version is None:
        return [
            "MISSING_FIELD — fsm_version is absent from front matter"
        ]
    if str(version) != FSM_VERSION:
        return [
            f"VERSION_MISMATCH — fsm_version '{version}' does not match "
            f"schema version '{FSM_VERSION}'"
        ]
    return []


# ---------------------------------------------------------------------------
# Rules — governance-history.md (Rules 4, 6)
# ---------------------------------------------------------------------------

def rule4_transition_legality(transitions):
    """Check that each transition has a valid (from, event, to) tuple per the Transition Table.

    For events that map to pop_queue_or_EXECUTING in the schema, the recorded `to`
    must be a member of POP_QUEUE_VALID_TO (the concrete resolved state).
    """
    if transitions is None:
        return [
            "MISSING_TRANSITION_LOG — governance-history.md must contain "
            "a '## Transition Log' section with a valid YAML list"
        ]

    errors = []

    for i, t in enumerate(transitions):
        raw_from = t.get("from")
        event = t.get("event")
        to = t.get("to")

        # YAML null deserialises to Python None; treat it as the null from-state.
        from_state = None if raw_from is None else raw_from

        key = (from_state, event)
        if key not in TRANSITION_TABLE:
            errors.append(
                f"ILLEGAL_TRANSITION — transitions[{i}]: "
                f"({raw_from!r}, {event!r}) is not a recognized (from, event) pair "
                f"in the Transition Table"
            )
            continue

        expected_to = TRANSITION_TABLE[key]

        if expected_to == "pop_queue_or_EXECUTING":
            if to not in POP_QUEUE_VALID_TO:
                errors.append(
                    f"ILLEGAL_TRANSITION — transitions[{i}]: "
                    f"event '{event}' from '{raw_from}' resolves via pop_queue_or_EXECUTING; "
                    f"recorded 'to' is '{to}' which is not a valid resolved state "
                    f"(expected one of: {', '.join(sorted(POP_QUEUE_VALID_TO))})"
                )
        else:
            if to != expected_to:
                errors.append(
                    f"ILLEGAL_TRANSITION — transitions[{i}]: "
                    f"({raw_from!r}, {event!r}) → '{to}' is invalid; "
                    f"expected '{expected_to}'"
                )

    return errors


def rule6_deadlock_detection(transitions):
    """Detect 3 or more consecutive failed recovery cycles.

    A failed cycle is a transition where `from` is a recovery state and `to`
    is not EXECUTING or COMPLETED. 3 or more consecutive failed cycles indicate
    a deadlock condition as defined in schemas/governance-state-machine-v1.md §6.
    """
    if not transitions:
        return []

    consecutive_failed = 0
    max_consecutive_failed = 0

    for t in transitions:
        to = t.get("to")
        from_state = t.get("from")

        if to in {"EXECUTING", "COMPLETED"}:
            consecutive_failed = 0
        elif from_state in RECOVERY_STATES and to not in {"EXECUTING", "COMPLETED"}:
            consecutive_failed += 1
            if consecutive_failed > max_consecutive_failed:
                max_consecutive_failed = consecutive_failed

    if max_consecutive_failed >= 3:
        return [
            f"DEADLOCK_DETECTED - {max_consecutive_failed} consecutive governance cycles "
            f"exited a recovery state without returning to EXECUTING or COMPLETED; "
            f"human operator intervention required "
            f"(see schemas/governance-state-machine-v1.md section 6)"
        ]
    return []


# ---------------------------------------------------------------------------
# Validator orchestration
# ---------------------------------------------------------------------------

def validate(path, front_matter, body, file_type):
    """Run the appropriate rule set based on file type. Returns (rule_results, file_type)."""
    rule_results = []

    def run(rule_num, label, errors):
        if errors:
            for msg in errors:
                rule_results.append(("FAIL", rule_num, label, msg))
        else:
            rule_results.append(("PASS", rule_num, label, None))

    def skip(rule_num, label):
        rule_results.append(("SKIP", rule_num, label, None))

    if file_type == "state":
        run(1, "current_state is a valid FSM state", rule1_valid_current_state(front_matter))
        run(2, "pending_queue entries are valid FSM states", rule2_valid_queue_entries(front_matter))
        run(3, "pending_queue length <= 2", rule3_queue_length(front_matter))
        skip(4, "transition legality (not applicable to state file)")
        run(5, "fsm_version matches schema version", rule5_fsm_version(front_matter))
        skip(6, "deadlock detection (not applicable to state file)")
    else:
        # history file
        transitions = extract_transition_log(body)
        skip(1, "current_state (not present in history file)")
        skip(2, "pending_queue entries (not present in history file)")
        skip(3, "pending_queue length <= 2 (not present in history file)")
        run(4, "transition legality", rule4_transition_legality(transitions))
        run(5, "fsm_version matches schema version", rule5_fsm_version(front_matter))
        run(6, "deadlock detection", rule6_deadlock_detection(transitions or []))

    return rule_results


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_report(path, file_type, rule_results):
    """Print the validation report to stdout."""
    print("=== Governance State Machine Validator ===")
    print(f"File: {path}")
    print(f"Type: {file_type}")
    print()

    error_count = 0
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
    print(f"Result: {error_count} error(s), {skipped_count} rule(s) skipped")
    return error_count


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validate a governance-state.md or governance-history.md file "
            "against the governance-state-machine-v1 schema."
        )
    )
    parser.add_argument(
        "record",
        help="Path to the governance-state.md or governance-history.md file",
    )
    parser.add_argument(
        "--skip-filesystem-checks",
        action="store_true",
        help="Reserved for future filesystem-level checks (currently a no-op).",
    )
    args = parser.parse_args()
    path = args.record

    try:
        front_matter, body = load_front_matter(path)
    except FileNotFoundError:
        print(f"✗ File not found: {path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"✗ Failed to parse YAML front matter: {e}")
        sys.exit(1)

    file_type = detect_file_type(path, front_matter)
    rule_results = validate(path, front_matter, body, file_type)
    error_count = print_report(path, file_type, rule_results)
    sys.exit(0 if error_count == 0 else 1)


if __name__ == "__main__":
    main()
