## Context

FE-F4 provides project-first review and delivery, and FE-P1 establishes route-loading boundaries. `/home` and `/opportunities` are still placeholder routes. Existing `SourceDocument`, `DataSnapshot`, `ContentProject`, `CreativeBriefRevision`, `ProjectEvent`, project Overview, Review projection, and Delivery facts are usable, but there is no owner-scoped object representing a reason to create content before a project exists.

F5A must add that decision layer without turning `ContentOpportunity` into a second Topic, duplicating project/review state, inventing a news crawler, or mutating evidence and identity automatically. The first implementation is local and backend-backed; external connectors remain inputs only when they already produce a persisted source/snapshot.

## Goals / Non-Goals

**Goals:**

- Persist owner-scoped opportunities, source signals, and append-only assessment revisions.
- Make the opportunity lifecycle and triage state explicit and auditable.
- Let a user explicitly convert an opportunity into a ContentProject with suggested values as draft input.
- Make `/opportunities` a real workspace and `/home` a deterministic projection over existing business facts.
- Preserve ownership, identity readiness, evidence-boundary, review, delivery, unknown, blocked, and stale semantics.

**Non-Goals:**

- No automatic news/search ingestion, new external connector, or scraping system.
- No automatic ContentProject creation, Fact Boundary mutation, unselected Source binding, Candidate approval, Delivery authorization, or Identity update. Explicitly selected SourceDocument signals may become ordinary ProjectSourceBinding rows during conversion.
- No Topic replacement or deletion of the existing Topic/Brief flow.
- No `HomeTask`, dashboard status, schedule, performance-learning, asset-library, or settings domain in F5A.
- No production migration, external publishing, or production database write.

## Decisions

1. **Use four persisted opportunity records.** `ContentOpportunity` owns lifecycle and triage identity; `ContentOpportunitySignal` records immutable source observations; `ContentOpportunityAssessmentRevision` is append-only and versioned; `OpportunityProjectConversion` is the idempotent origin relation. A JSON payload is appropriate for evolving signal/assessment detail, but stable ownership, lifecycle, revision, source reference, checksum, and timestamps remain columns. Source categories are derived from signal types rather than a second single source field.

2. **Keep opportunity separate from TopicBrief.** An opportunity explains why-now and fit. Conversion may later create a project brief, while TopicBrief remains a compatible production input for legacy flows. No opportunity endpoint creates or mutates Topic rows.

3. **Make conversion one explicit transaction.** `POST /content-opportunities/{id}/convert-to-project` requires an editor owner, the current assessment revision, and an idempotency key. It creates one ContentProject, a durable origin relation, a normal CreativeBriefRevision v1, and optionally attaches explicitly selected SourceDocument signals through the existing ProjectSourceBinding. It never creates, freezes, or binds a FactPack or Project Fact Boundary. Repeated conversion returns the existing project and does not duplicate events.

4. **Reuse project and identity validation.** Suggested identity scope is checked against the requesting user's visible hierarchy before it is placed in the draft Brief. Suggestions remain editable and are not treated as a frozen identity snapshot. Existing project brief/evidence endpoints remain the only approval paths. Selected signal IDs are revalidated at commit time.

5. **Build Home from read models.** The Home endpoint composes current opportunities, owned ContentProjects and their existing Overview, project events, Review projection, Delivery reconciliation, and identity-readiness risks. It returns typed cards and links, not a second state machine. “近期计划” is not fabricated because no schedule entity exists; F5A exposes recent project activity/updated projects instead.

6. **Use route-level modules.** `/home` and `/opportunities` are separate lazy page roots so F5A does not regress FE-P1's initial `/projects` budget. Shared presentation types are type-only or placed in a focused product module; no heavy editor dependency is imported.

7. **Fail closed on authorization and unknowns.** Opportunity and signal/assessment reads are owner-scoped. Home only aggregates owned projects. Unknown delivery remains a reconciliation card and never becomes delivered or ready; blocked/stale and `identity_unready` remain distinct typed actions.

8. **Keep automated analysis optional.** A replaceable `opportunity_analysis` capability may produce a validated assessment, but an unavailable capability returns an explicit unavailable result and never creates fake analysis. Manual assessment is the primary path.

9. **Use existing audit boundaries.** Opportunity lifecycle mutations are written to `AuditLog`; assessment rows are their own immutable history; only post-conversion project activity is written to `ProjectEvent`. F5A does not add `ContentOpportunityEvent`.

10. **Make Home failure semantics explicit.** Core projection failures are request/section errors with `incomplete` metadata; only optional capability failures may be partial. Missing core data is never rendered as an empty successful section.

## Risks / Trade-offs

- **[Assessment JSON evolves quickly]** → Keep lifecycle, revision, checksum, ownership, and source lineage normalized; version the assessment schema and preserve old JSON.
- **[Conversion could silently create project facts]** → Require an explicit command, return the created project, record provenance, bind only explicitly selected SourceDocument references, and never create or freeze a Fact Boundary during conversion.
- **[Home projection becomes a duplicate workflow engine]** → Reuse project Overview and Review/Delivery projections; Home only groups cards and links to authoritative actions.
- **[Large opportunity list slows Home]** → Bound each projection query, paginate opportunities, and avoid loading full project histories; measure before introducing caching.
- **[Existing route initial graph regresses]** → Keep Home/Opportunity in their own lazy chunks and rerun FE-P1 budget after implementation.

## Migration Plan

Additive migration creates the four opportunity tables and indexes; existing rows are not backfilled or reclassified. Lifecycle constraints and conversion uniqueness are enforced at both service and database boundaries. Rollback is a code/schema rollback in an isolated development database before any production migration is considered. Apply must first verify the workspace can read FE-P1 commit `85b8c08` and the canonical FE-P1 spec.

## Open Questions

- Whether future connectors should write signals directly or first create SourceDocument/DataSnapshot remains deferred to the connector-specific change.
- A real “近期计划” card needs a scheduling contract; F5A will not infer a plan from timestamps.
