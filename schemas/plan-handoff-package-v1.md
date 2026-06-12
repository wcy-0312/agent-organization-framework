# Plan Handoff Package Schema v1

> **Schema ID:** `plan-handoff-package-v1`
> **Status:** Stable
> **Owned by:** agent-organization-framework

---

## 1. Purpose

This schema defines the interface contract between two skills:

| Skill | Role |
|-------|------|
| `plan-formulation` | **Producer** — populates and outputs a conforming package |
| `create-agent-organization` | **Consumer** — reads the package and uses it to scaffold `.agent-org/` |

A Plan Handoff Package is the structured object that carries everything `create-agent-organization` needs to make load-bearing decisions about team composition, workstream boundaries, and governance initialization. It is the only authorized channel through which planning intent crosses into the organization layer.

Neither skill should embed the other's logic. This schema is the seam.

---

## 2. Canonical Source Rule

**YAML is the sole authoritative source.**

When a handoff package is embedded inside a Markdown document (e.g., inside a fenced code block), that block is a **summary view** — a human-readable snapshot for review purposes only. It carries no semantic authority.

Rules that follow from this:

- If the YAML and the Markdown summary disagree, the YAML governs.
- `create-agent-organization` must parse the YAML block, not the prose.
- A package that exists only as prose (no YAML block) is not a valid instance of this schema. See §13.

---

## 3. Top-Level Fields

```yaml
schema_version: "plan-handoff-package-v1"   # required; must match this document's schema ID exactly
project_title: "<string>"                    # short human-readable name for the project
project_stage: "<string>"                    # e.g. "pre-kickoff", "phase-1", "mid-project"
plan_status: "<enum>"                        # see values below
```

### `plan_status` values

| Value | Meaning |
|-------|---------|
| `draft` | Plan is being authored; not ready for handoff |
| `review_pending` | Plan is complete but awaiting sign-off |
| `approved` | Plan has been reviewed and approved by a human or designated authority |
| `confirmed` | Plan has been approved and the producer skill has validated readiness |

Only `approved` and `confirmed` are eligible for consumption by `create-agent-organization`. See §10.

---

## 4. Required Capabilities

Declares the functional capabilities the agent organization must possess. This is the primary input for role and team design.

```yaml
required_capabilities:
  - capability: "<string>"       # what the team must be able to do
    purpose: "<string>"          # why this capability is needed in this project
    criticality: "<enum>"        # high | medium | low
```

### Field notes

- `capability` should name an ability, not a role (prefer "parallel file transformation" over "needs a Transformer agent").
- `criticality: high` means the project cannot proceed if this capability is absent. `create-agent-organization` must ensure at least one role covers every `high`-criticality capability.
- Multiple entries may share the same `capability` string if their `purpose` or `criticality` differs across contexts.

---

## 5. Suggested Workstreams

Provides the producer's recommended decomposition of work into parallel or sequential streams. These are suggestions, not mandates — `create-agent-organization` may adjust boundaries during organization design.

```yaml
suggested_workstreams:
  - id: "WS-<N>"                              # unique identifier, e.g. WS-1
    name: "<string>"                          # short label
    objective: "<string>"                     # what this workstream must accomplish
    required_capabilities:                    # list of capability strings from §4
      - "<capability-string>"
    notes_for_organization_design: "<string>" # constraints or considerations for team design
```

### Field notes

- `expected_artifacts` is **not** a field in this schema. Artifact tracking belongs to `.agent-org/artifact-manifest.md` after initialization.
- `notes_for_organization_design` is for structural observations (e.g., "this stream has high parallelism and may benefit from multiple subagents"), not task instructions.
- A workstream with no `required_capabilities` entry is valid but unusual — flag it during review.

---

## 6. Information Continuity Requirements

Declares what information must survive the transition from planning to execution. These entries protect against knowledge loss at the skill boundary.

```yaml
information_continuity_requirements:
  - id: "ICR-<N>"
    area: "<string>"                            # domain or topic area (e.g. "data model", "auth constraints")
    must_persist: "<string>"                    # the information, relationship, or distinction that must not be lost
    importance: "<enum>"                        # high | medium | low
    blocks_create_agent_organization: <bool>    # true | false
```

### Authoring rule for `must_persist`

The subject of `must_persist` must be **information, a relationship, or a distinction** — not an artifact, file, or document.

| Correct | Incorrect |
|---------|-----------|
| "The distinction between soft-delete and hard-delete in the user table" | "The ERD file must be attached" |
| "The dependency between Module A's output schema and Module B's input contract" | "The architecture document must be preserved" |
| "Which stakeholder groups have veto power over scope changes" | "The stakeholder list spreadsheet" |

If a continuity requirement can only be expressed as "keep this file," the underlying information it carries has not been articulated. Revise the entry.

---

## 7. Open Questions

Tracks unresolved questions that may affect organization design. Questions marked as blocking must be resolved before `create-agent-organization` proceeds.

```yaml
open_questions:
  - id: "OQ-<N>"
    question: "<string>"                        # the unresolved question
    owner: "<string>"                           # who is responsible for resolving it
    blocks_create_agent_organization: <bool>    # true | false
```

### Field notes

- A question `blocks_create_agent_organization: true` means `create-agent-organization` cannot make a correct structural decision without its answer.
- The `owner` field accepts a role name, a person's name, or `"producer"` (meaning the `plan-formulation` skill must resolve it before handoff).

