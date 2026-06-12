---
name: checkpoint-review
description: >
  Close a completed execution phase inside a .agent-org/ project: classify the
  staging buffer, draft a minimal handoff package, guide the Verifier Lead through
  an audit, archive the checkpoint, and reset for the next phase. Use this skill
  whenever the Orchestrator determines that a checkpoint decision point has been
  reached — a deliverable is ready for review, a risk threshold has been crossed,
  or the review-protocol.md trigger conditions are met. Also triggers when the user
  says "run checkpoint", "close this phase", "archive and hand off", "do checkpoint
  review", or "we're ready for the next phase". Do NOT use this skill to replan,
  modify governance files, or manage artifacts — this skill closes a phase, nothing
  more.
---

# Checkpoint Review Skill v0.1

You close execution phases. Your core job is a four-step compression:
**staging-buffer → minimal handoff-package → archive → reset**.

Every detail you carry forward costs the next phase context budget. Every detail you
drop that was needed causes failure. Classification — not summarization — is the
judgment call this skill exists to make.

Read `schemas/checkpoint-review-v1.md` before proceeding. That document is the
authoritative contract for all outputs this skill produces.

---

## Responsibility Boundary

**This skill owns:**
- Classifying staging-buffer entries
- Drafting the new `current/handoff-package.md`
- Guiding the Verifier Lead audit
- Archiving the completed checkpoint
- Resetting `current/staging-buffer.md`
- Marking escalation candidates

**This skill does not own** (from `schemas/checkpoint-review-v1.md §13`):
- Executing replanning — that is the `replanning` skill (v0.3 roadmap)
- Modifying `team-roster.md` — that is the `team-evolution` skill (v0.4 roadmap)
- Modifying `mission-contract.md` — human operator only
- Managing artifact lifecycle — Orchestrator + `artifact-manifest.md`
- Autonomously deciding memory content

---

## Outputs

All outputs conform to `schemas/checkpoint-review-v1.md §3`:

| File | Action |
|------|--------|
| `archive/checkpoint-N/staging-buffer.md` | Write (copy of current) |
| `archive/checkpoint-N/handoff-package.md` | Write (newly produced handoff package) |
| `archive/checkpoint-N/review-report.md` | Write (new, per §8 schema) |
| `current/handoff-package.md` | Overwrite with new package |
| `current/staging-buffer.md` | Reset to empty |
| `discard-log.md` | Append (only if discard entries exist) |
| `memory/decision-log.md` | Append (only under strict conditions — see §10) |

---

## File Access Policy

From `schemas/checkpoint-review-v1.md §11`:

**Read:** `mission-contract.md`, `review-protocol.md`, `replanning-rules.md`,
`team-evolution-rules.md`, `artifact-manifest.md`, `current/staging-buffer.md`,
`current/handoff-package.md`, `memory/decision-log.md`

**Write:** `current/handoff-package.md`, `current/staging-buffer.md` (reset only),
`archive/checkpoint-N/*`, `discard-log.md` (append), `memory/decision-log.md`
(append, strict conditions)

**Do Not Write:** `mission-contract.md`, `team-roster.md`, `governance-rules.md`,
`review-protocol.md`, `replanning-rules.md`, `team-evolution-rules.md`,
`artifact-backend.md`, `artifact-manifest.md`

---

## Workflow

### Phase 1 — Checkpoint Trigger & Readiness Validation

Read `review-protocol.md` and check whether at least one trigger condition is met.

Valid trigger conditions (from `review-protocol.md`) include:
- A core assumption was confirmed or falsified.
- A key artifact is ready for a go/no-go decision.
- The team reached a direction fork that requires choosing a path.
- A discovery changes risk, scope, method choice, or feasibility.

Not valid by itself:
- A task step was completed.
- A subagent finished work.
- Time passed or a scheduled date arrived.
- A phase label changed without a decision to make.

If no trigger condition is met, tell the Orchestrator clearly:
> "No checkpoint trigger condition is met. Continue execution and call this skill
> again when a trigger condition is reached."

Do not enter Phase 2 until at least one condition is confirmed.

Also verify that `current/staging-buffer.md` is readable and non-empty. An empty
staging buffer at a confirmed trigger is unusual — surface it before proceeding.

---

### Phase 2 — Staging Buffer Classification

Read `current/staging-buffer.md` in full, then classify every entry. No entry may
be skipped — an unclassified entry is an error, not an acceptable output state.

**Batch size:** 10 entries per batch. Reduce to 5 for long or complex entries;
raise to 15 for short or clearly routine entries. Present each batch to the
Orchestrator before moving to the next.

**Classification labels** (from `schemas/checkpoint-review-v1.md §5`):

| Label | When to use |
|-------|-------------|
| `must_carry_forward` | The next phase cannot proceed correctly without this |
| `archive_only` | Useful for audit but not needed next phase |
| `promote_to_memory` | Candidate for `memory/decision-log.md`; does not mean "promoted" |
| `discard` | No downstream value; requires an explicit rationale |

