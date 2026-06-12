# Checkpoint Review Schema v1

> **Schema ID:** `checkpoint-review-v1`
> **Status:** Stable
> **Owned by:** agent-organization-framework

---

## 1. Purpose

This schema defines the interface contract for the `checkpoint-review` skill — the
process by which the Orchestrator closes a completed work phase, classifies the
contents of `current/staging-buffer.md`, produces the next `current/handoff-package.md`,
and archives the completed checkpoint.

**Relationship to `plan-handoff-package-v1`:**
`plan-handoff-package-v1` governs the boundary between planning and organization
initialization — it carries intent from `plan-formulation` into `create-agent-organization`.
`checkpoint-review-v1` governs a different boundary: the recurring transition between
execution phases inside a running `.agent-org/`. The two schemas are structurally
independent; `checkpoint-review` reads the governance files produced during
initialization but does not re-read or re-validate the original handoff package.

---

## 2. Lifecycle Position

```
plan-formulation
      │
      ▼
create-agent-organization  ──→  .agent-org/ initialized
                                       │
                          ┌────────────┘
                          │  Orchestrator executes tasks
                          │  Agents write to staging-buffer.md
                          │
                          ▼
                  checkpoint-review  ◄── (this schema)
                          │
                          ├── archive current checkpoint
                          ├── produce next handoff-package.md
                          ├── reset staging-buffer.md
                          └── escalate if needed
                                       │
                          ┌────────────┘
                          │  Orchestrator continues next phase
                          ▼
                  checkpoint-review  (next iteration)
```

`checkpoint-review` runs at every checkpoint trigger defined in
`.agent-org/review-protocol.md`. It does not run on a fixed schedule — it runs when
a trigger condition is met.

---

## 3. Canonical Outputs

Every checkpoint-review execution produces or modifies the following files, in order:

| File | Action | Condition |
|------|--------|-----------|
| `archive/checkpoint-N/staging-buffer.md` | Write (copy of current) | Always |
| `archive/checkpoint-N/handoff-package.md` | Write (newly produced) | Always |
| `archive/checkpoint-N/review-report.md` | Write (new) | Always |
| `current/handoff-package.md` | Overwrite | Always |
| `current/staging-buffer.md` | Reset to empty | Always |
| `discard-log.md` | Append | Only if entries classified `discard` exist |
| `memory/decision-log.md` | Append | Only under strict conditions — see §10 |

**`archive/checkpoint-N/handoff-package.md`** is the newly verified handoff package
produced during this checkpoint review, not the pre-review handoff package that
existed in `current/` before this review began.

**`archive/checkpoint-N/`** must be created atomically: all three archive files must
be written before `current/` files are modified. If the skill is interrupted between
archive and current writes, the operator must re-run from the archive step.

---

## 4. Checkpoint Numbering Rule

The checkpoint number `N` is derived, not manually assigned:

```
N = (count of existing archive/checkpoint-* directories) + 1
```

Rules:
- An empty `archive/` directory yields `N = 1`.
- `N` is always a positive integer with no zero-padding requirement.
- If the computed `N` already exists as a directory (`archive/checkpoint-N/` is
  present), halt immediately and report:

  ```
  ARCHIVE_INCONSISTENCY_ERROR
  Expected to create archive/checkpoint-<N> but it already exists.
  Count of existing checkpoints: <count>
  Existing directory: archive/checkpoint-<N>
  Manual inspection required before proceeding.
  ```

- Never overwrite an existing `archive/checkpoint-N/`.
- Never renumber existing checkpoints to resolve a conflict.

---

## 5. Staging Buffer Classification Labels

Every entry in `current/staging-buffer.md` must be assigned exactly one of the
following labels during checkpoint review:

| Label | Meaning |
|-------|---------|
| `must_carry_forward` | Required for the next phase to proceed correctly |
| `archive_only` | Useful for audit or retrospective but not needed next phase |
| `promote_to_memory` | Candidate for `memory/decision-log.md` (see §10 for actual promotion rules) |
| `discard` | No downstream value; record in `discard-log.md` if discarded |