---

## 8. Decision Log

Records decisions made during planning that are relevant to organization design. This is distinct from `.agent-org/memory/decision-log.md`, which records decisions made during execution.

```yaml
decision_log:
  - id: "DL-<N>"
    decision: "<string>"                            # what was decided
    rationale: "<string>"                           # why this decision was made
    status: "<enum>"                                # confirmed | assumed | pending
    required_for_create_agent_organization: <bool>  # true | false
```

### `status` values

| Value | Meaning |
|-------|---------|
| `confirmed` | Decision has been explicitly made and validated |
| `assumed` | Decision has been implicitly made but not formally confirmed |
| `pending` | Decision has not yet been made |

A `pending` decision with `required_for_create_agent_organization: true` is a readiness blocker. See §10.

---

## 9. Readiness

The `readiness` block communicates whether the package is safe to consume. **This is a derived field — it must not be manually authored.**

```yaml
readiness:
  ready_for_create_agent_organization: <bool>   # derived; do not set by hand
  derivation_rule: "plan_handoff_readiness_v1"  # must match the rule defined in §10
  blockers:                                     # empty list if ready_for_create_agent_organization is true
    - type: "<string>"   # "open_question" | "continuity_requirement" | "decision"
      ref: "<id>"        # e.g. OQ-2, ICR-1, DL-3
      reason: "<string>" # why this entry blocks readiness
```

Because this block is derived, it should be produced by the `plan-formulation` skill's finalization step, not written by a human author. Any manually authored `readiness` block is subject to conflict detection under §12 Case 1.

---

## 10. Readiness Derivation Rule: `plan_handoff_readiness_v1`

`ready_for_create_agent_organization` is `true` if and only if **all four** of the following conditions hold:

1. `plan_status` ∈ `{approved, confirmed}`
2. No entry in `open_questions` has `blocks_create_agent_organization: true`
3. No entry in `information_continuity_requirements` has `blocks_create_agent_organization: true`
4. No entry in `decision_log` has both `status: pending` and `required_for_create_agent_organization: true`

If any condition fails, `ready_for_create_agent_organization` is `false` and each failing entry must appear in `readiness.blockers`.

---

## 11. Version Compatibility Policy

The `readiness.derivation_rule` field names the exact rule version used to derive the readiness block. This enables forward compatibility without silent semantic drift.

Rules for consuming skills:

1. **Use the declared version.** `create-agent-organization` must evaluate the package using the rule version declared in `readiness.derivation_rule`, not its own latest version.
2. **No silent reinterpretation.** A consuming skill must not silently apply a newer rule version to a package that declares an older one. If the consuming skill only supports a newer version, it must surface this explicitly and halt.
3. **Unsupported versions must refuse.** If `create-agent-organization` does not implement the declared rule version, it must halt with a clear error rather than proceeding under a best-effort interpretation.

This policy ensures that a package's readiness verdict remains stable across skill updates.

---

## 12. Validation Behavior

When `create-agent-organization` receives a package, it must perform the following validation before proceeding:

### Case 1 — `readiness` block is present

Re-derive `ready_for_create_agent_organization` using the rule named in `readiness.derivation_rule`.

- If the re-derived result matches the stored result: proceed normally.
- If the re-derived result **contradicts** the stored result: halt immediately with:

  ```
  SCHEMA_CONFLICT_ERROR
  The stored readiness verdict contradicts the re-derived result under rule <rule_version>.
  Stored:  ready_for_create_agent_organization = <stored_value>
  Derived: ready_for_create_agent_organization = <derived_value>
  Blockers: <list>
  The package must be corrected by the producer before this skill can proceed.
  ```

### Case 2 — `readiness` block is absent, but derivation fields are present

The fields required for derivation (§10) are present, but no `readiness` block was produced.

- Automatically derive `ready_for_create_agent_organization` using `plan_handoff_readiness_v1`.
- Emit a warning before proceeding:

  ```
  SCHEMA_INCOMPLETE_WARNING
  No readiness block found. Readiness has been derived automatically under plan_handoff_readiness_v1.
  Derived: ready_for_create_agent_organization = <derived_value>
  This package should be corrected to include an explicit readiness block.
  ```

- If the derived result is `false`, halt and surface the blockers.

### Case 3 — `readiness` block is absent and derivation fields are also absent

One or more of the fields required to evaluate §10 are missing from the package.

- Halt immediately with:

  ```
  SCHEMA_INVALID_ERROR
  The package is missing required fields and readiness cannot be derived.
  Missing: <list of missing fields>
  This package is not a valid instance of plan-handoff-package-v1.
  ```

---

## 13. Free-Form Input Disclaimer

A free-form plan document — a prose writeup, a Markdown outline, a set of bullet points, a conversation transcript — is **not** an instance of this schema.

`create-agent-organization` may accept free-form input as a convenience fallback, but when it does so it is operating outside the schema contract. Any behavior in that mode is best-effort and does not carry the guarantees described in this document.

If a user provides a free-form plan and expects deterministic, schema-validated organization generation, the correct path is:

1. Run `plan-formulation` on the free-form input to produce a conforming `plan-handoff-package-v1` YAML block.
2. Pass that package to `create-agent-organization`.

Skipping step 1 means skipping the readiness check, the continuity requirements, and the decision log — all of which exist to prevent silent failures during organization initialization.