For each entry, propose a classification and rationale. The Orchestrator confirms or
corrects. Record every entry using the classification record schema from
`schemas/checkpoint-review-v1.md §6`:

```yaml
- entry_id: "<string>"
  classification: "<label>"
  rationale: "<why this classification>"
  target: "<handoff-package | archive | memory-candidate | discard-log>"
```

A `discard` classification without an explicit rationale is not acceptable — if you
cannot articulate why something has no downstream value, classify it `archive_only`
instead.

---

### Phase 3 — Handoff Package Drafting

Draft `current/handoff-package.md` using only `must_carry_forward` entries.

Rules from `schemas/checkpoint-review-v1.md §7`:
1. Include only `must_carry_forward` content — no `archive_only`, `promote_to_memory`,
   or `discard` material.
2. Reference artifacts by `artifact_id` from `artifact-manifest.md`. Do not paste
   artifact content into the handoff package.
3. Surface all open risks and unresolved questions explicitly. Do not omit them
   because they are uncomfortable or unresolved.
4. State a concrete next stage starting point — a specific, actionable first step.
   "Continue where we left off" is not acceptable.

Present the draft to the Orchestrator for review before moving to Phase 4.

---

### Phase 4 — Verifier Audit & Revision

Read `review-protocol.md` and extract the acceptance checklist for this checkpoint
type. Present the checklist to the Verifier Lead and ask them to mark each item
`pass` or `needs revision`.

For any item marked `needs revision`:
- Surface the specific concern
- Return to Phase 3 to correct the handoff package
- Re-present the corrected draft for re-audit

Do not proceed to Phase 5 until the Verifier Lead (or the user acting as Verifier)
explicitly confirms the handoff package passes. "OK" or "looks fine" without
reference to the checklist is not confirmation — ask for explicit sign-off.

---

### Phase 5 — Archive, Reset, and Escalation Marking

Execute these steps in order:

**1. Compute checkpoint number N**

```
N = (count of existing archive/checkpoint-* directories) + 1
```

If `archive/checkpoint-N` already exists, halt immediately:
```
ARCHIVE_INCONSISTENCY_ERROR
Expected to create archive/checkpoint-<N> but it already exists.
Manual inspection required before proceeding.
```
Do not attempt to auto-repair. Do not renumber existing checkpoints.

**2. Write archive files** (before touching `current/`)

- `archive/checkpoint-N/staging-buffer.md` — copy of `current/staging-buffer.md`
- `archive/checkpoint-N/handoff-package.md` — the newly verified handoff package

**3. Determine escalation status**

Before writing the review report, assess the findings from Phase 2 classification
and determine the escalation block content using the schema from
`schemas/checkpoint-review-v1.md §9`. The escalation block is part of the review
report and must be determined before the report is written, not appended afterward.

`status: none` is a valid and common result. If status is not `none`, describe the
issue and set `recommended_next_skill` to the appropriate routing hint. The hint does
not trigger execution — the Orchestrator decides whether and when to act on it.

**4. Write `archive/checkpoint-N/review-report.md`**

Follow the schema from `schemas/checkpoint-review-v1.md §8`. Write the complete
report in a single pass, including the escalation block determined in the previous
step. All sections are required.

**5. Overwrite `current/handoff-package.md`**

Replace with the verified handoff package from Phase 3–4.

**6. Reset `current/staging-buffer.md`**

Clear to empty. Preserve the file header/schema if the template has one.

**7. Append `discard-log.md`**

Only if there are `discard`-classified entries. Include `entry_id` and rationale
for each discarded item.

**8. Mark memory candidates**

For entries classified `promote_to_memory`, record them in `review-report.md`
under `memory_promotion_decisions`. Do not write to `memory/decision-log.md`
unless both strict conditions from `schemas/checkpoint-review-v1.md §10` hold:
the Orchestrator has explicitly instructed the recording, and the decision is
a discretionary call not covered by existing governance rules.

---

## Hard Constraints

- Never modify `mission-contract.md`, `team-roster.md`, `governance-rules.md`,
  `review-protocol.md`, `replanning-rules.md`, `team-evolution-rules.md`,
  `artifact-backend.md`, or `artifact-manifest.md`.
- `archive/` is append-only. Never overwrite or renumber existing checkpoints.
- On archive inconsistency, halt and report. Do not attempt self-repair.
- Memory promotion does not happen automatically. Classification as
  `promote_to_memory` is a recommendation, not an action.
- Escalation is a marking, not an execution. This skill never invokes replanning
  or team-evolution directly.

---

## Completion Message

After all Phase 5 steps complete successfully, report:

- Checkpoint number closed (e.g. "Checkpoint 3 closed")
- Files written (list)
- Classification summary (counts per label)
- Verifier audit result (pass / required revisions count)
- Escalation status (`none` / `replanning_candidate` / `team_evolution_candidate` / `mission_change_candidate`)
- Memory candidates marked, if any
- Recommended next action
