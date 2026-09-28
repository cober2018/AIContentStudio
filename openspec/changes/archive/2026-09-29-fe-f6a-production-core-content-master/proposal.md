## Why

AIContentStudio now has a durable product shell, ContentProject, Identity, persistent Workflow execution, project-first Review/Distribution, Opportunity/Learning, and System Assets/Settings. Production is the next major gap.

The current `ProductionDesigner` is a strong control-plane shell (IdentitySnapshot + Workflow Run/Debugger + Shared Assets), but the actual content layer is still shallow:
- text only lists Draft/Candidate outputs and leaves editing in the legacy Draft stack;
- graphic only lists generated image/chart/screenshot revisions;
- video only lists Draft scripts and video material revisions;
- project Candidate v3 freeze only accepts Draft-backed `ProjectWorkflowOutput`, so non-text modalities cannot become first-class Candidates without pretending to be Draft.

F6A introduces the common production revision model that Text/Graphic/Video will all use before specialized editors are built.

## What Changes

- Add append-only `ContentMasterRevision` as the production revision root for one ContentUnit × modality.
- Pin exact IdentitySnapshot, CreativeBrief revision, Project Fact Boundary revision, channel/content form, and production provenance on every Master revision.
- Add immutable `ContentMasterAssetRef` and `ContentMasterEvidenceRef` so shared MaterialRevision and frozen evidence can be referenced without copying bytes/text.
- Add append-only `ContentMasterCheckRun` for Master-level deterministic/semantic/human check results.
- Add a `ProductionModalityAdapter` contract for `text`, `graphic`, and `video` payload validation, readiness, preview/render snapshot, and packaging.
- Define minimal versioned payload envelopes for all three modalities without implementing the final Text/Graphic/Video editors yet.
- Add Candidate manifest schema v4 that freezes one exact ContentMasterRevision and its context/assets/evidence/check/render/provenance.
- Evolve project Candidate freeze to accept either legacy Draft output (v3) or ContentMasterRevision (v4).
- Preserve v1/v2/v3 Candidate, Draft, MotherRevision, legacy Topic, and old delivery histories without backfill or guessed linkage.
- Add `ContentAsset.content_master_revision_id`; make non-text v4 Candidates valid without requiring Draft/MotherRevision provenance.
- Promote `video` to a real artifact kind.
- Extend local package/review/diff/read models to understand v4 without requiring remote publisher support.
- Refactor Production Workspace into reusable core shell components plus modality extension points while keeping the current Workflow mini-canvas behavior.
- Keep F5C canonical archive/sync as a hard apply prerequisite.
- Preserve post-F5C canonical blocks and close Master-only history, idempotency, source/render lineage, legacy-access and schema-version dispatch boundaries before implementation.

## Audit baseline and authorization

Local audit: `main@661e30a`, FE-F5C archived, both new F5C canonical specs present, Alembic code head `f5c000000001` (read-only `heads`, not a migration). External connector freshness remains unverified. This phase is specification-only; apply and targeted test-code generation require explicit user confirmation. No business code, test code, migration execution, push, deployment or canonical sync in this phase.

## Capabilities

### New Capabilities

- `production-content-master`: append-only ContentMasterRevision, context/assets/evidence/check lineage, modality adapters, stale/readiness projection, and v4 Candidate source contract.

### Modified Capabilities

- `fe-f2-persistent-production-workflow`: Workflow-produced outputs can seed ContentMasterRevision; Production Workspace becomes a reusable core shell with modality adapters.
- `fe-f3a-content-project-core`: Project Versions/Overview include ContentMasterRevision and derived production staleness/readiness.
- `fe-f3b-content-identity`: every new Master revision pins the exact IdentitySnapshot and never resolves latest identity in place for historical production.
- `fe-f4-project-review-distribution`: Candidate v4 freezes ContentMasterRevision while preserving v3 Draft freeze compatibility and existing approval/delivery separation.

## Impact

Backend:
- additive ContentMaster tables and ContentAsset link;
- modality adapter/readiness services;
- v4 Candidate freeze/diff/package support;
- no destructive rewrite of Draft/MotherRevision.

Frontend:
- Production Workspace component split;
- generic current Master / revision history / readiness UI;
- Review v4 preview/check/diff compatibility.

This change intentionally does NOT implement the full Text editor, Graphic canvas editor, or Video timeline. Those are follow-up F6B/F6C/F6D slices.
