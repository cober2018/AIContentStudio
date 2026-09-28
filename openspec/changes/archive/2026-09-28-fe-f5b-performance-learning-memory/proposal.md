## Why

AIContentStudio now supports Opportunity → ContentProject → Identity-aware Production → Candidate Review → controlled Delivery. The remaining lifecycle gap is learning from what was actually published and what happened afterward.

Existing `DeliveryFeedback` is intentionally small and delivery-scoped. It is not sufficient for multi-year published-content recovery, structured platform metrics, coverage/quality visibility, long-term analysis, validated Learning Candidates, or Content Memory. At the same time, performance observations must never silently rewrite Content Identity, Workflow defaults, or channel strategy.

FE-F5B adds the durable post-delivery learning layer:

Published / Historical Content
→ Performance & Feedback Observations
→ Insight
→ Learning Candidate
→ Evidence Accumulation
→ Human Validation
→ Content Memory

## What Changes

- Add `PublishedContentRecord` as the durable analysis root for both Studio-produced publications and historical external imports.
- Add immutable `PerformanceObservation` rows for structured metrics and qualitative observations while preserving platform-specific metric meaning; incompatible platform metrics are not silently summed.
- Add immutable `ContentInsight` rows for bounded, evidence-backed analysis with explicit coverage, limitations and confidence.
- Add `LearningCandidate` plus evidence bindings for identity/audience/channel/format/topic/workflow learning categories.
- Require explicit validation before a Learning Candidate may be promoted. Performance alone never mutates Identity, Workflow, Account preference, or strategy.
- Add append-only `ContentMemoryEntry` / `ContentMemoryRevision` for validated dynamic memory scoped to owner/Brand/Persona/Account/Series.
- Promotion from an accepted Learning Candidate to Content Memory is a separate explicit action; it does not automatically edit Content Identity.
- Replace `/learning` placeholder with four real views: Historical Recovery, Long-term Analysis, Learning Candidates, Content Memory.
- Upgrade the Identity Workspace Content Memory tab from placeholder text to a view over validated memory for that identity scope.
- Allow Home to surface Learning Candidate validation as a pending human decision without introducing duplicate task state.
- Preserve FE-P1 route-level lazy loading and bundle budgets.

## Capabilities

### New Capabilities

- `content-performance-history`: Published-content recovery, historical import, structured observations, data coverage and long-term performance read models.
- `content-learning-memory`: Evidence-backed Insights, Learning Candidates, human validation and versioned Content Memory.

### Modified Capabilities

- `fe-f0-f1-project-experience`: `/learning` becomes a persistent primary workspace.
- `fe-f3b-content-identity`: Content Memory becomes a real dynamic layer linked to identity scope while remaining separate from stable Identity revisions.
- `fe-f4-project-review-distribution`: confirmed delivery/receipts and feedback become provenance sources for published-history/performance, without changing delivery state semantics.
- `content-home-workspace`: Home may surface Learning Candidate validation as an additional pending decision while Learning remains the authoritative source.

## Impact

Backend: additive models/migration, learning/performance services and APIs, delivery-to-history synchronization, identity-memory read integration, Home projection integration.

Frontend: real lazy `/learning` workspace with four subviews and Identity Memory integration.

No production deployment/migration, no new external platform connector, no automatic crawling, no automatic identity/workflow/channel mutation, and no hidden cross-platform KPI normalization is included.

## SPEC review calibration

The reviewed package distinguishes actual publication time from legacy receipt-confirmation time, freezes validated evidence, declares metric measurement grain, closes direct Memory write bypasses, and adds concurrency/idempotency gates. Four modified requirements preserve the canonical contracts. Business-code apply awaits confirmation of this calibrated proposal under the project process.
