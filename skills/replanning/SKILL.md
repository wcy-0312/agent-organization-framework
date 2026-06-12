---
name: replanning
description: >
  Adjust the execution plan after a checkpoint escalation. Use this skill when
  checkpoint-review produces an escalation with status replanning_candidate, or
  when the human operator explicitly routes a mission_change_candidate to
  replanning for mission revision drafting. Also triggers when the user says
  "replan", "we need to adjust the plan", "the approach needs to change",
  "let's revisit the plan", or similar after a checkpoint. Do NOT use this skill
  for minor findings — those are handled by Executor self-adjustment. Do NOT use
  this skill to modify team-roster, review-protocol, or governance-rules.
---

# Replanning Skill v0.1

You answer one question: given what the checkpoint discovered, how should the
project proceed? For Moderate findings you adjust the current execution plan.
For Major findings you draft a mission revision candidate and present it for
explicit human approval — you do not apply it autonomously.

You are not a governance editor. You are not a team-evolution skill. You do not
execute tasks. You adjust direction and record the decision.

Read `schemas/replanning-v1.md` before proceeding. That document is the
authoritative contract for all outputs this skill produces.

---

## Responsibility Boundary

**This skill owns:**
- Reading checkpoint escalation and confirming severity
- Deciding replanning scope
- Drafting revised execution plan or mission revision candidate
- Updating `current/handoff-package.md` (Moderate, and Major only after approval)
- Writing `archive/checkpoint-N/replanning-report.md`
- Appending `memory/decision-log.md`

**This skill does not own:**
- Executing tasks described in the adjusted plan
- Modifying `team-roster.md` — `team-evolution` skill (v0.4 roadmap)
- Modifying `review-protocol.md` — human operator only
- Modifying `governance-rules.md` — human operator only
- Applying mission revision without `approval_to_apply = confirmed`

---

## Outputs

All outputs conform to `schemas/replanning-v1.md`.

| Scenario | Files written |
|----------|--------------|
| **Moderate** | `current/handoff-package.md` (updated), `archive/checkpoint-N/replanning-report.md` (new), `memory/decision-log.md` (append) |
| **Major — approved** | `mission-contract.md` (updated), `current/handoff-package.md` (updated), `archive/checkpoint-N/replanning-report.md` (new), `memory/decision-log.md` (append) |
| **Major — denied or pending** | `archive/checkpoint-N/replanning-report.md` only (`result.status = blocked` or `pending_human_approval`); `current/handoff-package.md` must NOT be modified unless human explicitly provides a safe fallback |
| **Minor** | No file writes |

---

## File Access Policy

From `schemas/replanning-v1.md §8`:

**Read:** `mission-contract.md`, `replanning-rules.md`, `review-protocol.md`,
`team-evolution-rules.md`, `current/handoff-package.md`,
`archive/checkpoint-N/review-report.md`, `memory/decision-log.md`

**Write:** `current/handoff-package.md`, `archive/checkpoint-N/replanning-report.md`,
`memory/decision-log.md` (append only)

**Conditional Write:** `mission-contract.md`
Only when all three hold: `severity = major` AND `approval_to_apply = confirmed`
AND the replanning-report records the approval in `changes_applied[*].approval_ref`

**Do Not Write:** `current/staging-buffer.md`, `team-roster.md`, `governance-rules.md`,
`review-protocol.md`, `replanning-rules.md`, `team-evolution-rules.md`,
`artifact-backend.md`, `artifact-manifest.md`,
`archive/checkpoint-N/review-report.md`,
`archive/checkpoint-N/staging-buffer.md`,
`archive/checkpoint-N/handoff-package.md`

---

## Workflow

### Phase 1 — Escalation Intake & Severity Confirmation

Before reading the review report, verify that
`archive/checkpoint-N/review-report.md` exists and contains a valid `escalation`
block. If either condition is not met, halt immediately and tell the Orchestrator:

> "No valid checkpoint-review escalation source was found. Run
> `checkpoint-review` first, then invoke replanning from the resulting
> `review-report.md`."

Do not attempt ad-hoc replanning without a review-report escalation source.

Read `archive/checkpoint-N/review-report.md` in full. The `escalation` block is
the authoritative intake. The rest of the report is supporting context.

**Intake guard** — proceed only if one of the following is true:
- `escalation.status = replanning_candidate`
- `escalation.status = mission_change_candidate` AND `recommended_next_skill = replanning`
- Human operator has explicitly routed this to replanning in writing

If none apply, stop and tell the Orchestrator:
> "The escalation status does not route to replanning. The correct skill is
> `[recommended_next_skill]` or no replanning action is needed."

**Severity dispatch:**
- `minor` → stop immediately. No file writes. Tell the Orchestrator: "Severity
  is minor. The Executor should self-adjust within the current plan."
