## 0. Prerequisite reconciliation and baseline

- [ ] 0.1 Verify apply workspace contains canonical/implemented FE-F3B, FE-F4 and FE-P1. If connector points to an older branch/commit, stop apply and reconcile first.
- [ ] 0.2 Identify actual post-FE-P1 commit and Alembic head; create `codex/fe-f5a-home-opportunity` from that real baseline.
- [ ] 0.3 Preserve user-provided untracked source artifacts; do not silently add/delete/move them.
- [ ] 0.4 Record baseline backend tests, frontend build, all canonical OpenSpec strict results, diff-check and FE-P1 bundle budgets.
- [ ] 0.5 If canonical FE-P1 requires route-registration delta, add it using its actual capability name after reconciliation; do not invent the name.

## 1. Opportunity persistence

- [ ] 1.1 Add ContentOpportunity with owner/status/priority/relevant_until/lifecycle fields and indexes.
- [ ] 1.2 Add ContentOpportunitySignal with bounded resource-reference metadata and active/detached lifecycle.
- [ ] 1.3 Add ContentOpportunityAssessmentRevision with append-only revision/checksum/provenance.
- [ ] 1.4 Add OpportunityProjectConversion with unique Opportunity, Project and idempotency constraints.
- [ ] 1.5 Add reversible migration after actual FE-P1 head; do not synthesize Opportunities for old Projects.
- [ ] 1.6 Validate isolated SQLite up/down/up and PostgreSQL-compatible constraints.

## 2. Opportunity lifecycle and authorization

- [ ] 2.1 Add owner-scoped opportunity authorization service.
- [ ] 2.2 Enforce lifecycle transitions and archive read-only behavior.
- [ ] 2.3 Add bounded list/detail/create/patch/archive APIs.
- [ ] 2.4 Use AuditLog where operationally appropriate; do not create a generic duplicate event system.

## 3. Signal references

- [ ] 3.1 SourceDocument attach/reattach/detach with no raw_text/parsed-body copy.
- [ ] 3.2 DataSnapshot signal with owning project/unit authorization and checksum-only reference.
- [ ] 3.3 DeliveryFeedback signal through authorized DeliveryTarget/project lineage.
- [ ] 3.4 Bounded manual/external_ref signals with no network fetch.
- [ ] 3.5 Idempotent duplicate resource attach/reactivation.
- [ ] 3.6 Historical Assessments remain readable after Signal detach.

## 4. Assessment revisions

- [ ] 4.1 Add typed assessment schema and enum validation.
- [ ] 4.2 Validate FE-F3B identity recommendations.
- [ ] 4.3 Validate current modality and Channel Registry recommendations.
- [ ] 4.4 Add current/history/detail/save APIs with expected_revision and race→409 behavior.
- [ ] 4.5 Preserve similarity `unknown` when comparison has not run.
- [ ] 4.6 Store analyzer provider/version provenance when applicable.

## 5. Optional Opportunity Analysis

- [ ] 5.1 Define replaceable `opportunity_analysis` capability contract using bounded authorized signal context.
- [ ] 5.2 Reuse existing model/runtime cleanly; do not bind Opportunity core to one provider.
- [ ] 5.3 Validate model output using the same Assessment schema.
- [ ] 5.4 Unavailable capability returns truthful unavailable state and no fake Assessment.
- [ ] 5.5 Treat all Source/Signal text as data, never executable instructions.

## 6. Opportunity → Project conversion

- [ ] 6.1 Add conversion read endpoint.
- [ ] 6.2 Add explicit convert endpoint requiring current assessment revision and idempotency key.
- [ ] 6.3 Commit Project + Conversion + Brief v1 + selected Source bindings + ProjectEvent + Opportunity status atomically.
- [ ] 6.4 Support bounded explicit Project/Brief overrides.
- [ ] 6.5 Never create/freeze/bind FactPack/Fact Boundary during conversion.
- [ ] 6.6 Repeated conversion returns existing primary Project.
- [ ] 6.7 Injected failure rolls back all conversion mutations.
- [ ] 6.8 Add bounded Project origin Opportunity read model.

## 7. Project-core integration

- [ ] 7.1 Register `project.created_from_opportunity`.
- [ ] 7.2 Keep converted Project `evidence_needed` until explicit frozen Fact Boundary.
- [ ] 7.3 Show origin Opportunity link in Project Overview/detail.
- [ ] 7.4 Existing Projects without origin remain valid.

## 8. Home projection backend

