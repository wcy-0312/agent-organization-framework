# Agent Organization Framework

A governance framework for structured multi-agent task execution. Defines how agent teams organize, operate, hand off context, and evolve — without becoming a bureaucracy.

---

## Project Purpose

Most multi-agent systems either have no governance (chaos at scale) or too much (agents blocked waiting for rules that don't exist). This framework occupies the middle ground:

- **Lean governance** — a small set of rules with explicit gaps handled by documented discretion
- **Intentional forgetting** — not all information is worth carrying forward; the handoff layer is designed to filter
- **Separation of concerns** — governance files live in `.agent-org/`, task artifacts live in the workspace; never mixed
- **Rules from practice** — patterns must appear in 3+ cases before becoming rules; no top-down rule invention

This framework also includes an upstream plan-formulation skill that helps users turn early ideas into structured, reviewable plans and canonical handoff packages ready for agent organization creation.

---

## Architecture Overview

```
project-root/
└── .agent-org/
    ├── mission-contract.md        ← ROOT: goal, scope, constraints (almost never changes)
    ├── team-roster.md             ← Who the agents are and what they do
    ├── governance-rules.md        ← When and how files can be revised
    ├── review-protocol.md         ← Checkpoint triggers and acceptance criteria
    ├── replanning-rules.md        ← Minor / Moderate / Major finding classification
    ├── team-evolution-rules.md    ← When the team composition can change
    ├── artifact-backend.md        ← GitHub / local-git / folder — how artifacts flow
    ├── artifact-manifest.md       ← Unified index of all task outputs
    ├── discard-log.md             ← Auditable record of intentionally discarded information
    ├── current/
    │   ├── staging-buffer.md      ← Running queue during execution (cleared each checkpoint)
    │   └── handoff-package.md     ← Minimum-necessary context for the next phase
    ├── archive/
    │   └── checkpoint-N/          ← Archived staging-buffer and handoff from prior checkpoints
    └── memory/
        ├── decision-log.md        ← Cross-task Orchestrator discretionary decisions
        └── case-library/          ← Manually curated non-trivial cases
```

**Four layers:**

| Layer | Files | Cadence |
|-------|-------|---------|
| Governance | mission-contract, team-roster, rules | Rarely — high threshold |
| Execution | staging-buffer, handoff-package | Every checkpoint |
| Artifact | artifact-backend, artifact-manifest | Per artifact submission |
| Memory | decision-log, case-library | Manually promoted across tasks |

---

## What Is Implemented (v0.1)

- [x] Architecture specification (`architecture/agent-team-organization-v1.0.md`)
- [x] `plan-formulation` skill — turns rough ideas into reviewable plan documents and canonical handoff packages
- [x] `schemas/plan-handoff-package-v1.md` — interface contract between plan-formulation and create-agent-organization
- [x] `create-agent-organization` skill — generates `.agent-org/` from a finalized plan
- [x] `checkpoint-review` skill — closes execution phases: classifies staging-buffer, produces minimal handoff-package, guides Verifier audit, archives checkpoint, and resets for next phase
- [x] `schemas/checkpoint-review-v1.md` — interface contract for checkpoint-review outputs
- [x] `replanning` skill — adjusts execution plan after checkpoint escalation; handles Moderate plan adjustments and Major mission revision candidates with two-gate human approval
- [x] `schemas/replanning-v1.md` — interface contract for replanning outputs
- [x] All 10 governance templates (`templates/`)
- [x] Layer documentation (`docs/`)

---

## What Is Not Yet Implemented

The following capabilities are defined in the architecture but not yet built as skills:

| Capability | Status |
|------------|--------|
| Team evolution workflow | Architecture defined, no skill |
| Memory retrieval | Architecture defined, no skill |
| Full organization manager | Addressed by OQ-001 — initializer only for now |
| Orchestrator manager skill | Defined in team-roster template only |

---

## Open Questions

From `architecture/agent-team-organization-v1.0.md`:

**OQ-001 — Generator vs. Manager?**
Is the skill purely an initializer, or should it evolve into an ongoing Organization Manager? Currently: initializer only.

**OQ-002 — Case Library at Scale**
When case-library grows to 1000+ entries: indexing, retrieval, relevance selection?

**OQ-003 — Role-Level Memory**
Should individual roles (e.g., Python Expert Executor) accumulate their own memory separate from org-level memory?

**OQ-004 — Vector/Semantic Memory**
Does the memory layer eventually need embedding-based retrieval? Current design is markdown + manual curation.

**OQ-005 — checkpoint-review patch archival responsibility**
`checkpoint-review` must archive `current/team-context-patch.md`
(if present) at checkpoint closure, and remove it from `current/`.
This was deferred from v0.4. Target: v0.4.1 or v0.5 prep.

---

## Roadmap

✅ **v0.2 — Checkpoint Review Skill** _(complete)_
A skill that guides the Orchestrator through staging-buffer classification, handoff-package production, and archive management.

✅ **v0.3 — Replanning Skill** _(complete)_
A skill that consumes checkpoint-review escalation and adjusts the execution plan; handles Moderate plan adjustments and Major mission revision candidates with two-gate human approval.

✅ **v0.4 — Team Evolution Skill** _(complete)_
A skill that processes team-evolution proposals and updates the roster.
Includes patch-revision to schemas/team-evolution-v1.md and
team-evolution-artifacts-v1.md, validator updates (Rules 11–13),
and Orchestrator startup rule in architecture spec.

**v1.0 — Full Organization Manager**
Addresses OQ-001: a persistent Orchestrator skill that manages the full lifecycle, not just initialization.

---

## Usage

The framework follows a sequential lifecycle:

1. **Plan formulation** — Run the `plan-formulation` skill to turn a rough idea into a reviewed `plan.md` and a canonical `plan-handoff-package.yaml`
2. **Validate handoff package** — Run `tools/validate_plan_handoff.py` against the generated YAML to confirm schema compliance before proceeding
3. **Create agent organization** — Run the `create-agent-organization` skill pointing at the validated handoff package; this generates `.agent-org/` with all governance files
4. **Orchestrator execution** — Hand `.agent-org/current/handoff-package.md` to your Orchestrator agent; it reads all governance files and drives task execution
5. **Checkpoint review** — At each decision point or phase boundary, run the `checkpoint-review` skill to classify the staging buffer, produce a minimal handoff package, and archive the checkpoint
6. **Replanning** — Only when `checkpoint-review` escalates a finding (Moderate or Major severity); run the `replanning` skill to adjust the execution plan or initiate a mission revision via two-gate human approval

---

## Repository Structure

```
agent-organization-framework/
├── architecture/
│   └── agent-team-organization-v1.0.md   ← canonical architecture spec
├── schemas/
│   ├── plan-handoff-package-v1.md        ← interface contract: plan-formulation → create-agent-organization
│   ├── checkpoint-review-v1.md           ← interface contract: checkpoint-review outputs
│   └── replanning-v1.md                  ← interface contract: replanning outputs
├── skills/
│   ├── plan-formulation/
│   │   └── SKILL.md                      ← upstream planning skill
│   ├── create-agent-organization/
│   │   └── SKILL.md                      ← initialization skill
│   ├── checkpoint-review/
│   │   └── SKILL.md                      ← phase-close and checkpoint skill
│   └── replanning/
│       └── SKILL.md                      ← escalation-driven replanning skill
├── tools/
│   └── validate_plan_handoff.py          ← schema validator for handoff packages
├── templates/                             ← all 10 governance file templates
├── docs/                                  ← layer-by-layer documentation
├── examples/                              ← (empty, for future worked examples)
└── README.md
```
