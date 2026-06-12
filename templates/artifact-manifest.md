# Artifact Manifest

> This is the governance index. All artifact references use artifact_id. Never reference artifacts by path alone.

---

## Status Machine

```
pending → in-review → approved
                    ↘ rejected → (Executor revises) → pending
approved → superseded (when a new version is approved)
```

---

## Entries

<!-- Add one entry per artifact. Copy the template below. -->

<!--
| Field | Value |
|-------|-------|
| artifact_id | [unique id, e.g. ART-001] |
| checkpoint | [checkpoint number] |
| type | code \| config \| schema \| report \| benchmark \| prompt \| test \| other |
| path | [relative path from project-root] |
| version | [e.g. 1.0] |
| previous_version | [artifact_id of prior version, or —] |
| produced_by | [role name] |
| review_status | pending \| in-review \| approved \| rejected \| superseded |
| checksum | [sha256] |
| large_asset | true \| false |
| notes | [optional] |
-->

_No artifacts yet. Entries will be added during execution._
