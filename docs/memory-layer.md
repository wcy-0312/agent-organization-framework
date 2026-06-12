# Memory Layer

The memory layer stores cross-task organizational experience. It lives at `.agent-org/memory/` and is the only part of `.agent-org/` that persists beyond a single task.

---

## Files in the Memory Layer

| Path | Purpose |
|------|---------|
| `memory/decision-log.md` | Every Orchestrator discretionary decision, indexed chronologically |
| `memory/case-library/` | Individual case files selected from decision-log for long-term retention |

---

## Design Principle: Intentional Forgetting

Not all information is worth keeping. The memory layer is built on the principle that **selective retention is a feature, not a limitation.** Information falls into three categories:

| Category | Definition | Destination |
|----------|------------|-------------|
| Must Carry Forward | Next agent needs this to proceed | `current/handoff-package.md` |
| Archive Only | Preserve but don't actively load | `archive/checkpoint-N/` |
| Discard | Definitively no value | `discard-log.md` (auditable) |

Memory is promoted manually — it is never automatically accumulated.

---

## `decision-log.md`

Records every time the Orchestrator exercised judgment in a situation not covered by written rules.

**Each entry format:**

```markdown
## Decision [ID]

- **Task ID / Checkpoint:** [reference]
- **Situation:** [what the Orchestrator faced]
- **Rule Coverage:** [was there an applicable rule? if so, which?]
- **Decision:** [what was decided]
- **Reasoning:** [why]
- **Outcome:** [post-hoc: did it work?]
```

This log is the **source material** for the case-library, not a substitute for it.

---

## `case-library/`

Each file is one non-trivial decision worth preserving across tasks. Cases are **manually selected** from the decision-log — the selection itself is a judgment call.

**Promotion threshold:** A pattern must appear in at least 3 distinct cases before it becomes a rule candidate. Single cases stay as cases.

---

## Open Questions (v1.0)

See `architecture/agent-team-organization-v1.0.md` OQ-002 through OQ-004:

- **OQ-002:** How does the case-library scale to 1000+ cases? (indexing, retrieval)
- **OQ-003:** Should individual roles have their own memory, separate from org memory?
- **OQ-004:** Does the memory layer eventually need vector/semantic search?

These are intentionally deferred. The current markdown-based design is the right starting point — don't over-engineer before the need is demonstrated.
