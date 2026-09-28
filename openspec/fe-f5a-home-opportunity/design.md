## Context

The current product already has:
- SourceDocument / FactPack / Project Fact Boundary;
- ContentProject / CreativeBrief / Content Matrix;
- Brand / Persona / Account / Series + IdentitySnapshot;
- Workflow production and project DataSnapshot;
- project-first Review/Candidate/Delivery contract;
- project Overview / Versions / Activity;
- FE-P1 route-level performance requirements.

Legacy `TopicBrief` represents an already-decided production topic. It is not Opportunity.

Current `DataSnapshot` belongs to a ContentUnit/WorkflowRun. FE-F5A MUST NOT generalize it into an upstream signal database.

Current Home and Opportunity routes are placeholders.

## Hard prerequisite before apply

Business-code apply MUST first verify the actual workspace contains:
1. canonical/implemented FE-F3B;
2. canonical/implemented FE-F4;
3. canonical FE-P1 performance spec and optimized route baseline;
4. the actual migration head after those changes.

If the connector/workspace still exposes an older baseline, STOP apply and reconcile first.

## Goals / Non-Goals

**Goals**
- durable ContentOpportunity before ContentProject;
- source-referenced Opportunity signals without raw-store duplication;
- append-only Opportunity assessments;
- truthful identity/channel/modality/evidence/similarity recommendations;
- explicit idempotent Opportunity→Project conversion;
- Home as a bounded deterministic projection;
- optional AI-assisted analysis independent of core persistence;
- persistent Home/Opportunity frontend;
- full traceability from converted Project back to Opportunity.

**Non-Goals**
- crawler/search engine/social listener;
- upstream quant/media platform;
- Topic replacement;
- full planning calendar;
- Perspective domain;
- Performance ingestion / LearningCandidate;
- automatic strategy or identity mutation;
- new Data Source connectors or publishers;
- full BI dashboard.

## 1. ContentOpportunity stable object

Add `ContentOpportunity`:

- `id`
- `owner_user_id`
- `title`
- `summary`
- `status`
- `priority`
- `relevant_until nullable`
- `created_by`
- `created_at`
- `updated_at`
- `archived_at nullable`

Status:
- `new`
- `watching`
- `qualified`
- `dismissed`
- `converted`
- `archived`

Priority:
- `low`
- `normal`
- `high`

Server validates lifecycle transitions. `converted` is set only by a committed OpportunityProjectConversion. `archived` is read-only.

Do not add Topic/Workflow/Facts directly to Opportunity.

## 2. Opportunity signals reference existing truth

Add `ContentOpportunitySignal`:

- `id`
- `opportunity_id`
- `signal_type`
- `source_entity_type nullable`
- `source_entity_id nullable`
- `external_ref nullable`
- `label`
- `annotation_json`
- `source_checksum nullable`
- `source_version nullable`
- `observed_at nullable`
- `status` (`active|detached`)
- `attached_by`
- `created_at`
- `detached_at nullable`

Initial signal types:
- `source_document`
- `data_snapshot`
- `delivery_feedback`
- `manual`
- `external_ref`

Rules:
- SourceDocument signal stores ID/checksum/annotation, never copies raw_text/parsed body.
- DataSnapshot signal validates access through owning project/unit and stores ID/checksum, never copies normalized_output.
- DeliveryFeedback signal validates its authorized delivery/project path and stores row reference.
- Manual signal may store bounded human observation in annotation_json because no external source exists.
- external_ref stores bounded identifier/URL/label only; F5A does not fetch it.

Signal payload is immutable; detach/reattach changes only membership lifecycle. Historical assessments may still refer to detached signals.

Repeated attach of the same resource to the same Opportunity is idempotent/reactivates the existing row where applicable.

## 3. Append-only Opportunity Assessment

Add `ContentOpportunityAssessmentRevision`:

- `id`
- `opportunity_id`
- `revision_no`
- `parent_revision_id nullable`
- `what_happened`
- `why_now`
- `brand_relevance`
- `audience_fit`
- `suggested_angle nullable`
- `time_sensitivity`
- `recommended_identity_refs_json`
- `recommended_modalities_json`
- `recommended_channels_json`
- `evidence_signal_ids_json`
- `evidence_summary_json`
- `risk_flags_json`
- `similarity_state`
- `similar_content_refs_json`
- `confidence nullable`
- `analysis_source`
- `analysis_provider_key nullable`
- `analysis_provider_version nullable`
- `checksum`
- `created_by`
- `created_at`