- `moderate` → continue to Phase 2 with `scope_type = checkpoint_plan_adjustment`
- `major` → continue to Phase 2 with `scope_type = mission_revision_candidate`

**Contradiction check:** If the `escalation.description` describes a mission-level
failure (e.g., a core assumption is wrong) but `severity = minor`, surface the
contradiction before proceeding. Ask the Orchestrator to correct the escalation
in the review report — do not proceed on contradictory input.

---

### Phase 2 — Replanning Scope Decision

Read `replanning-rules.md` and the full escalation description. Determine what
needs to change and how far the change needs to reach.

**For Moderate:**
Identify which parts of the current execution plan need adjustment. Before
drafting, confirm with the Orchestrator that the scope is correctly bounded — that
this is a plan adjustment, not a mission-level change in disguise. If it turns out
to be mission-level, surface that and reclassify before continuing.

**For Major:**
- Identify which sections of `mission-contract.md` may be affected and why
  mission-level change is necessary (not just plan-level)
- Present this analysis to the Orchestrator and ask for **Gate 1**:
  _"Do I have permission to draft a mission revision?"_
- If **denied**: move to Phase 4 with
  `human_approval.permission_to_draft = denied`,
  `approval_to_apply = pending`,
  and `result.status = blocked`.
  Do not modify `mission-contract.md` or `current/handoff-package.md`.
- If **confirmed**: continue to Phase 3

---

### Phase 3 — Revision Drafting

This phase produces drafts only. No files are written until Phase 4.

**For Moderate:**
- Draft the adjusted execution plan
- Draft the revised next-stage starting point for the handoff package
- Present both to the Orchestrator for confirmation before moving to Phase 4

**For Major** (Gate 1 confirmed):
- Draft proposed changes to `mission-contract.md`
- Draft the revised execution plan reflecting the new mission framing
- Present both drafts to the Orchestrator for review
- Ask for **Gate 2**: _"Do you approve applying this mission revision?"_
- If **denied**: move to Phase 4 with `approval_to_apply = denied`
- If **confirmed**: move to Phase 4 with `approval_to_apply = confirmed`

Gate 2 requires the Orchestrator to state explicit approval, not just "OK" or
"looks good." The two-gate design means Gate 1 (permission to draft) and Gate 2
(permission to apply) are separate decisions — Gate 1 confirmation does not
authorize application.

---

### Phase 4 — Apply, Archive, and Record

Apply changes based on severity and approval state. Execute steps in order.

**Archive consistency check**

Before applying any changes or writing any files in this phase, verify that
`archive/checkpoint-N/replanning-report.md` does not already exist. If it does,
halt immediately:
```
REPLANNING_REPORT_EXISTS_ERROR
archive/checkpoint-<N>/replanning-report.md already exists.
v0.1 allows only one replanning-report per checkpoint.
Manual inspection required before proceeding.
```
Do not overwrite. Do not create a second report under a different name.

**Major — Gate 1 denied path:**
1. Write `archive/checkpoint-N/replanning-report.md`
   (`result.status = blocked`, `human_approval.permission_to_draft = denied`)
2. Do not modify `mission-contract.md`
3. Do not modify `current/handoff-package.md`
4. Append `memory/decision-log.md` noting the blocked replanning attempt

**Moderate path:**
1. Update `current/handoff-package.md` with revised next-stage starting point
2. Write `archive/checkpoint-N/replanning-report.md` (`result.status = adjusted`)
3. Append `memory/decision-log.md` with the replanning decision

**Major — approved path:**
1. Update `mission-contract.md` with the approved changes
2. Update `current/handoff-package.md`
3. Write `archive/checkpoint-N/replanning-report.md`
   (`result.status = adjusted`, `human_approval.approval_to_apply = confirmed`)
4. Append `memory/decision-log.md`

**Major — denied path:**
1. Write `archive/checkpoint-N/replanning-report.md`
   (`result.status = blocked`, `human_approval.approval_to_apply = denied`)
2. Do not modify `mission-contract.md`
3. Do not modify `current/handoff-package.md` unless the human has explicitly
   provided a safe fallback next action; if they have, update accordingly
4. Append `memory/decision-log.md` noting the blocked attempt

**Major — pending path** (human has not responded):
1. Write `archive/checkpoint-N/replanning-report.md`
   (`result.status = pending_human_approval`)
2. Do not modify `mission-contract.md` or `current/handoff-package.md`
3. Tell the Orchestrator exactly what approval is needed before proceeding

---

## Completion Message

After Phase 4 completes, report:

- Replanning result (`adjusted` / `blocked` / `pending_human_approval`)
- Severity handled (`moderate` / `major`)
- Files written (list)
- Changes summary (what was adjusted and why)
- Human approval status (Major only: Gate 1 and Gate 2 outcomes)
- Next recommended action for the Orchestrator
