#!/usr/bin/env python3
"""
validate_plan_handoff.py — Validate a plan-handoff-package.yaml against
the plan-handoff-package-v1 schema contract.

Usage:
    python tools/validate_plan_handoff.py <path-to-plan-handoff-package.yaml>

Exit codes:
    0  — validation passed (may include SCHEMA_INCOMPLETE_WARNING)
    1  — validation failed (SCHEMA_CONFLICT_ERROR, SCHEMA_INVALID_ERROR, or field errors)
"""

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

SCHEMA_VERSION = "plan-handoff-package-v1"
DERIVATION_RULE = "plan_handoff_readiness_v1"

VALID_PLAN_STATUS = {"draft", "review_pending", "approved", "confirmed"}
VALID_CRITICALITY = {"high", "medium", "low"}
VALID_IMPORTANCE = {"high", "medium", "low"}
VALID_DECISION_STATUS = {"confirmed", "assumed", "pending"}

# Fields that must be present for readiness derivation (§10)
DERIVATION_FIELDS = [
    "plan_status",
    "open_questions",
    "information_continuity_requirements",
    "decision_log",
]


# ---------------------------------------------------------------------------
# Readiness derivation
# ---------------------------------------------------------------------------

def derive_readiness(package):
    """Apply plan_handoff_readiness_v1 to the package.

    Implements the four conditions from §10 of plan-handoff-package-v1.md.
    Returns (ready: bool, blockers: list[dict]).
    """
    blockers = []

    # Condition 1: plan_status ∈ {approved, confirmed}
    plan_status = package.get("plan_status")
    if plan_status not in {"approved", "confirmed"}:
        blockers.append({
            "type": "plan_status",
            "ref": "plan_status",
            "reason": f"plan_status is '{plan_status}'; must be 'approved' or 'confirmed'",
        })

    # Condition 2: no blocking open questions
    for oq in package.get("open_questions") or []:
        if oq.get("blocks_create_agent_organization") is True:
            blockers.append({
                "type": "open_question",
                "ref": oq.get("id", "<unknown>"),
                "reason": oq.get("question", "(no question text)"),
            })

    # Condition 3: no blocking continuity requirements
    for icr in package.get("information_continuity_requirements") or []:
        if icr.get("blocks_create_agent_organization") is True:
            blockers.append({
                "type": "continuity_requirement",
                "ref": icr.get("id", "<unknown>"),
                "reason": icr.get("must_persist", "(no description)"),
            })

    # Condition 4: no pending required decisions
    for dl in package.get("decision_log") or []:
        if dl.get("status") == "pending" and dl.get("required_for_create_agent_organization") is True:
            blockers.append({
                "type": "decision",
                "ref": dl.get("id", "<unknown>"),
                "reason": dl.get("decision", "(no decision text)"),
            })

    return (len(blockers) == 0, blockers)


# ---------------------------------------------------------------------------
# Field validation
# ---------------------------------------------------------------------------

def validate_fields(package):
    """Check required fields, enum values, and schema_version.

    Returns a list of error message strings; empty means no errors.
    """
    errors = []

    # schema_version — required, exact match
    sv = package.get("schema_version")
    if sv is None:
        errors.append("Missing required field: schema_version")
    elif sv != SCHEMA_VERSION:
        errors.append(
            f"schema_version '{sv}' does not match expected '{SCHEMA_VERSION}'"
        )

    # plan_status — required enum
    ps = package.get("plan_status")
    if ps is None:
        errors.append("Missing required field: plan_status")
    elif ps not in VALID_PLAN_STATUS:
        errors.append(
            f"plan_status '{ps}' is not valid; "
            f"must be one of: {', '.join(sorted(VALID_PLAN_STATUS))}"
        )

    # required_capabilities[*].criticality
    for i, cap in enumerate(package.get("required_capabilities") or []):
        c = cap.get("criticality")
        if c is not None and c not in VALID_CRITICALITY:
            errors.append(
                f"required_capabilities[{i}].criticality '{c}' is not valid; "
                f"must be one of: {', '.join(sorted(VALID_CRITICALITY))}"
            )

    # information_continuity_requirements[*].importance
    for i, icr in enumerate(package.get("information_continuity_requirements") or []):
        imp = icr.get("importance")
        if imp is not None and imp not in VALID_IMPORTANCE:
            errors.append(
                f"information_continuity_requirements[{i}].importance '{imp}' is not valid; "
                f"must be one of: {', '.join(sorted(VALID_IMPORTANCE))}"
            )

    # decision_log[*].status
    for i, dl in enumerate(package.get("decision_log") or []):
        s = dl.get("status")
        if s is not None and s not in VALID_DECISION_STATUS:
            errors.append(
                f"decision_log[{i}].status '{s}' is not valid; "
                f"must be one of: {', '.join(sorted(VALID_DECISION_STATUS))}"
            )

    # readiness.derivation_rule — if present, must be a supported version
    readiness = package.get("readiness")
    if isinstance(readiness, dict):
        rule = readiness.get("derivation_rule")
        if rule and rule != DERIVATION_RULE:
            errors.append(
                f"readiness.derivation_rule '{rule}' is not supported; "
                f"this validator only implements '{DERIVATION_RULE}'"
            )

    return errors


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------

