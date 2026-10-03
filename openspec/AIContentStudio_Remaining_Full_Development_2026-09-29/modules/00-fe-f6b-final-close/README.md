# FE-F6B Final Close

This module does **not** create a second OpenSpec change.

Continue the existing active change:
`openspec/changes/fe-f6b-text-production-studio`

Verified planning state when this package was generated:
- FE-F6B: 131/162
- Backend Milestone A: PASS
- Backend Milestone B: PASS
- Professional Text Studio frontend 15–20: complete
- remaining: 31

Goal: close the existing F6B change to 162/162, commit locally, and mark ARCHIVE_READY. Canonical sync/archive still requires separate explicit authorization.

## Remaining work

### Cross-layer bridge
- 5.6 citation bind/unbind, emoji/list/repeated-use/edit/AI invalidation/range/boundary-drift acceptance
- 6.1 prove real Text Studio draft emits `text.master.v2` envelope through existing append-only Master API
- 6.3 prove atomic v2 payload + asset refs + evidence refs + verified AI provenance

### Legacy/cross-modality regression
- 21.1–21.5

### Browser acceptance
- 22.1–22.13

### Final gates
- 23.1–23.10

## Acceptance fixture

Create only in isolated test data:
- ContentProject
- IdentitySnapshot
- CreativeBrief
- frozen FactPack + FactPackItems
- Project Fact Boundary
- project-visible image MaterialRevision
- project-visible chart MaterialRevision
- Text ContentUnit
- optional real verified Draft ProjectWorkflowOutput for seed acceptance

Do not point browser acceptance at development/production data.

## Required final chain

`Text Studio
→ structured edit
→ exact image/chart
→ exact citation/evidence
→ AI suggestion + explicit accept
→ explicit Master save
→ checks
→ structured diff
→ Candidate v4
→ Review
→ Approval
→ Delivery Authorization
→ local ZIP`

The downloaded `content.md` must equal the frozen deterministic render and packaged media hashes must equal exact frozen MaterialRevision hashes.
