# Team Evolution Artifacts Schema v1

> **Schema ID:** `team-evolution-artifacts-v1`
> **Status:** Stable
> **Owned by:** agent-organization-framework

---

## 1. Purpose

This schema defines the format contract for the six artifacts produced by the
`team-evolution` skill during a single execution cycle. All artifacts are stored
under `.agent-org/archive/checkpoint-N/`.

This schema exists alongside `team-evolution-v1.md`, which defines the record
structure and lifecycle. The two schemas co-evolve: a version bump in either
schema always triggers a coordinated review of the other. They are not
independently versioned.

The `validate_team_evolution.py` tool validates state artifacts structurally
(front matter fields and machine change block content). Human artifacts are
validated at the front matter level only — their prose bodies are not parsed
or structurally enforced.

---

## 2. Artifact Classification

Artifacts are divided into two categories based on their primary consumer and
the depth of validator enforcement.

### Human Artifacts (report-first)

Written for human readers. The validator checks front matter metadata fields
only. Prose body content is not parsed.

| Artifact | Outcome condition |
|---|---|
| `team-evolution-report.md` | `proposal_ready` or `no_change_recommended` |
| `team-evolution-escalation.md` | `stopped_mission_impact` or `stopped_governance_impact` |
| `team-evolution-rejection.md` | `rejected_invalid_trigger` |

### State Artifacts (record-first)

Written for machine consumption and audit trails. The validator parses both
front matter and any structured machine change blocks, and enforces
cross-artifact hash consistency constraints.

| Artifact | Outcome condition |
|---|---|
| `team-roster.patch.md` | `proposal_ready`, `applied`, or `rolled_back` |
| `team-evolution-application.md` | `applied` or `rolled_back` |
| `team-evolution-rollback.md` | `rolled_back` |

---

## 3. team-evolution-report.md

**Classification:** Human Artifact
**Outcome condition:** `proposal_ready` or `no_change_recommended`

### Front Matter

```yaml
artifact_type: team-evolution-report
schema_version: v1
checkpoint: checkpoint-N
outcome_status: proposal_ready | no_change_recommended
timestamp: <ISO8601>
```

### Body

Markdown prose. Describes the complete reasoning chain from Evidence →
Diagnosis → Boundary Check → Proposed Change (or rationale for no change).
The validator does not parse the body; all structural enforcement is via
front matter.

---

## 4. team-evolution-escalation.md

**Classification:** Human Artifact
**Outcome condition:** `stopped_mission_impact` or `stopped_governance_impact`

### Front Matter

```yaml
artifact_type: team-evolution-escalation
schema_version: v1
checkpoint: checkpoint-N
outcome_status: stopped_mission_impact | stopped_governance_impact
timestamp: <ISO8601>
```

### Body

Markdown prose. May include a `proposed_change_summary` described in natural
language. The body must not contain a `changes:` YAML block or any
machine-parseable patch structure. This constraint is enforced by the outcome
matrix (`archive_files_created` does not include `team-roster.patch.md` for
escalation outcomes) rather than by body parsing. The validator does not parse
the body.

---

## 5. team-evolution-rejection.md

**Classification:** Human Artifact
**Outcome condition:** `rejected_invalid_trigger`

### Front Matter

```yaml
artifact_type: team-evolution-rejection
schema_version: v1
checkpoint: checkpoint-N
rejection_reason: invalid_trigger_type | missing_required_evidence |
                  duplicate_trigger | out_of_scope
timestamp: <ISO8601>
```

`rejection_reason` accepts exactly four values. There is no `other` escape
hatch. When a genuinely new rejection type is encountered, the schema must be
versioned — not patched via an `other` value.

### Body

```markdown
## Original Trigger
<description of the original trigger>

## Rejection Reason
<specific explanation of why the trigger was rejected>
```

The body must not contain Diagnosis content. This record does not proceed
past the rejection gate, so no Diagnosis section is relevant or appropriate.

---

## 6. team-roster.patch.md

**Classification:** State Artifact
**Outcome condition:** `proposal_ready`, `applied`, or `rolled_back`

### Front Matter

```yaml
artifact_type: team-roster-patch
schema_version: v1
checkpoint: checkpoint-N
patch_format: structured_change
changes_count: <int>
timestamp: <ISO8601>
```

Note: this file does not contain a `patch_sha256` field. The hash of this file
is recorded in `team-evolution-application.md` to avoid a self-referential hash
problem.

### Machine Change Block

The body must contain exactly one fenced code block with language marker
`yaml team-evolution-changes`. The validator uses this marker as a structural
anchor for Rules 9 and 10.

````markdown
## Machine Change Block