def _print_blockers(blockers):
    """Print a formatted list of readiness blockers."""
    for b in blockers:
        print(f"    - [{b['type']}] {b['ref']}: {b['reason']}")


def validate(package):
    """Run all checks against the package dict. Returns exit code (0 or 1)."""

    # Field and enum validation always runs first
    field_errors = validate_fields(package)
    if field_errors:
        print("✗ Validation error(s) in required fields:")
        for e in field_errors:
            print(f"  - {e}")
        return 1

    has_readiness = "readiness" in package
    has_derivation_fields = all(f in package for f in DERIVATION_FIELDS)

    if has_readiness:
        # Case 1: readiness block present — re-derive and compare
        stored_ready = package["readiness"].get("ready_for_create_agent_organization")
        derived_ready, derived_blockers = derive_readiness(package)

        if derived_ready != stored_ready:
            print("✗ SCHEMA_CONFLICT_ERROR")
            print(
                f"  The stored readiness verdict contradicts the re-derived result "
                f"under rule {DERIVATION_RULE}."
            )
            print(f"  Stored:  ready_for_create_agent_organization = {str(stored_ready).lower()}")
            print(f"  Derived: ready_for_create_agent_organization = {str(derived_ready).lower()}")
            if derived_blockers:
                print("  Derived blockers:")
                _print_blockers(derived_blockers)
            print("  The package must be corrected by the producer before this skill can proceed.")
            return 1

        if derived_ready:
            print("✓ Validation passed")
            print("  ready_for_create_agent_organization: true")
            return 0
        else:
            print("✗ Validation failed: ready_for_create_agent_organization is false")
            print("  Blockers:")
            _print_blockers(derived_blockers)
            return 1

    elif has_derivation_fields:
        # Case 2: readiness block absent, derivation fields present — auto-derive
        print(
            f"⚠ SCHEMA_INCOMPLETE_WARNING: No readiness block found. "
            f"Derived automatically under {DERIVATION_RULE}."
        )
        derived_ready, derived_blockers = derive_readiness(package)

        if derived_ready:
            print("  ready_for_create_agent_organization: true")
            print("  This package should be corrected to include an explicit readiness block.")
            return 0
        else:
            print("  ready_for_create_agent_organization: false")
            print("  Blockers:")
            _print_blockers(derived_blockers)
            return 1

    else:
        # Case 3: readiness block absent and derivation fields also missing
        missing = [f for f in DERIVATION_FIELDS if f not in package]
        print("✗ SCHEMA_INVALID_ERROR")
        print("  The package is missing required fields and readiness cannot be derived.")
        print("  Missing fields:")
        for f in missing:
            print(f"    - {f}")
        print(f"  This package is not a valid instance of {SCHEMA_VERSION}.")
        return 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Parse CLI args, load the YAML file, and run validation."""
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <path-to-plan-handoff-package.yaml>")
        sys.exit(1)

    path = sys.argv[1]

    try:
        with open(path, "r", encoding="utf-8") as f:
            package = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"✗ File not found: {path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"✗ Failed to parse YAML: {e}")
        sys.exit(1)

    if not isinstance(package, dict):
        print("✗ SCHEMA_INVALID_ERROR: File does not parse to a YAML mapping.")
        sys.exit(1)

    sys.exit(validate(package))


if __name__ == "__main__":
    main()
