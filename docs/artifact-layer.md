# Artifact Layer

The artifact layer separates task outputs from governance. The actual artifacts live in the project workspace; the governance index lives in `.agent-org/`.

---

## Files in the Artifact Layer

| Path | Purpose |
|------|---------|
| `artifact-backend.md` | Backend type and operation protocols |
| `artifact-manifest.md` | Unified index of all artifacts, regardless of backend |

---

## Design Principle: Separation of Artifact Body and Index

```
Project workspace (e.g., src/, artifacts/, benchmarks/)
    └── Artifact bodies live here (code, reports, data)

.agent-org/
    └── artifact-manifest.md  ← governance index only
```

No artifact body goes inside `.agent-org/`. No governance index goes in the workspace. The manifest links them: it records `path` (where the body lives) and `artifact_id` (the stable identifier used in all governance references).

---

## Three Backend Types

### GitHub

| Operation | How |
|-----------|-----|
| Executor submits | Opens a PR from a feature branch |
| Verifier reviews | PR review with inline comments |
| Orchestrator decides | Merges (approved) or requests changes (rejected) |

Best for: distributed teams, code artifacts, need for diff visibility.

### local-git

| Operation | How |
|-----------|-----|
| Executor submits | Commits to local branch, generates patch file |
| Verifier reviews | Reads patch file |
| Orchestrator decides | Cherry-picks (approved) or marks patch rejected |

Best for: single-machine work, offline operation, code artifacts.

### folder

| Operation | How |
|-----------|-----|
| Executor submits | Writes to `artifacts/` with version + previous_version |
| Verifier reviews | Reads manifest diff, inspects files |
| Orchestrator decides | Updates manifest review_status |

Best for: non-code artifacts (reports, benchmarks, configs), simple setup.

**Note on folder backend:** It lacks a built-in diff mechanism. Compensate by ensuring every artifact entry in the manifest has `version` and `previous_version` fields so the Verifier knows what changed between submissions.

---

## Artifact Manifest Entry Fields

| Field | Required | Description |
|-------|----------|-------------|
| artifact_id | Yes | Unique identifier (e.g., ART-001) |
| checkpoint | Yes | Which checkpoint produced this |
| type | Yes | code / config / schema / report / benchmark / prompt / test / other |
| path | Yes | Relative path from project-root |
| version | Yes | Version number (e.g., 1.0, 1.1) |
| previous_version | Yes | artifact_id of prior version, or `—` |
| produced_by | Yes | Role that created this artifact |
| review_status | Yes | See status machine below |
| checksum | Yes | SHA-256 hash |
| large_asset | Yes | true/false |
| notes | No | Optional annotation |

---

## Review Status Machine

```
pending       Executor submitted, awaiting review
   ↓
in-review     Verifier is reviewing
   ↓         ↘
approved      rejected     Orchestrator's decision
   ↓
superseded    A newer version has been approved (old stays for traceability)
```

---

## Referencing Artifacts

All references to artifacts in governance documents (handoff-package, staging-buffer, decision-log) **must use artifact_id**, not file paths. This ensures references survive file moves and renames.

```markdown
✓  See ART-007 for the baseline benchmark results.
✗  See artifacts/benchmarks/baseline_v1.csv for the results.
```
