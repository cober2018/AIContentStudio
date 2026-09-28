## Context

The stable lifecycle now reaches delivery. Current reusable facts include immutable project Candidate (`ContentAsset`) with Project/Unit/IdentitySnapshot/Workflow provenance, `DeliveryTarget`, `DeliveryAttempt`, `DeliveryReceipt`, `DeliveryFeedback`, ContentAccount/Identity hierarchy, Opportunity/Home projections, and Project Activity/Versions/Overview.

There is no durable LearningCandidate, ContentMemory, historical published-content registry, structured performance observation model, or long-term analysis domain. `DeliveryFeedback(kind=performance|correction|note)` is useful provenance, but its free-text body cannot safely serve as the structured metric store.

## Goals / Non-Goals

**Goals**
- support Studio publications and historical external content in one analysis workspace;
- preserve exact publication/account/candidate provenance when known;
- store performance/feedback observations append-only;
- make missing historical data/coverage visible;
- create evidence-backed Insights and Learning Candidates;
- require explicit human/rule/experiment validation;
- promote accepted learnings into versioned Content Memory only by explicit action;
- expose memory by identity scope;
- keep metrics platform-specific unless an explicit later normalization rule exists.

**Non-Goals**
- no automatic social-platform ingestion connector;
- no universal KPI score or black-box cross-platform ranking;
- no automatic Identity/Workflow/Channel mutation;
- no full experimentation platform or BI warehouse replacement;
- no automatic scraping of historical content;
- no automatic memory injection into Workflow prompts without a future explicit memory-context contract.

## Hard prerequisite before apply

Apply only from the real post-F5A canonical baseline. Verify:
- `content-opportunities` and `content-home-workspace` are canonical;
- FE-F5A archive is visible;
- migration head is `f5a000000001` or the actual later reconciled head;
- FE-P1 bundle contract is canonical.

## 1. PublishedContentRecord is the analysis root

Add `PublishedContentRecord` with: id, owner_user_id, origin (`studio|external_import`), external_key nullable, content_asset_id nullable, delivery_target_id nullable, delivery_receipt_id nullable, content_account_id nullable, identity_snapshot_id nullable, channel, content_form nullable, account_ref_snapshot nullable, title nullable, canonical_url nullable, published_at nullable, content_hash nullable, content_snapshot_json nullable, coverage_json, confidence nullable, status (`active|archived`), created_by, created_at, updated_at.

Studio record rules:
- derive only from a confirmed publication receipt (`DeliveryReceipt.status=human_confirmed` with delivered_at), not merely authorization, package generation or Attempt success;
- link ContentAsset/Target/Receipt and preserve Candidate/Identity/Account provenance;
- internal content truth remains the immutable Candidate manifest; do not duplicate the full Candidate into content_snapshot_json.

External import rules:
- may persist normalized content snapshot because no internal Candidate exists;
- body/subtitles/metadata may be stored in a bounded snapshot;
- media are references/metadata, not duplicated binary blobs;
- owner + channel + external_key gives idempotent import identity.

Do not claim external imported content was produced by Studio.

## 2. Historical recovery and coverage

Historical import supports manual/API batch normalized records. Connector-specific ingestion remains future work.

Every PublishedContentRecord exposes coverage for: title, body, media, subtitles, identity, account, channel, published_at, metrics, comments/feedback, production provenance. `coverage_json` records known/missing/unknown, never invented values.

Coverage read models aggregate by time/year, channel, account, identity and content form. Old incomplete records remain useful but visibly incomplete. Cohorts with materially different coverage require warnings.

## 3. PerformanceObservation is append-only

Add `PerformanceObservation`: id, published_content_id, observation_kind (`metric|feedback|editorial|correction`), metric_namespace nullable, metric_key nullable, numeric_value nullable, text_value nullable, unit nullable, period_start/end nullable, observed_at, source_type (`manual|delivery_feedback|external_import|connector`), source_ref nullable, source_checksum nullable, confidence nullable, payload_json, supersedes_id nullable, created_by, created_at.

Rows are immutable. Corrections append a new row. Stable metric examples include `youtube.views`, `youtube.watch_time_seconds`, `xiaohongshu.saves`, `wechat.reads`. Different metric keys MUST NOT be summed or treated as equivalent without an explicit normalization rule.

