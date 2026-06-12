# Handoff Layer

The handoff layer manages information flow between checkpoints. It implements the "intentional forgetting" principle: only the minimum necessary context moves forward.

---

## Files in the Handoff Layer

| Path | Purpose |
|------|---------|
| `current/staging-buffer.md` | Running queue of potentially-relevant execution observations |
| `current/handoff-package.md` | Curated minimum-necessary context for the next phase |
| `archive/checkpoint-N/` | Archived staging-buffer and handoff-package from prior checkpoints |

---

## The Two-File Design

The split between staging-buffer and handoff-package is intentional:

**Staging buffer** = low-friction, high-volume. Any agent can write here. Entries are cheap to add and cheap to discard. This is the working memory of the current phase.

**Handoff package** = high-friction, low-volume. Only the Orchestrator produces it, only after the Verifier audits it. This is the curated signal that survives a checkpoint.

---

## Staging Buffer Rules

- Any execution agent may write to `current/staging-buffer.md` at any time
- Each entry must include: Summary, Source, Why It May Matter, Artifact Ref
- No full documents or long transcripts — summarize only
- The buffer is **cleared at every checkpoint review** — nothing automatically carries over

---

## Checkpoint Review Flow

```
1. Orchestrator + Verifier scan staging-buffer
2. Each entry classified (4 options — see below)
3. Orchestrator writes new handoff-package
4. Verifier audits handoff-package against review-protocol.md checklist
5. Old staging-buffer and handoff-package archived to archive/checkpoint-N/
6. Orchestrator evaluates: is anything in archive worth promoting to memory/?
7. New empty staging-buffer created for next checkpoint
```

---

## Entry Classification (4 Options)

| Classification | Action |
|----------------|--------|
| Must Carry Forward | Include in new `current/handoff-package.md` |
| Archive Only | Moves to `archive/checkpoint-N/staging-buffer.md` — available for lookup but not loaded |
| Promote to Memory | Write to `memory/decision-log.md` or new case-library file |
| Discard | Record in `discard-log.md` with reason |

---

## Handoff Package Constraints

The handoff-package is intentionally minimal:

- References artifacts by `artifact_id` only — never paste artifact content
- Surfacing risks is mandatory — do not bury problems in positive framing
- The "next stage starting point" must be specific enough for a fresh agent to act on immediately
- The Verifier's sign-off is required before the Orchestrator declares a checkpoint complete

---

## Archive Structure

```
archive/
├── checkpoint-1/
│   ├── staging-buffer.md    ← snapshot from that checkpoint
│   └── handoff-package.md   ← the handoff that was produced
├── checkpoint-2/
│   └── ...
```

Archives are read-only after creation. Agents consult them only when they need to trace historical decisions — not as part of normal operation.
