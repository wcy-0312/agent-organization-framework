# Artifact Backend

> Stability: HIGH — do not change backend type mid-task. Only between tasks with human authorization.

---

## Backend Configuration

**`backend_type`:** `_[github | local-git | folder]_`

---

## Submit Protocol (Executor)

> How the Executor Lead submits a completed work unit for review.

_[Fill in based on backend_type:]_

**GitHub:**
```
1. Create a branch: feat/<task-id>-<description>
2. Commit work to branch
3. Open a Pull Request targeting the main branch
4. Add artifact_id as PR description header
5. Update artifact-manifest.md: set review_status → pending
```

**local-git:**
```
1. Commit work to local branch
2. Generate patch file: git format-patch HEAD~1 -o artifacts/patches/
3. Record patch filename in artifact-manifest.md
4. Update artifact-manifest.md: set review_status → pending
```

**folder:**
```
1. Write output to artifacts/<checkpoint>/<artifact_id>/
2. Update artifact-manifest.md with version and previous_version
3. Set review_status → pending
```

---

## Review Protocol (Verifier)

> How the Verifier Lead reviews a submitted work unit.

**GitHub:** Review PR inline comments. Use review-protocol.md checklist.

**local-git:** Read the patch file. Use review-protocol.md checklist.

**folder:** Read manifest diff (version vs previous_version). Check artifacts/ directory. Use review-protocol.md checklist.

---

## Approve Protocol (Orchestrator)

> How the Orchestrator approves or rejects after Verifier's recommendation.

**GitHub:** Merge PR (approved) or request changes (rejected).

**local-git:** Cherry-pick commit (approved) or mark patch as rejected in manifest.

**folder:** Set artifact-manifest.md review_status to `approved` or `rejected`.

---

## Large Asset Policy

Assets over 50MB are not stored inline. Manage as follows:

- Store at: `_[specify location: e.g., shared drive, S3, local NAS]_`
- Record in artifact-manifest.md: `large_asset: true`, `path: <storage-location>`, `checksum: <sha256>`
- The artifact_id still exists in the manifest; only the content lives elsewhere

---

## Notes

_[Any project-specific notes about this backend configuration.]_