DeliveryFeedback may be referenced as a qualitative source; free text is not parsed into fabricated numeric metrics.

## 4. Studio publication synchronization

Add `services/published_history.py`.

On confirmed receipt creation, or an idempotent backfill command for existing confirmed receipts, ensure one Studio PublishedContentRecord per Receipt. Repeated sync is idempotent.

Do not create PublishedContentRecord for authorized-only, package-only, unknown, failed, or draft-only delivery. Legacy records are linked only when provenance is provable; unknown links remain null/legacy.

## 5. ContentInsight is immutable evidence-backed analysis

Add `ContentInsight`: id, owner_user_id, insight_type (`identity|audience|channel|format|topic|workflow|general`), statement, scope_json, cohort_json, coverage_json, supporting_refs_json, contradicting_refs_json, limitations_json, confidence nullable, analysis_source (`manual|rule|model`), provider_key/version nullable, checksum, supersedes_id nullable, created_by, created_at.

Insights are immutable. Corrections create new Insights, optionally superseding older rows.

Every Insight must preserve cohort definition, evidence refs, coverage, limitations and contradiction/negative evidence when known. No unsupported “best practice” claim may be persisted without provenance.

## 6. Long-term analysis read models

`/learning/analysis` provides bounded cohort summaries using date range, channel/account, identity scope, modality/content form and metric namespace/key.

Only same metric namespace/key is aggregated unless a future explicit normalization rule exists. Responses include sample count, min/max, average/median when meaningful, trend, coverage and limitations. FE-F5B does not create a universal engagement score.

Optional model analysis may propose an Insight, but model unavailable returns capability-unavailable and creates no fake Insight.

## 7. LearningCandidate

Add `LearningCandidate`: id, owner_user_id, category (`identity|audience|channel|format|topic|workflow`), title, proposition, rationale, scope_json, status (`collecting|ready_for_review|accepted|rejected|archived`), confidence nullable, validation_method nullable (`human|rule|experiment|multi_sample`), validation_summary_json, created_from_insight_id nullable, created_by, created_at, decided_by/decided_at nullable.

Transitions:
- collecting → ready_for_review
- ready_for_review → accepted|rejected|collecting
- accepted/rejected → archived

Accepted/rejected propositions are immutable historical decisions.

## 8. LearningCandidateEvidence

Add `LearningCandidateEvidence`: id, learning_candidate_id, evidence_type (`published_content|performance_observation|insight|delivery_feedback`), entity_id, role (`support|contradict|context`), snapshot_checksum nullable, note nullable, created_by, created_at.

Historical accepted evidence remains readable. Acceptance requires at least one valid evidence ref plus explicit validation method and summary. UI distinguishes single-sample from multi-sample validation.

## 9. Content Memory is separate from stable Identity

Add `ContentMemoryEntry`: id, owner_user_id, scope_type (`owner|brand|persona|account|series`), brand_id/persona_id/account_id/series_id nullable, memory_type (`historical_viewpoint|audience_learning|channel_experience|editorial_preference|validated_strategy|workflow_learning|topic_learning`), status (`active|archived`), created_at.

Add append-only `ContentMemoryRevision`: id, memory_entry_id, revision_no, parent_revision_id nullable, statement, applicability_json, limitations_json, source_learning_candidate_id nullable, evidence_snapshot_json, checksum, created_by, created_at. Unique `(memory_entry_id, revision_no)`.

Scope validation reuses FE-F3B hierarchy. Memory is additive context, not Identity inheritance. Parent/child scope entries do not overwrite each other; read APIs return explicit origin labels.

## 10. Explicit promotion only

Flow:
Observation(s) → Insight → LearningCandidate → accepted validation → explicit Promote to Content Memory → Memory revision.

`POST /learning-candidates/{id}/promote-to-memory` requires accepted status, validated destination scope, idempotency key and explicit memory type/statement mapping. It freezes source candidate/evidence provenance.

Promotion does NOT update ContentBrand/Persona/Account/Series revisions, Workflow defaults, Channel configuration, Opportunity or production runs. Stable-domain changes require their own explicit save/version action.

## 11. Identity Memory integration