**No fifth label may be introduced.** If an entry does not fit any of these four
categories, the Orchestrator must decide which is the closest fit and record the
ambiguity in the review report's `open_items` section.

---

## 6. Classification Record Schema

Each classified entry must be recorded in `archive/checkpoint-N/review-report.md`
using the following structure:

```yaml
- entry_id: "<string>"          # unique identifier for the staging-buffer entry
  classification: "<enum>"      # must_carry_forward | archive_only | promote_to_memory | discard
  rationale: "<string>"         # why this classification was chosen
  target: "<string>"            # where the information goes: handoff-package | archive | memory-candidate | discard-log
```

`target` values map to labels as follows:

| classification | target |
|----------------|--------|
| `must_carry_forward` | `handoff-package` |
| `archive_only` | `archive` |
| `promote_to_memory` | `memory-candidate` |
| `discard` | `discard-log` |

---

## 7. Handoff Package Rules

`current/handoff-package.md` produced by checkpoint-review must satisfy all of the
following:

1. **Carry only `must_carry_forward` content.** Information classified `archive_only`,
   `promote_to_memory`, or `discard` must not appear in the handoff package.

2. **Reference artifacts by `artifact_id` only.** Do not paste artifact content
   into the handoff package. Use the identifier from `artifact-manifest.md`.

3. **Surface risks and unresolved questions.** Any open risk or unresolved question
   must appear explicitly. Do not omit items because they are uncomfortable or
   unresolved — surfacing is mandatory, resolution is not.

4. **State a concrete next stage starting point.** The "next stage starting point"
   field must name a specific, actionable first step. Phrases like "continue where
   we left off" or "proceed with the plan" are not acceptable.

---

## 8. Review Report Schema

`archive/checkpoint-N/review-report.md` must contain the following sections:

```yaml
trigger:
  condition: "<string>"         # which review-protocol trigger fired
  checkpoint_number: <int>      # N as computed by §4
  timestamp: "<ISO-8601>"

classification_summary:
  total_entries: <int>
  must_carry_forward: <int>
  archive_only: <int>
  promote_to_memory: <int>
  discard: <int>

entries_classified:              # list of classification records per §6
  - entry_id: "<string>"
    classification: "<enum>"
    rationale: "<string>"
    target: "<string>"

handoff_audit_result:
  carries_only_must_carry_forward: <bool>
  artifact_refs_only: <bool>
  risks_surfaced: <bool>
  next_stage_concrete: <bool>
  notes: "<string>"              # any audit observations

memory_promotion_decisions:      # list of promote_to_memory entries and their disposition
  - entry_id: "<string>"
    recommended: <bool>          # true if recommend promoting to decision-log
    reason: "<string>"           # why this warrants promotion (or why not)

escalation:                      # see §9

open_items:                      # unresolved questions or ambiguities to carry forward
  - "<string>"
```

---

## 9. Escalation Block Schema

The `escalation` block is a required section of every review report:

```yaml
escalation:
  status: "<enum>"               # none | replanning_candidate | team_evolution_candidate | mission_change_candidate
  severity: "<enum>"             # minor | moderate | major
  description: "<string>"        # what the escalation is about; empty string if status is none
  requires_human_approval: <bool>
  recommended_next_skill: "<enum | null>"  # null | replanning | team-evolution | human-review

  # New fields for Governance State Machine integration (v0.5)
  team_issue_detected: <bool>
  # Default: false. Set to true when checkpoint-review identifies a team capability issue.

  blocking_capability_gap: <bool>
  # Default: false. Only meaningful when team_issue_detected = true.
  # Semantics: the CURRENT execution cannot safely continue because the team
  # lacks a required capability RIGHT NOW. This is not a future risk prediction.
  # Backward compatibility: absent field treated as false.
```

**`status` values:**

