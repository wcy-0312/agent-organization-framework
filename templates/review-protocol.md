# Review Protocol

> Stability: MEDIUM — update acceptance criteria after each checkpoint based on what was learned.

---

## Checkpoint Trigger Conditions

A checkpoint is triggered by a **decision point**, not by task completion.

Triggers include:
- A major assumption has been validated or invalidated
- A key artifact is ready for a go/no-go decision
- The team has reached a fork: continuing requires a direction choice
- An unexpected finding changes the risk profile

Checkpoints are **not** triggered by:
- Completing a step in the plan
- Finishing a subagent's work
- Hitting a time boundary (unless it coincides with a decision point)

---

## Evaluation Dimensions

For each checkpoint, the Verifier Lead evaluates submitted artifacts along these dimensions:

| Dimension | Question |
|-----------|----------|
| Correctness | Does the artifact do what it was supposed to do? |
| Completeness | Are all required parts present? |
| Consistency | Is it consistent with the mission-contract and prior decisions? |
| Risk | Does anything here introduce unacceptable risk? |

---

## Acceptance Criteria

> Fill in per-checkpoint criteria below. The first entry is always the bootstrap checkpoint.

### Checkpoint 0 — Bootstrap

Acceptance criteria: `.agent-org/` directory created and all governance files populated. Orchestrator has read handoff-package and confirmed readiness to proceed.

Declared complete by: Human or Orchestrator.

---

### Checkpoint N — [Name]

_[Add checkpoints here as the project evolves.]_

Acceptance criteria: _[specific, measurable criteria]_

Declared complete by: _[who]_

---

## Handoff-Package Audit Checklist

The Verifier Lead checks the handoff-package against this list before approving:

- [ ] Status summary is accurate (no inflated claims)
- [ ] All referenced artifact_ids exist in artifact-manifest.md
- [ ] Decisions include reasoning, not just conclusions
- [ ] Next stage starting point is unambiguous
- [ ] All known risks and open questions are surfaced
- [ ] No full artifact content is pasted into the handoff (use artifact_id references only)
