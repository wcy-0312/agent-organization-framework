# Team Evolution Artifacts Schema v1

> **Schema ID:** `team-evolution-artifacts-v1`
> **Status:** Stable
> **Owned by:** agent-organization-framework
>
> Patch revision notes (session 2):
> - Added team-context-patch.md as a new conditional artifact
> - Added deferred_insufficient_evidence to outcome matrix
> - Updated validator coverage table

---

## 1. Purpose

This schema defines the format contract for the artifacts produced by the
`team-evolution` skill during a single execution cycle. All archive artifacts
are stored under `.agent-org/archive/checkpoint-N/`. The active artifact
`team-context-patch.md` is stored under `.agent-org/current/`.

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

Artifacts are divided into three categories.

### Human Artifacts (report-first)

Written for human readers. The validator checks front matter metadata fields
only. Prose body content is not parsed.

| Artifact | Outcome condition |
|---|---|
| `team-evolution-report.md` | `proposal_ready`, `no_change_recommended`, or `deferred_insufficient_evidence` |
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

### Active Artifacts (current/ directory)

Written to `current/` during execution. Not archived until the next
checkpoint closure, at which point `checkpoint-review` is responsible for
archiving and removing them.

| Artifact | Outcome condition | Location |
|---|---|---|
| `team-context-patch.md` | `applied` AND handoff assumptions stale | `current/` |

---

## 3. team-evolution-report.md

**Classification:** Human Artifact
**Outcome condition:** `proposal_ready`, `no_change_recommended`, or `deferred_insufficient_evidence`

### Front Matter

```yaml
artifact_type: team-evolution-report
schema_version: v1
checkpoint: checkpoint-N
outcome_status: proposal_ready | no_change_recommended | deferred_insufficient_evidence
timestamp: <ISO8601>
```

### Body

Markdown prose. Required sections vary by `outcome_status`:

**For `proposal_ready`:**
Describes the complete reasoning chain from Evidence → Diagnosis → Boundary
Check → Proposed Change.

**For `no_change_recommended`:**
Describes Evidence → Diagnosis → why structural change is not required →
recommended followup rationale.

**For `deferred_insufficient_evidence`:**
Describes what evidence was available → why it is insufficient → what specific
evidence is required before the proposal can be re-evaluated →
`recommended_followup` rationale.

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
machine-parseable patch structure. The validator does not parse the body.

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

The body must not contain Diagnosis content.

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
team_context_patch_generated: true | false
timestamp: <ISO8601>
```

All hash fields (`patch_sha256`, `snapshot_sha256`, `applied_roster_sha256`)
are mandatory. The validator fails if any is null or empty (Rule 7).

`team_context_patch_generated` records whether `current/team-context-patch.md`
was produced as part of this application. This field enables checkpoint-review
to confirm whether a patch file should be present in `current/` when archiving.

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
team_context_patch_removed: true | false
timestamp: <ISO8601>
```

All hash fields are mandatory. The validator fails if any is null or empty (Rule 7).

`team_context_patch_removed` records whether `current/team-context-patch.md`
was removed as part of rollback. If `team-evolution-application.md` records
`team_context_patch_generated: true`, then rollback must set
`team_context_patch_removed: true`. The validator enforces this constraint.

### Cross-Artifact Hash Constraints

1. `restored_from_snapshot_sha256` must equal `snapshot_sha256` from the
   corresponding `team-evolution-application.md` in the same checkpoint.
2. `current_roster_sha256` must equal `restored_from_snapshot_sha256`.

---

## 9. team-context-patch.md

**Classification:** Active Artifact
**Location:** `.agent-org/current/team-context-patch.md`
**Outcome condition:** `applied` AND handoff team assumptions became stale

### Purpose

Reconciles stale team-related assumptions in `current/handoff-package.md`
with the updated `team-roster.md`. It does not replace `team-roster.md`,
which remains the source of truth.

### Front Matter

```yaml
artifact_type: team-context-patch
schema_version: v1
checkpoint: checkpoint-N
generated_by: team-evolution
status: active
application_ref: archive/checkpoint-N/team-evolution-application.md
timestamp: <ISO8601>
```

### Body

```markdown
## Roster Change Summary
<brief description of what changed in team-roster.md>

## New / Changed Role Routing
<which roles were added, removed, or changed and what that means for task routing>

## Obsolete Handoff Assumptions
<which statements in current/handoff-package.md are now stale and how to interpret them>

## Must Apply Before Execution
<any constraints the Orchestrator must observe before starting the next phase>
```

### Lifecycle

- Created by `team-evolution` after successful application.
- Resides in `current/` while active.
- Archived to `archive/checkpoint-N+1/team-context-patch.md` at the next
  checkpoint closure.
- Removal from `current/` is the responsibility of `checkpoint-review`.
- If rollback occurs, `team-context-patch.md` must be removed from `current/`
  as part of the rollback procedure.

---

## 10. Validator Coverage Table

| Artifact | Front matter (Rules 2/4) | Hash fields present (Rule 7) | Machine block parsed (Rules 9/10) | Cross-artifact hash (Rule 8) | Body parsed |
|---|---|---|---|---|---|
| `team-evolution-report.md` | Indirect (outcome matrix) | No | No | No | No |
| `team-evolution-escalation.md` | Indirect (outcome matrix) | No | No | No | No |
| `team-evolution-rejection.md` | Indirect (outcome matrix) | No | No | No | No |
| `team-roster.patch.md` | No | No | Yes | No | No |
| `team-evolution-application.md` | No | Yes | No | Source | No |
| `team-evolution-rollback.md` | No | Yes | No | Target | No |
| `team-context-patch.md` | No | No | No | No | No |

Additional constraint for rollback: if `team-evolution-application.md` records
`team_context_patch_generated: true`, the validator checks that
`team-evolution-rollback.md` records `team_context_patch_removed: true`.

---

## 11. Version Note

This schema (`team-evolution-artifacts-v1`) co-evolves with `team-evolution-v1`.
A structural change to either schema requires a coordinated review of the other.
Validators in `tools/validate_team_evolution.py` implement rules for both schemas
under a single validation pass — Rules 1–6 cover the main record structure, and
Rules 7–10 cover artifact-level constraints introduced by this schema.
