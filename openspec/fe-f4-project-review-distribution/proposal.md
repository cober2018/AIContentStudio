## Why

AIContentStudio already has legacy primitives for Draft checks, immutable candidate manifests/hashes, Review decisions, DeliveryTarget authorization, DeliveryAttempt idempotency/unknown handling, receipts and feedback. But the visible Review & Publish Center is Topic-centric and `/review` in the new product shell is still a placeholder.

V2 requires a Project-first chain:

`ContentProject → ContentUnit → Freeze Candidate → Content Approval → Delivery Authorization → Delivery`

FE-F4 upgrades the existing candidate/review/delivery stack instead of building a second state system.

## What Changes

- Replace `/review` placeholder with a project-first Review & Distribution Center grouped by project and unit.
- Keep Review Center as a projection; do not add a `ReviewCenter` persistence table.
- Separate Candidate freeze from Content Approval.
- Reuse `ContentAsset` as immutable Candidate storage instead of adding a parallel Candidate table, unless implementation review proves compatibility impossible.
- Add project-native Candidate manifest schema v3 with Project/Unit/IdentitySnapshot/Evidence/Workflow/Checks/Render/Media provenance.
- Extend Review to bind directly to immutable Candidate/ContentAsset when available while keeping legacy draft-bound rows.
- Treat DeliveryTarget creation as explicit Delivery Authorization; do not add a duplicate authorization table.
- Preserve DeliveryAttempt unknown/reconciliation semantics and no-auto-retry behavior.
- Integrate FE-F3B ContentAccount when available while retaining `account_ref` as a historical snapshot.
- Keep legacy `/review-publish` routes/read models for compatibility.

## Capabilities

### New
- `fe-f4-project-review-distribution`

### Modified
- `fe-f0-f1-project-experience`
- `fe-f2-persistent-production-workflow`
- `fe-f3a-content-project-core`
- `fe-f3b-content-identity`

## Impact

Backend: candidate/review/delivery services, project review read models, project event/version/overview integration, additive migration.
Frontend: new `/review` workspace and unit-level review UI.
No new publisher/provider, learning loop, Opportunity work, production deployment or production migration.
