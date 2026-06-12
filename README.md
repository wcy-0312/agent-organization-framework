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
- [x] All 10 governance templates (`templates/`)
- [x] Layer documentation (`docs/`)

---

## What Is Not Yet Implemented

The `create-agent-organization` skill handles initialization only. The following are defined in the architecture but not yet built as skills:

| Capability | Status |
|------------|--------|
| Checkpoint review | Architecture defined, no skill |
| Replanning execution | Architecture defined, no skill |
| Team evolution workflow | Architecture defined, no skill |
| Memory retrieval | Architecture defined, no skill |
| Orchestrator system prompt | Defined in team-roster template only |

See `OQ-001` in the architecture doc: the framework is currently a **generator**, not a **manager**. The Orchestrator is expected to operate the framework after initialization.

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

---

## Roadmap

✅ **v0.2 — Checkpoint Review Skill** _(complete)_
A skill that guides the Orchestrator through staging-buffer classification, handoff-package production, and archive management.

**v0.3 — Replanning Skill** ← _current target_
A skill that classifies a finding's severity and executes the appropriate replanning protocol.

**v0.4 — Team Evolution Skill**
A skill that processes team-evolution proposals and updates the roster.

**v1.0 — Full Organization Manager**
Addresses OQ-001: a persistent Orchestrator skill that manages the full lifecycle, not just initialization.

---

## Usage

1. Write a finalized plan document describing your mission, team needs, and artifact backend
2. Run the `create-agent-organization` skill pointing at your plan
3. Review `.agent-org/mission-contract.md` and `.agent-org/team-roster.md`
4. Hand `.agent-org/current/handoff-package.md` to your Orchestrator agent
5. The Orchestrator reads all governance files and begins execution

---

## Repository Structure

```
agent-organization-framework/
├── architecture/
│   └── agent-team-organization-v1.0.md   ← canonical architecture spec
├── schemas/
│   └── plan-handoff-package-v1.md        ← handoff interface contract
├── skills/
│   ├── plan-formulation/
│   │   └── SKILL.md                      ← upstream planning skill
│   └── create-agent-organization/
│       └── SKILL.md                      ← initialization skill
├── templates/                             ← all 10 governance file templates
├── docs/                                  ← layer-by-layer documentation
├── examples/                              ← (empty, for future worked examples)
└── README.md
```