Replace the FE-F3B placeholder with real memory projection for the selected identity scope. Show active entries, scope origin, revision, source LearningCandidate, evidence count, applicability/limitations and archived history when requested.

No memory entry may masquerade as a stable Identity field.

## 12. `/learning` workspace

Replace placeholder with four tabs:
1. 历史回收
2. 长期分析
3. 学习候选
4. 内容记忆

Historical Recovery: Studio confirmed publications, external import, coverage matrix, missing-data warnings, observations.
Long-term Analysis: cohort filters, metric-key-specific trends, saved Insights, coverage/limitations.
Learning Candidates: evidence, contradictions, validation, promotion.
Content Memory: scope filter, current/history, provenance.

## 13. Home integration

Home may surface `ready_for_review` LearningCandidates as pending decisions, while Learning remains authoritative. Operational work keeps higher precedence:
unknown/reconciliation > blocker > stale > waiting human > approval > delivery authorization > identity readiness > learning validation.

No HomeTask.

## 14. APIs

Recommended routers: `performance_history.py` and `learning.py`.

Published history:
- GET/POST `/published-content`
- GET `/published-content/{id}`
- POST `/published-content/import`
- POST `/published-content/sync-studio`
- GET/POST `/published-content/{id}/observations`

Coverage/analysis:
- GET `/learning/coverage`
- GET `/learning/analysis`
- GET/POST `/learning/insights`
- GET `/learning/insights/{id}`

Learning:
- GET/POST `/learning-candidates`
- GET `/learning-candidates/{id}`
- POST `/learning-candidates/{id}/evidence`
- POST `/learning-candidates/{id}/submit-review`
- POST `/learning-candidates/{id}/validate`
- POST `/learning-candidates/{id}/promote-to-memory`
- DELETE archive

Memory:
- GET/POST `/content-memory`
- GET `/content-memory/{id}`
- GET `/content-memory/{id}/revisions`
- POST `/content-memory/{id}/revisions`
- DELETE archive

All owner-scoped, bounded and paginated.

## 15. Historical safety and data quality

Cross-owner refs return no disclosure. Archived history remains readable but immutable. Accepted-candidate evidence and promoted Memory provenance cannot disappear from historical reads.

Every analysis response includes record count, observation count, coverage, missing flags and limitations. Missing metrics/comments/watch-time are unknown/missing, not zero.

## 16. Migration

Additive reversible migration after `f5a000000001` or actual reconciled later head. Create seven tables: published_content_record, performance_observation, content_insight, learning_candidate, learning_candidate_evidence, content_memory_entry, content_memory_revision.

No destructive changes to DeliveryFeedback/Receipt/ContentAsset/Identity. Migration itself does not fabricate publication records.

## 17. FE-P1 performance

`/learning` stays lazy; lists and observations are paginated. TipTap/XYFlow/ProductionDesigner MUST NOT enter `/learning` initial graph. Existing `/projects` budget remains green.

## 18. Required tests

At minimum:
1. owner isolation
2. confirmed receipt only publication sync
3. unknown/failed/authorized-only creates no published record
4. Studio sync idempotency
5. external import idempotency/provenance
6. missing coverage != zero
7. observations append-only/corrections
8. no cross-key metric summation
9. free-text feedback creates no fabricated numeric metric
10. Insight provenance/coverage/limitations
11. Insight supersede preserves old row
12. LearningCandidate lifecycle gates
13. evidence cross-owner denial
14. acceptance requires evidence + validation summary
15. performance never mutates Identity/Workflow/Channel
16. promotion denied before acceptance
17. promotion idempotency
18. Memory append-only revision
19. Memory scope validation
20. Memory promotion leaves stable Identity/default Workflow unchanged
21. Home learning decision projection/dedupe
22. incomplete cohort warning
23. analyzer unavailable no fake Insight
24. F3B/F4/F5A regressions green

## 19. Rollout sequence

1. models/migration
2. history + receipt sync
3. observations + coverage
4. analysis + Insight
5. LearningCandidate/evidence/validation
6. ContentMemory/promotion
7. Identity Memory + Home integration
8. `/learning` frontend
9. targeted/full tests + bundle checks + isolated browser
10. independent review
11. canonical sync/archive only after explicit authorization

