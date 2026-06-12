# Staging Buffer

> Checkpoint: _[N]_ — _[phase description]_
> Status: ACTIVE (cleared at checkpoint review)

---

## Purpose

This file is the execution-phase information queue. Any agent may write here during execution. At checkpoint review, every entry must be classified and the file cleared.

---

## How to Write an Entry

Each entry must include all four fields. Do not paste full documents or long transcripts — summarize.

```
## Entry [sequential number]

**Summary:** [one or two sentences — what happened or was discovered]
**Source:** [which agent, which step, which artifact_id if applicable]
**Why It May Matter:** [what decision or risk this could affect]
**Artifact Ref:** [artifact_id if applicable, or —]
```

---

## Entries

_[Agents append entries here during execution. This section starts empty.]_

---

## Checkpoint Review Actions

At checkpoint review, the Orchestrator and Verifier Lead classify every entry:

| Classification | Destination |
|----------------|-------------|
| Must Carry Forward | → `current/handoff-package.md` |
| Archive Only | → `archive/checkpoint-N/staging-buffer.md` |
| Promote to Memory | → `memory/decision-log.md` or `memory/case-library/` |
| Discard | → `discard-log.md` (with reason) |

After classification, this file is cleared and a new empty one is created for the next checkpoint.
