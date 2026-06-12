# Governance Layer

The governance layer defines the rules by which an agent organization operates. It lives entirely inside `.agent-org/` and is never mixed with task artifacts.

---

## Files in the Governance Layer

| File | Stability | Purpose |
|------|-----------|---------|
| `mission-contract.md` | Very High | Root goal, scope, and hard constraints |
| `team-roster.md` | High | Agent roles, responsibilities, system prompts |
| `governance-rules.md` | Medium-High | Document revision rules and Orchestrator discretion bounds |
| `review-protocol.md` | Medium | Checkpoint triggers and acceptance criteria |
| `replanning-rules.md` | Medium | When and how to change the plan |
| `team-evolution-rules.md` | Medium-High | When and how to change the team |

---

## Design Principle: Governance Is a Rule Engine, Not a Role

Governance does not require a dedicated "governance agent." The Orchestrator enforces rules by reading governance documents and acting accordingly. If the Orchestrator makes a decision outside the rules, they must record it in `decision-log.md`. Rules are promoted from practice, not invented top-down.

---

## Stability Hierarchy

```
mission-contract.md          ← almost never changes
    ↓
team-roster.md               ← changes only after checkpoint review
governance-rules.md          ← changes only with 3-case evidence + human
    ↓
review-protocol.md           ← updated per checkpoint
replanning-rules.md          ← adjusted if severity calibration is off
team-evolution-rules.md      ← adjusted rarely
    ↓
current/handoff-package.md   ← produced fresh at each checkpoint
current/staging-buffer.md    ← cleared at each checkpoint
```

---

## Rule Promotion Path

```
Observation in practice
    → recorded in decision-log.md
    → appears in 3+ distinct cases in case-library
    → Orchestrator proposes rule promotion in writing
    → human confirms
    → governance-rules.md updated
```

The 3-case threshold exists to prevent single-instance over-generalization. "Rules are lean; cases carry complexity."

---

## What Belongs Here vs. the Workspace

| Location | Contains |
|----------|----------|
| `.agent-org/` | All governance files, manifest index, memory |
| Project workspace | All task artifacts (code, reports, data, benchmarks) |

No exceptions. Mixing these two domains breaks the separation that makes this architecture tractable.
