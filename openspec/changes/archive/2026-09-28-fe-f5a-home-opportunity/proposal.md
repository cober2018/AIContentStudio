## Why

The system can now carry content from evidence through project, identity, production, review, and delivery, but it still lacks a durable answer to “why should we make this content now?”. The current `/home` and `/opportunities` pages are placeholders, while the existing `TopicBrief` is a production input rather than an opportunity judgment; F5A adds that missing decision layer without creating a second source, project, or review state machine.

## What Changes

- Add an owner-scoped `ContentOpportunity` lifecycle with `new`, `watching`, `qualified`, `dismissed`, `converted`, and `archived` states.
- Add immutable opportunity signal references and append-only assessment revisions, preserving source/version/checksum lineage and distinguishing suggestions from approved project facts.
- Provide a projectable opportunity read model containing why-now, audience/identity fit, modality/channel suggestions, similar-history references, risks, and confidence.
- Require an explicit user action to convert a qualified opportunity into one `ContentProject`; create a normal Brief v1 and optionally attach explicitly selected SourceDocument signals through the existing project-source binding, without auto-freezing evidence or creating a Topic.
- Replace `/opportunities` with a real workspace for triage, assessment, filtering, and explicit project conversion.
- Replace `/home` with a projection over opportunities, project overview/read models, project events, review decisions, delivery reconciliation, identity readiness, and blocked/stale states; do not add `HomeTask`, `DashboardState`, or another duplicate status table.
- Preserve existing `SourceDocument`, `DataSnapshot`, `DeliveryFeedback`, `ContentProject`, `CreativeBriefRevision`, `ProjectEvent`, Review, and Delivery facts as the underlying sources of truth.

## Capabilities

### New Capabilities

- `content-opportunities`: Owner-scoped opportunity, signal, assessment revision, lifecycle, triage, and explicit conversion contracts.
- `content-home-workspace`: Home projection and actionable work queues derived from existing opportunity, project, review, delivery, and identity state.

### Modified Capabilities

- `fe-f0-f1-project-experience`: make Home and Opportunity real persistent workspaces.
- `fe-f3a-content-project-core`: Define opportunity conversion as an explicit project-creation entry point with suggested values that remain drafts until the existing project brief/evidence flows approve them.
- `fe-f3b-content-identity`: allow validated identity recommendations without mutating identity or creating snapshots.
- `fe-f4-project-review-distribution`: allow Home to consume review/delivery pending-decision projections without creating a parallel state machine.

## Impact

- Backend: new opportunity persistence, API/read-model services, an additive migration, and conversion orchestration that reuses existing project/brief/evidence boundaries.
- Frontend: real `/home` and `/opportunities` route modules, opportunity list/detail/assessment UI, conversion flow, and projection cards linking to existing project/review/delivery routes.
- Existing source, data snapshot, project, review, delivery, and identity APIs remain authoritative and compatible; no external news-fetching system, real connector, automatic project creation, automatic fact-boundary mutation, or automatic identity update is included.
- No production migration, external publishing, or third-party connector activation is part of F5A. Optional automated analysis must fail closed when no verified capability exists; manual assessment remains complete.