Unique `(opportunity_id, revision_no)`.

Save requires `expected_revision`; stale or DB race returns 409. Old revisions never mutate.

`time_sensitivity`:
- timeless
- low
- medium
- high

`similarity_state`:
- unknown
- none
- possible

Never translate `unknown` into `none`.

`confidence` is optional 0..1 metadata and MUST NOT become a hidden ranking score.

Modalities are limited to `text|graphic|video`.
Channels are validated using current Channel Registry when possible.

## 4. Identity recommendation semantics

`recommended_identity_refs_json` uses typed Brand/Persona/Account/Series refs and validates FE-F3B hierarchy ownership.

Recommendations:
- do not mutate identity;
- do not create IdentitySnapshot;
- do not change workflow defaults;
- do not bind a ContentUnit.

An append-only assessment may store bounded name/revision/checksum metadata so the historical recommendation remains understandable if identity labels later change.

If a recommended identity is archived later, the old assessment remains readable and UI marks it unavailable.

## 5. Optional AI Opportunity Analysis

Stable core is the Assessment revision.

Optional endpoint:
`POST /content-opportunities/{id}/analyze`

Behavior:
- gather only bounded authorized Signal summaries/references;
- invoke a registered replaceable task capability `opportunity_analysis` if available;
- validate model output with the exact Assessment schema;
- never treat source text as executable instructions;
- record provider/version provenance;
- unavailable capability returns truthful `capability_unavailable`.

Manual Assessment MUST remain complete and first-class.

If current runtime cannot expose a clean opportunity-analysis capability without invasive changes, F5A may ship manual assessment plus unavailable capability state first. It MUST NOT fake automated analysis.

## 6. Historical similarity truthfulness

F5A does not implement F5B's historical performance/embedding system.

Assessment stores `similarity_state` and verified `similar_content_refs`.

If no reliable comparison exists:
`similarity_state = unknown`.

UI displays "未完成历史重复判断", not "无重复".

No synthetic duplicate score.

## 7. Explicit Opportunity → Project conversion

Add `OpportunityProjectConversion`:

- `id`
- `opportunity_id`
- `project_id`
- `assessment_revision_id`
- `idempotency_key`
- `conversion_snapshot_json`
- `created_by`
- `created_at`

Constraints:
- unique opportunity_id;
- unique project_id;
- unique idempotency_key.

F5A supports one primary Project per Opportunity. One ContentProject has at most one origin Opportunity.

### Endpoint

`POST /content-opportunities/{id}/convert-to-project`

Input:
- `expected_assessment_revision`
- `idempotency_key`
- optional project title/objective overrides
- selected signal IDs to attach as project sources
- optional Brief field overrides

Single DB transaction:
1. authorize mutable Opportunity;
2. verify no prior conversion;
3. verify current assessment revision;
4. verify selected Signals belong to the Opportunity;
5. create ContentProject;
6. create OpportunityProjectConversion;
7. create CreativeBriefRevision v1 from assessment + explicit overrides;
8. attach selected SourceDocument Signals using normal ProjectSourceBinding;
9. record `project.created_from_opportunity`;
10. set Opportunity status `converted`;
11. commit.

Repeated same conversion returns the existing Project. No duplicate Project.

On failure, no partial Project/Brief/Source/event/conversion/status mutation remains.

### Brief prefill

Assessment may prefill:
- objective
- primary_audience
- angle
- required_evidence references
- identity_scope
- modality_scope
- channel_scope
- references

Do not fabricate core_message/CTA if absent.

The new Brief is a normal immutable project Brief revision and is editable only via later revisions.

## 8. Opportunity evidence is not Fact Boundary

This is a hard boundary.

Conversion MUST NOT:
- create a FactPack;
- turn Signals into Fact rows automatically;
- freeze a FactPack;
- bind a Project Fact Boundary.

Selected SourceDocument signals may become ProjectSourceBinding only.