- [ ] 8.1 Add bounded `home_projection` service; no HomeTask/DashboardState tables.
- [ ] 8.2 Implement deterministic Today Opportunity selection/order.
- [ ] 8.3 Aggregate active Project Overview summaries with bounded/bulk queries.
- [ ] 8.4 Reuse FE-F4 pending approval/authorization/reconciliation facts.
- [ ] 8.5 Reuse identity readiness and deduplicate by stable code/entity refs.
- [ ] 8.6 Return truthful schedule capability/empty state when no scheduling contract exists.
- [ ] 8.7 Add `/api/v1/home`.
- [ ] 8.8 Add query-count/performance regression to avoid obvious N+1 growth.

## 9. Opportunity frontend

- [ ] 9.1 Replace `/opportunities` placeholder with lazy persistent list.
- [ ] 9.2 Add lazy `/opportunities/:id` detail.
- [ ] 9.3 Add status/priority/signal/time-sensitivity/search filters.
- [ ] 9.4 Add Signals panel with provenance.
- [ ] 9.5 Add Assessment revision editor/history with conflict handling.
- [ ] 9.6 Show why-now, identity/audience fit, modalities/channels, evidence, risks and similarity truth.
- [ ] 9.7 Add explicit Convert to Project preview/confirm flow.
- [ ] 9.8 Converted Opportunity links to Project.

## 10. Home frontend

- [ ] 10.1 Replace `/home` placeholder with lazy HomePage.
- [ ] 10.2 Add Today's Opportunities.
- [ ] 10.3 Add Pending Decisions with deep links to responsible workspaces.
- [ ] 10.4 Add Active Projects from Overview summaries.
- [ ] 10.5 Add truthful Upcoming 7 Days empty/capability state.
- [ ] 10.6 Add Identity Alerts.
- [ ] 10.7 Keep Home lightweight: no workflow canvas, full editors, provider dashboard or full Candidate payload.

## 11. FE-P1 performance preservation

- [ ] 11.1 Keep Home and Opportunity routes lazy under canonical FE-P1.
- [ ] 11.2 Verify TipTap/XYFlow/legacy editor do not enter Home/Opportunity initial chunks.
- [ ] 11.3 Keep `/projects` initial-JS budget green.
- [ ] 11.4 Add/extend bundle checks for Home/Opportunity according to canonical FE-P1.
- [ ] 11.5 Avoid importing full Project/Review route modules only for shared card/types.

## 12. Targeted tests

- [ ] 12.1 cross-owner Opportunity denial
- [ ] 12.2 lifecycle transition + archive read-only
- [ ] 12.3 Source signal no raw-body duplication
- [ ] 12.4 DataSnapshot/Feedback authorization
- [ ] 12.5 idempotent signal attach/reactivation
- [ ] 12.6 Assessment append-only + stale revision 409
- [ ] 12.7 concurrent Assessment conflict 409
- [ ] 12.8 identity recommendation validation
- [ ] 12.9 modality/channel validation
- [ ] 12.10 similarity unknown truthfulness
- [ ] 12.11 analyzer unavailable no fake assessment
- [ ] 12.12 conversion current-assessment precondition
- [ ] 12.13 conversion idempotency
- [ ] 12.14 atomic Project/Brief/Source/Event/status conversion
- [ ] 12.15 no FactPack/Fact Boundary auto-creation
- [ ] 12.16 rollback on injected conversion failure
- [ ] 12.17 Project origin after Opportunity archive
- [ ] 12.18 Home deterministic ordering
- [ ] 12.19 Home decision precedence/dedupe
- [ ] 12.20 Home schedule capability false without dates
- [ ] 12.21 bounded Home query behavior
- [ ] 12.22 FE-F3A/F3B/F4 regressions green

## 13. Local acceptance and handoff

- [ ] 13.1 Run full backend suite and targeted regressions.
- [ ] 13.2 Run frontend TypeScript/Vite build.
- [ ] 13.3 Run all canonical OpenSpec strict validation and git diff --check.
- [ ] 13.4 Run FE-P1 bundle budgets and record Home/Opportunity initial chunks.
- [ ] 13.5 Isolated browser: Opportunity → Source → Assessment → Convert → Project.
- [ ] 13.6 Verify Brief/source prefill and missing Fact Boundary.
- [ ] 13.7 Verify Home reflects Opportunity/Project/F4 decisions after reload.
- [ ] 13.8 Verify truthful schedule empty state.
- [ ] 13.9 Independent review before archive/commit; no push/merge/deploy/production migration.