```yaml team-evolution-changes
changes:
  - operation: add_agent | remove_agent | modify_agent
    agent_id: "<string>"
    summary: "<one-line human-readable description>"
    fields_modified: []
```
````

**Operation rules:**

| operation | `fields_modified` |
|---|---|
| `add_agent` | must be `[]` or omitted |
| `remove_agent` | must be `[]` or omitted |
| `modify_agent` | must be a non-empty list |

The `changes_count` front matter field must equal the number of entries in the
`changes` list. The validator enforces this constraint (Rule 9) and validates
each entry's operation legality (Rule 10).

The body may include before/after markdown comparison tables as a human audit
aid. A unified diff is optional. Neither is parsed by the validator.

---

## 7. team-evolution-application.md

**Classification:** State Artifact
**Outcome condition:** `applied` or `rolled_back`

### Front Matter

```yaml
artifact_type: team-evolution-application
schema_version: v1
checkpoint: checkpoint-N
applied_by: human | auto
approval_ref: <path to approval record>
patch_ref: archive/checkpoint-N/team-roster.patch.md
patch_sha256: <sha256 of team-roster.patch.md>
snapshot_ref: archive/checkpoint-N/team-roster.snapshot.md
snapshot_sha256: <sha256 of team-roster.snapshot.md>
applied_roster_sha256: <sha256 of team-roster.md after application>
timestamp: <ISO8601>
```

All hash fields (`patch_sha256`, `snapshot_sha256`, `applied_roster_sha256`)
are mandatory. The validator fails if any is null or empty (Rule 7). This file
records the hash of `team-roster.patch.md` rather than having the patch file
hash itself, which would be self-referential.

---

## 8. team-evolution-rollback.md

**Classification:** State Artifact
**Outcome condition:** `rolled_back`

### Front Matter

```yaml
artifact_type: team-evolution-rollback
schema_version: v1
checkpoint: checkpoint-N
rollback_reason: validation_failure | human_requested | post_apply_error
application_ref: archive/checkpoint-N/team-evolution-application.md
snapshot_ref: archive/checkpoint-N/team-roster.snapshot.md
restored_from_snapshot_sha256: <sha256 of snapshot used for rollback>
current_roster_sha256: <sha256 of team-roster.md after rollback>
timestamp: <ISO8601>
```

All hash fields (`restored_from_snapshot_sha256`, `current_roster_sha256`)
are mandatory. The validator fails if any is null or empty (Rule 7).

### Cross-Artifact Hash Constraints

These constraints are enforced by Rule 8 of the validator when
`--skip-filesystem-checks` is not active:

1. `restored_from_snapshot_sha256` must equal `snapshot_sha256` from the
   corresponding `team-evolution-application.md` in the same checkpoint.
2. `current_roster_sha256` must equal `restored_from_snapshot_sha256`.

Constraint 2 encodes the invariant that a rollback restores the roster to the
exact state captured in the snapshot, with no additional modifications.

---

## 9. Validator Coverage Table

| Artifact | Front matter (Rules 2/4) | Hash fields present (Rule 7) | Machine block parsed (Rules 9/10) | Cross-artifact hash (Rule 8) | Body parsed |
|---|---|---|---|---|---|
| `team-evolution-report.md` | Indirect (outcome matrix) | No | No | No | No |
| `team-evolution-escalation.md` | Indirect (outcome matrix) | No | No | No | No |
| `team-evolution-rejection.md` | Indirect (outcome matrix) | No | No | No | No |
| `team-roster.patch.md` | No | No | Yes | No | No |
| `team-evolution-application.md` | No | Yes | No | Source | No |
| `team-evolution-rollback.md` | No | Yes | No | Target | No |

**Key:**

- **Indirect (outcome matrix):** The artifact's presence is verified by Rules 2 and 4
  checking `archive_files_created` against the outcome matrix. The artifact's internal
  front matter is not parsed directly by the validator.
- **Hash fields present (Rule 7):** The validator reads the artifact and checks that
  mandatory hash fields are non-null and non-empty.
- **Machine block parsed (Rules 9/10):** The validator locates the
  `yaml team-evolution-changes` fenced block, parses the `changes` list, and
  validates count and operation legality.
- **Cross-artifact hash — Source:** `team-evolution-application.md` provides the
  `snapshot_sha256` that rollback hashes are checked against.
- **Cross-artifact hash — Target:** `team-evolution-rollback.md` fields are checked
  against the source artifact's hash values.

---

## 10. Version Note

This schema (`team-evolution-artifacts-v1`) co-evolves with `team-evolution-v1`.
A structural change to either schema requires a coordinated review of the other.
Validators in `tools/validate_team_evolution.py` implement rules for both schemas
under a single validation pass — Rules 1–6 cover the main record structure, and
Rules 7–10 cover artifact-level constraints introduced by this schema.