Opportunity evidence answers "why this looks worth doing"; Fact Boundary answers "what may be asserted as fact".

After conversion, Project Overview remains evidence-needed until an authorized user explicitly creates/freezes/binds FactPack.

## 9. Project origin relation

Do not copy Opportunity state into ContentProject.

Project origin is resolved through OpportunityProjectConversion.

Project/detail/Overview may expose:
- opportunity id/title/status
- assessment revision used at conversion

Historical `conversion_snapshot_json` remains available even if Opportunity is archived later.

Add stable ProjectEvent code:
`project.created_from_opportunity`.

Existing Projects with no conversion remain valid.

## 10. Home is a projection, not a task store

Do NOT create:
- HomeTask
- DashboardState
- TodayDecision
- duplicated project/review status rows

Add `services/home_projection.py`.

Home aggregates:
1. actionable Opportunities;
2. active ContentProjects via existing Overview rules;
3. FE-F4 pending approval/authorization/reconciliation decisions;
4. identity-readiness alerts from existing identity/project facts;
5. truthful upcoming dated items only if a real scheduling contract exists.

Recommended API:
`GET /api/v1/home`

Bounded response:
- `opportunities`
- `decisions`
- `projects`
- `upcoming`
- `identity_alerts`
- `capabilities`
- `generated_at`

## 11. Deterministic "today opportunities"

Actionable Opportunity statuses:
- new
- watching
- qualified

Excluded:
- dismissed
- converted
- archived

Order:
1. priority high > normal > low
2. currently relevant before expired
3. time_sensitivity high > medium > low > timeless
4. relevant_until ascending
5. updated_at descending

Do not hide an opaque model score behind Home ordering.

Expired opportunities remain visible in Opportunity workspace but are not promoted to Today's list unless later explicitly reopened/updated under valid lifecycle semantics.

## 12. Home pending decisions

Home reuses FE-F4 / project Overview business facts.

Examples:
- delivery unknown / reconciliation required
- deterministic blocker
- stale output/check
- waiting human workflow step
- Content Approval pending
- Delivery Authorization pending
- identity_unready

Each decision contains stable code + entity refs + destination href. Human-readable label is presentation, not the contract.

Suggested precedence:
1. unknown/reconciliation
2. blocker
3. stale
4. waiting human
5. approval pending
6. authorization pending
7. identity readiness

Deduplicate the same underlying issue exposed by multiple projections.

Do not reimplement FE-F4 review-state logic inside Home.

## 13. Active Projects on Home

Reuse persisted Project Overview.

Card fields:
- id/title
- stage
- active unit count
- modality counts
- risk count
- pending-decision count
- next action
- origin Opportunity when present
- updated_at

Exclude archived projects.

Use bounded/bulk DB queries. Do not recursively call HTTP endpoints or introduce obvious N+1 scaling.

## 14. Future 7-day cadence stays truthful

The product contract includes a 7-day rhythm section, but current stable core has no general planned-publication object.

F5A MUST NOT infer future schedule from created_at/updated_at/DeliveryTarget.requested_at.

Home returns:
- real dated items only if the reconciled system has a genuine planning contract;
- otherwise `upcoming=[]` and `capabilities.schedule=false`.

UI displays "尚未启用内容排期" or equivalent truthful empty state.

Do not create a half-defined schedule table merely to fill Home.

## 15. API

Recommended new router: `routers/opportunities.py`.

Opportunity:
- GET `/content-opportunities`
- POST `/content-opportunities`
- GET `/content-opportunities/{id}`
- PATCH `/content-opportunities/{id}`
- DELETE `/content-opportunities/{id}` → archive

Signals:
- GET `/content-opportunities/{id}/signals`
- POST `/content-opportunities/{id}/signals`
- DELETE `/content-opportunities/{id}/signals/{signal_id}` → detach

Assessment:
- GET `/content-opportunities/{id}/assessments`
- GET `/content-opportunities/{id}/assessments/{revision_id}`
- POST `/content-opportunities/{id}/assessments`
- POST `/content-opportunities/{id}/analyze` optional capability

Conversion:
- GET `/content-opportunities/{id}/conversion`
- POST `/content-opportunities/{id}/convert-to-project`

Home:
- GET `/home`

List APIs use bounded pagination/filtering.