| Value | Meaning |
|-------|---------|
| `none` | No escalation; proceed to next phase normally |
| `replanning_candidate` | A finding may require scope or method adjustment |
| `team_evolution_candidate` | Team composition may need to change |
| `mission_change_candidate` | A finding may affect the mission-contract |

**`severity` values:**

| Value | Defined in |
|-------|-----------|
| `minor` | `.agent-org/replanning-rules.md` |
| `moderate` | `.agent-org/replanning-rules.md` |
| `major` | `.agent-org/replanning-rules.md` |

**Note:** `recommended_next_skill` is a routing hint only. It does not trigger
execution. The Orchestrator or a human operator must explicitly invoke the
recommended skill after reviewing this report.

---

## 10. Memory Promotion Boundary

`checkpoint-review` does not autonomously promote memory. The following rules govern
all writes to `memory/`:

**`memory/decision-log.md` — append permitted only when:**
1. The Orchestrator has explicitly instructed that a decision should be recorded, AND
2. The decision is a discretionary call not covered by existing governance rules.

Both conditions must hold simultaneously. If only one holds, do not append.

**`memory/case-library/` — no writes in v0.1.** Direct writes to `memory/case-library/`
are not permitted from `checkpoint-review`. To flag a case as a candidate for
case-library inclusion, record it in `review-report.md` under `memory_promotion_decisions`
with `recommended: true`. A human operator or a future skill is responsible for
acting on that recommendation.

**`promote_to_memory` classification** means "this entry is a candidate for memory
promotion." It does not mean "this entry has been promoted." The actual promotion
decision follows the two conditions above.

---

## 11. File Access Policy

### Read

`checkpoint-review` may read the following files:

- `.agent-org/mission-contract.md`
- `.agent-org/review-protocol.md`
- `.agent-org/replanning-rules.md`
- `.agent-org/team-evolution-rules.md`
- `.agent-org/artifact-manifest.md`
- `.agent-org/current/staging-buffer.md`
- `.agent-org/current/handoff-package.md`
- `.agent-org/memory/decision-log.md`

### Write

`checkpoint-review` may write to:

- `.agent-org/current/handoff-package.md` (overwrite)
- `.agent-org/current/staging-buffer.md` (reset to empty only)
- `.agent-org/archive/checkpoint-N/*` (create new directory and files)
- `.agent-org/discard-log.md` (append only)
- `.agent-org/memory/decision-log.md` (append only, strict conditions per §10)

### Do Not Write

`checkpoint-review` must never write to:

- `.agent-org/mission-contract.md`
- `.agent-org/team-roster.md`
- `.agent-org/governance-rules.md`
- `.agent-org/review-protocol.md`
- `.agent-org/replanning-rules.md`
- `.agent-org/team-evolution-rules.md`
- `.agent-org/artifact-backend.md`
- `.agent-org/artifact-manifest.md`

Any attempt to write to these files is a governance violation.

---

## 12. Archive Consistency Rules

`archive/` is an **append-only log**. The following operations are never permitted:

- Overwriting any file inside an existing `archive/checkpoint-N/`
- Deleting any `archive/checkpoint-N/` directory
- Renumbering existing checkpoints (e.g., moving `checkpoint-3` to `checkpoint-2`)
- Merging two checkpoint archives into one

If an inconsistency is detected (e.g., gaps in numbering, duplicate directories),
halt and surface the inconsistency to the Orchestrator before proceeding. Do not
attempt to auto-repair archive state.

---

## 13. Non-Goals

`checkpoint-review` explicitly does not do the following. These responsibilities
belong to other skills or to the Orchestrator:

| Out of scope | Responsible party |
|-------------|-------------------|
| Executing replanning | `replanning` skill (not yet built, v0.3 roadmap) |
| Modifying `team-roster.md` | `team-evolution` skill (not yet built, v0.4 roadmap) |
| Modifying `mission-contract.md` | Human operator only |
| Managing artifact lifecycle | Orchestrator + `artifact-manifest.md` |
| Autonomously deciding memory content | Orchestrator, under explicit instruction |
