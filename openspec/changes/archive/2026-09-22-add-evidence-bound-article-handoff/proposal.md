## Why

AIContentStudio can generate and approve channel drafts, but its frozen FactPack still points at mutable facts, final media may be added after approval, and export/publish state does not prove that the approved content was the content handed to a specific account. Before expanding to more article channels, the first release needs one trustworthy path from an existing satisfactory article to complete WeChat and X Thread packages, manual publishing receipts, and feedback.

## What Changes

- Extend the existing FactPack boundary with typed, immutable evidence snapshots for facts/events, third-party quotations, and author opinions without treating opinions as objective facts.
- Add a small versioned mother-article lineage that platform drafts bind to explicitly; Markdown remains the canonical editable body and derived artifacts become stale when their input changes.
- Allow media to be assembled and frozen while a draft is under review so approval covers the final title, body, image order, citations, declarations, and checks as one content hash.
- Separate content approval from target authorization, and introduce independent manual delivery targets for WeChat and X Thread.
- Export complete public handoff packages, record manual delivery receipts and minimal feedback, and keep each target independent when another target waits or fails.
- Mark legacy evidence as untyped and keep it readable, but do not grant new approval or delivery eligibility through migration alone.
- Guard existing external-delivery entry points so missing or stale approval/authorization cannot be bypassed.
- Exclude WeChat automatic draft creation, X API publishing, scheduling, automatic external retries, other channels, video/digital-human workflows, SaaS tenancy, and billing from this change.

## Capabilities

### New Capabilities

- `typed-evidence-freeze`: Classify and freeze the exact evidence values, excerpts, attribution, source position, version, and rights needed by an article revision.
- `versioned-article-candidate`: Maintain an immutable mother-revision lineage and a complete review candidate whose text, media, citations, declarations, and checks share one content hash.
- `manual-article-handoff`: Authorize independent WeChat and X Thread manual delivery targets, export public handoff packages, and capture receipts and feedback without claiming automatic publication.

### Modified Capabilities

None. This project has no existing OpenSpec capability specifications; the change introduces the first formal capability set while retaining existing APIs unless the design explicitly adds fields or endpoints.

## Impact

- Database models and migrations for FactPackItem snapshots, MotherRevision, draft-stage media linkage, approval metadata, and DeliveryTarget.
- Existing fact-pack freeze/clone/read paths, generation and draft revision flows, fact checking, review approval, asset/media protection, exports, workflow delivery guards, and audit events.
- API and React surfaces needed to import/confirm an existing article, preview a complete candidate, authorize a target, download a package, and record receipt/feedback.
- Existing three-channel records remain readable. No remote platform operation is enabled by this proposal.