## 16. Frontend Opportunity workspace

Replace `/opportunities` placeholder.

Recommended modules:
- `product/opportunity/OpportunityListPage.tsx`
- `OpportunityCard.tsx`
- `OpportunityDetailPage.tsx`
- `OpportunitySignalsPanel.tsx`
- `OpportunityAssessmentPanel.tsx`
- `OpportunityRecommendations.tsx`
- `OpportunityHistory.tsx`
- `OpportunityConvertProject.tsx`

List filters:
- status
- priority
- signal type
- identity recommendation
- time sensitivity
- search

Card shows:
- title
- why now
- priority/time sensitivity
- source types
- signal count
- recommended identity
- modality/channel
- similarity state
- status

Detail shows:
- summary / what happened
- why now
- signals
- current Assessment + revision history
- identity/audience fit
- modality/channel suggestions
- evidence summary
- risks
- historical similarity truth
- conversion/project link

## 17. Home frontend

Replace `/home` placeholder.

Recommended modules:
- `product/home/HomePage.tsx`
- `TodayOpportunities.tsx`
- `PendingDecisions.tsx`
- `ActiveProjects.tsx`
- `UpcomingRhythm.tsx`
- `IdentityAlerts.tsx`

Home MUST NOT embed:
- Workflow canvas
- full editor
- provider/model dashboard
- full Candidate review payload
- full Opportunity editor

Cards deep-link to the responsible workspace.

## 18. FE-P1 performance preservation

After actual FE-P1 canonical spec is visible:
- Home route remains lazy-loaded;
- Opportunity list/detail remain lazy-loaded;
- TipTap/XYFlow/legacy editor dependencies do not enter Home/Opportunity initial chunks;
- existing `/projects` budget remains green;
- new route budgets follow canonical FE-P1 rules;
- Home modules must not import whole Project/Review workspace implementations just for types/cards.

If FE-P1 requires a delta, add it using the actual canonical capability name during reconciliation. Do not invent the capability name now.

## 19. Authorization / provenance

All Opportunity resources are owner-scoped.

Signal refs revalidate underlying access:
- SourceDocument using existing source rules;
- DataSnapshot using owning Project/Unit authorization;
- DeliveryFeedback through authorized DeliveryTarget/project path.

A known Signal ID does not grant source visibility.

Identity refs are validated through FE-F3B hierarchy service.

Conversion revalidates selected signals and assessment at commit time.

## 20. Migration

Additive reversible migration after the actual post-FE-P1 head.

Create:
- `content_opportunity`
- `content_opportunity_signal`
- `content_opportunity_assessment_revision`
- `opportunity_project_conversion`

Indexes:
- opportunity owner/status/priority/updated_at
- signal opportunity/type/status
- resource-reference uniqueness where supported
- unique `(opportunity_id, revision_no)`
- unique conversion opportunity/project/idempotency

No synthetic Opportunity backfill for existing Projects.
No TopicBrief rewrite.

## 21. Required tests

Backend:
1. owner isolation
2. lifecycle transition validation
3. archived read-only
4. Source signal does not copy raw body
5. DataSnapshot/Feedback access denial
6. Signal idempotent attach/reactivation
7. Assessment append-only + stale revision 409
8. concurrent Assessment DB conflict 409
9. identity recommendation validation
10. modality/channel validation
11. similarity unknown truthfulness
12. analyzer unavailable does not fake assessment
13. conversion current-assessment precondition
14. conversion idempotency
15. conversion atomic Project/Brief/Source/Event/status
16. conversion never creates FactPack/Fact Boundary
17. rollback on injected conversion failure
18. Project origin survives Opportunity archive
19. Home actionable ordering
20. Home decision precedence/dedupe
21. Home has no persisted task rows
22. schedule unavailable returns capability false
23. bounded Home query behavior
24. FE-F3A/F3B/F4 regression suites remain green

Frontend/local:
- create Opportunity
- attach Source
- create/edit Assessment revisions
- inspect identity recommendations
- convert to Project
- verify Brief/source prefill
- verify no automatic Fact Boundary
- Home deep links
- FE-F4 pending/unknown decision projection
- truthful schedule empty state
- persistence on reload
- FE-P1 budgets remain green
