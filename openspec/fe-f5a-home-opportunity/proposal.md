## Why

AIContentStudio already has a durable production core: ContentProject, CreativeBrief, Evidence/Fact Boundary, Content Identity, Workflow production, project-first Review/Distribution and frontend performance controls. The remaining gap at the beginning of the lifecycle is deciding **what is worth doing now**.

Legacy `TopicBrief` assumes the decision to create content has already been made. V2 places `Content Opportunity` before `ContentProject`, and Home must answer only three questions:

1. 今天有什么值得做？
2. 哪些项目正在推进？
3. 现在有什么需要我决定？

FE-F5A therefore adds a durable Opportunity domain plus a Home projection. It does not rebuild upstream research/news systems, does not rename Topic into Opportunity, does not create a second task system, and does not silently promote suggestions into Evidence or production.

## What Changes

- Add `ContentOpportunity` as a stable business object before ContentProject.
- Add immutable `ContentOpportunityAssessmentRevision` to version why-now, relevance, audience/identity fit, modality/channel recommendations, evidence summary, risk, time sensitivity and similarity state.
- Add `ContentOpportunitySignal` as a bounded reference/annotation layer over existing SourceDocument, project DataSnapshot, DeliveryFeedback, manual observations and future external references. Raw source bodies/bytes stay in their original truth stores.
- Add `OpportunityProjectConversion` as the durable origin relation between one Opportunity and its primary ContentProject. Conversion is explicit, transactional and idempotent.
- Conversion may create CreativeBrief v1 and attach selected SourceDocument signals, but MUST NOT create/freeze/bind FactPack or Fact Boundary automatically.
- Add optional model-assisted Opportunity Analysis as a replaceable capability. Persisted Assessment revisions remain the business truth; manual assessment remains fully usable when the model capability is unavailable.
- Replace `/opportunities` placeholder with a persistent Opportunity workspace and `/opportunities/:id` detail.
- Replace `/home` placeholder with a deterministic projection of current Opportunities, active Project Overview state, FE-F4 pending decisions and identity-readiness alerts.
- Home SHALL NOT persist `HomeTask`, `DashboardState` or a second review/project state system.
- Future 7-day rhythm stays truthful: if no real scheduling business object exists, Home shows an explicit empty/not-enabled state rather than inventing dates.
- Preserve FE-P1 route-level lazy-loading and bundle-budget rules after the actual FE-P1 canonical spec is reconciled.

## Capabilities

### New Capabilities

- `fe-f5a-home-opportunity`: Opportunity lifecycle, signal references, versioned assessment, explicit Opportunity→ContentProject conversion and Home/Today projection.

### Modified Capabilities

- `fe-f0-f1-project-experience`: `/home` and `/opportunities` become real primary workspaces.
- `fe-f3a-content-project-core`: ContentProject can retain origin Opportunity provenance; conversion may create initial Brief/source bindings and project activity while keeping Fact Boundary explicit.
- `fe-f3b-content-identity`: Opportunity may recommend stable identity hierarchy refs but cannot mutate Identity or create production IdentitySnapshot.
- `fe-f4-project-review-distribution`: Home may surface FE-F4 pending approval/authorization/reconciliation decisions without copying review state.

## Impact

Backend: additive Opportunity tables, Opportunity/Home services and routers, project-conversion transaction, ProjectEvent extension, identity/source authorization reuse and optional analysis adapter.

Frontend: lazy-loaded real `/home`, `/opportunities`, `/opportunities/:id`.

Data: no Topic/Project/Source/Evidence rows are rewritten. Existing Projects without Opportunity origin remain valid. No production deploy/migration, new external connector, LearningCandidate, performance ingestion or automatic identity strategy mutation is included.