## 20. SPEC review calibration against main dd71a14

- Actual Alembic code head: f5a000000001. Graph MCP discovery tools are unavailable in this session; targeted source reads verified delivery, identity and Home integration points.
- Receipt delivered_at is currently utcnow() in both delivery.add_receipt and article_handoff.add_receipt. It is confirmation provenance, not necessarily publication time. Keep the existing receipt contract compatible; accept explicit verified published_at plus provenance in the publication domain, otherwise store null with missing-date coverage. Never infer from created_at. Reconciliation currently changes Target/Attempt without creating Receipt: skip receipt-less targets and expose the missing confirmation; do not invent historical receipts or silently alter reconciliation semantics.
- Generic and legacy receipt creation must share the materialization gate. Keep local receipt/history/audit changes atomic; backfill is an explicit bounded owner-scoped command, never a migration side effect. Eligibility uses receipt status, Candidate hash and ownership, not successful draft Attempts.
- Receipt-less reconciliation recovery uses explicit POST /published-content/confirm-reconciled with target_id, publication_attestation, idempotency_key and optional verified published_at/evidence reference. Require an owned, mutation-eligible human_confirmed target, no unresolved unknown attempts, and exact immutable Candidate/hash match. This is a new human attestation of actual publication, not inference from draft reconciliation. Lock the target and create a human_confirmed Receipt plus history/audit/project events atomically; the recovery key/payload checksum and target lock make retries deterministic. Reuse an existing qualifying receipt rather than adding another; conflicting recovery payload returns 409. Keep Target/Attempt statuses and remote systems unchanged. UI must expose this action from Historical Recovery when sync reports missing confirmation. Generic/legacy receipt APIs retain their existing state gates; the new explicit route closes the missing recovery path.
- Observation payload_json declares measurement_mode (snapshot|interval), granularity and cutoff. Snapshot analysis selects the latest effective metric per published record/compatible unit/window; interval sums require non-overlap. Corrections are same-record compatible links with serialized tip update and no competing branches; exact-import identities are database-enforced. No implicit cross-unit normalization.
- Freeze candidate evidence into validation_summary_json on accept/reject; retain source checksums and bounded source payload snapshots. accepted/rejected cannot edit proposition/evidence/scope. Candidate operations use a revision counter, lock/constraint and 409 with rollback.
- Persist MemoryEntry source_learning_candidate_id (unique), promotion idempotency key and payload checksum so retries and destination conflicts cannot create duplicate entries under races. All initial Memory APIs share the accepted-candidate promotion gate. Revision saves use expected_revision and a database unique entry/revision constraint; changed learned claims require an accepted source candidate.
- Validate ownership/hierarchy for every Insight/evidence/cohort/supersedes reference, including legacy DeliveryFeedback target authorization. Freeze historical scope labels; current ancestry is used for access/applicability, never to rewrite snapshots.
- Rule/experiment/multi_sample labels require auditable validation evidence and sample definitions. No automatic rule/experiment engine is added; unverified automation is unavailable and human attestation is labeled explicitly.
- Four MODIFIED deltas now contain full canonical blocks rather than replacement fragments; the pre-F5 Memory placeholder scenario is explicitly historical. Source package stays unchanged.

## Risks / Trade-offs

- Human-confirmed publication may lack actual publication date → preserve record with unknown date; omit from dated cohorts and expose missing-date count.
- Repeated cumulative metrics inflate results → explicit measurement grain/effective corrections; do not sum snapshots.
- Direct Memory create or concurrent promotion bypasses validation → shared server gate, unique source candidate, expected revision and atomic rollback.
- Referenced evidence can change after acceptance → immutable bounded validation/provenance snapshots; no binary duplication.
- Rule/model/experiment capability is not verified → manual workflow remains usable; capability unavailable is honest.

## Migration Plan

Use the additive migration after f5a000000001 only in an isolated development database for upgrade/downgrade/upgrade verification. Add the documented revision/uniqueness columns to the seven new resources. No production migration, backfill, deploy or remote activation is authorized.

## Open Questions

The reviewed specification changes must receive explicit user confirmation before apply under the project OpenSpec process. The required regression suite in tasks remains part of the proposed scope; no new test code is created during spec review.
