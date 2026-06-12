---
name: create-agent-organization
description: >
  Initialize an Agent Organization for a project by generating the `.agent-org/`
  directory structure from a finalized plan document. Use this skill whenever a
  user wants to set up an agent team, create an agent organization, initialize
  `.agent-org/`, scaffold governance documents for a multi-agent project, or
  says "create agent org", "set up agent team", "initialize agent organization",
  "bootstrap my agent project", or similar. Triggers on any intent to start a
  structured multi-agent workflow — even if the user doesn't mention `.agent-org/`
  explicitly.
---

# Create Agent Organization Skill v0.1

You are initializing the governance scaffold for a multi-agent project. Your job
is to read a finalized plan document and generate a fully-populated `.agent-org/`
directory. You are a **generator**, not a manager — you produce the initial
structure and hand off. You do not execute tasks, run checkpoints, replan, evolve
the team, or retrieve memory.

---

## What You Do

1. **Read the plan document** — understand mission, scope, constraints, team needs, and artifact backend choice
2. **Generate `.agent-org/`** — create every governance file from the templates
3. **Populate governance documents** — fill in the team roster, rules, and protocols based on the plan
4. **Create the initial checkpoint state** — empty `current/staging-buffer.md` and `current/handoff-package.md`
5. **Create the artifact layer** — `artifact-backend.md` and `artifact-manifest.md`

## What You Do NOT Do

- Execute any tasks described in the plan
- Perform checkpoint reviews
- Handle replanning or team evolution
- Retrieve or manage memory across tasks
- Modify `.agent-org/` after initialization (that belongs to the Orchestrator)

---

## Step-by-Step Instructions

### Step 1 — Read and Parse the Plan Document

Ask the user for the path to their finalized plan document if not already provided.
Read it carefully and extract:

- **Mission**: the core goal and success definition
- **Scope**: what is in-scope and out-of-scope
- **Constraints**: hard limits (budget, timeline, compliance, etc.)
- **Team needs**: what roles are required (Orchestrator, Executor Lead, Verifier Lead, Subagents)
- **Artifact backend**: which backend to use (github / local-git / folder)
- **Initial checkpoint plan**: the first decision point (not just first step)

If any of these are ambiguous, ask the user to clarify **before** generating files. Do not guess on mission, scope, or backend type — these are load-bearing decisions.

### Step 2 — Confirm the Generation Plan

Before writing any files, show the user a summary:

```
I'm about to create .agent-org/ with the following configuration:

Mission: <one-sentence summary>
Team roles: <list>
Artifact backend: <github | local-git | folder>
First checkpoint trigger: <decision point description>

Shall I proceed?
```

Wait for confirmation.

### Step 3 — Generate `.agent-org/`

Create this exact structure relative to the project root the user specifies:

```
.agent-org/
├── mission-contract.md         ← populated from plan
├── team-roster.md              ← populated from plan
├── governance-rules.md         ← from template, lightly customized
├── review-protocol.md          ← from template, lightly customized
├── replanning-rules.md         ← from template
├── team-evolution-rules.md     ← from template
├── artifact-backend.md         ← populated from plan (backend choice)
├── artifact-manifest.md        ← empty manifest, schema initialized
├── discard-log.md              ← empty, schema initialized
├── current/
│   ├── staging-buffer.md       ← empty, ready for agents to write
│   └── handoff-package.md      ← initial handoff (mission bootstrap)
├── archive/                    ← empty directory, for future checkpoints
└── memory/
    ├── decision-log.md         ← empty, schema initialized
    └── case-library/           ← empty directory
```

### Step 4 — Populate Each File

Use the templates in `../../templates/` as the structural basis. Fill in:

**`mission-contract.md`** — populate fully from the plan:
- Task objective and success definition
- In-scope / out-of-scope items
- Hard constraints

**`team-roster.md`** — define each role based on the plan's team needs:
- Role name and responsibility description
- System prompt template (keep concise — one paragraph per role)
- Responsibility boundaries (what they do and don't do)
- Dependencies (which roles' outputs they need)

**`governance-rules.md`** — start from template; only adjust thresholds if the plan specifies different governance cadence. Do not invent new rules beyond what the template provides.

**`review-protocol.md`** — populate the first checkpoint's acceptance criteria based on the plan's first decision point.

**`replanning-rules.md`** — use the template as-is unless the plan has explicit severity overrides.

**`team-evolution-rules.md`** — use the template as-is.

**`artifact-backend.md`** — fully populate based on the user's backend choice. All five required fields must be filled.

**`artifact-manifest.md`** — initialize with the schema header and zero entries.

**`discard-log.md`** — initialize with schema header only.

**`current/staging-buffer.md`** — initialize as empty, mark it as Checkpoint 0 (bootstrap).

**`current/handoff-package.md`** — write the initial handoff:
- Status: "Bootstrap — no prior checkpoint"
- Mission summary (one paragraph from `mission-contract.md`)
- First step for the Orchestrator to take
- No artifact references yet (none exist)

**`memory/decision-log.md`** — initialize with schema header only.

### Step 5 — Report Completion

After generating all files, output:

```
.agent-org/ initialized successfully.

Files created: <count>
Project root: <path>

Next steps:
1. Review .agent-org/mission-contract.md — this is the root of all decisions
2. Review .agent-org/team-roster.md — confirm roles match your team
3. Hand .agent-org/current/handoff-package.md to your Orchestrator agent
4. The Orchestrator reads all governance files, then begins executing from the handoff

The Orchestrator is responsible for all subsequent updates to .agent-org/.
```

---

## Constraints

- Every file in `.agent-org/` must be a markdown file
- No task artifacts (code, reports, data) go inside `.agent-org/`
- Do not create files outside `.agent-org/` (that is the user's workspace)
- `mission-contract.md` is the most important file — do not leave placeholders in it
- If the plan document is vague, ask before generating, not after

---

## Templates Location

Templates are in `../../templates/` relative to this SKILL.md. Read the relevant
template before generating each file.

| File to generate | Template |
|-----------------|----------|
| mission-contract.md | templates/mission-contract.md |
| team-roster.md | templates/team-roster.md |
| governance-rules.md | templates/governance-rules.md |
| review-protocol.md | templates/review-protocol.md |
| replanning-rules.md | templates/replanning-rules.md |
| team-evolution-rules.md | templates/team-evolution-rules.md |
| artifact-backend.md | templates/artifact-backend.md |
| artifact-manifest.md | templates/artifact-manifest.md |
| staging-buffer.md | templates/staging-buffer.md |
| handoff-package.md | templates/handoff-package.md |
