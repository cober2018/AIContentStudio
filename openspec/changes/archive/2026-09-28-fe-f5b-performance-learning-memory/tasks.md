## 0. Baseline and scope gate

- [x] 0.1 Verify `main` contains archived F5A canonical specs and real FE-P1/F3B/F4 implementation; record base commit and current migration head.
- [x] 0.2 Create `codex/fe-f5b-performance-learning-memory` from the real baseline.
- [x] 0.3 Preserve existing untracked user artifacts exactly; do not include them in F5B commits.
- [x] 0.4 Record backend baseline, frontend build/bundle budgets, OpenSpec all-strict and diff-check.
- [x] 0.5 No production migration, push, merge, deploy or external connector activation.

## 1. Additive persistence

- [x] 1.1 Add PublishedContentRecord and coverage/provenance constraints.
- [x] 1.2 Add PerformanceObservation immutable rows and indexes.
- [x] 1.3 Add immutable ContentInsight.
- [x] 1.4 Add LearningCandidate and LearningCandidateEvidence.
- [x] 1.5 Add ContentMemoryEntry and append-only ContentMemoryRevision.
- [x] 1.6 Add reversible migration after actual F5A head; migration itself does not fabricate published history.
- [x] 1.7 Validate isolated SQLite upgrade/rollback/upgrade and PostgreSQL-compatible constraints.

## 2. Published history and recovery

- [x] 2.1 Add owner-scoped PublishedContent CRUD/read/archive APIs.
- [x] 2.2 Add idempotent Studio sync from confirmed DeliveryReceipt only.
- [x] 2.3 Reject/skip authorized-only, failed and unresolved-unknown targets as published history.
- [x] 2.4 Add normalized external historical import with idempotency/external provenance.
- [x] 2.5 Add record coverage calculation/read model with explicit missing/unknown fields.
- [x] 2.6 Preserve Candidate/Identity/Account provenance for Studio records and legacy/unknown when unprovable.

## 3. Performance observations

- [x] 3.1 Add append-only metric/feedback/editorial/correction observation APIs.
- [x] 3.2 Validate metric namespace/key/value/unit/time.
- [x] 3.3 Keep cross-platform metric keys separate; no universal KPI score.
- [x] 3.4 Reference DeliveryFeedback qualitatively without fabricating numeric metrics.
- [x] 3.5 Add correction/supersede history without rewriting old observations.

## 4. Long-term analysis and Insight

- [x] 4.1 Add bounded coverage and cohort-analysis endpoints.
- [x] 4.2 Aggregate only same metric namespace/key unless explicit future normalization exists.
- [x] 4.3 Return sample count, coverage and limitations with every analysis.
- [x] 4.4 Add immutable ContentInsight save/read APIs with support/contradict refs.
- [x] 4.5 Optional model analyzer must validate output and fail closed when unavailable.
- [x] 4.6 Prevent cross-owner refs in cohort/Insight.

## 5. LearningCandidate

- [x] 5.1 Add create/list/detail/archive with category/scope/status.
- [x] 5.2 Add evidence bindings for published content/observation/Insight/DeliveryFeedback with support/contradict/context roles.
- [x] 5.3 Add collecting → ready_for_review gate.
- [x] 5.4 Add explicit accept/reject validation requiring evidence + validation method/summary.
- [x] 5.5 Accepted/rejected history remains immutable/readable.
- [x] 5.6 No observation/Insight/candidate action automatically mutates Identity, Workflow, Account preference or Channel config.

## 6. Content Memory

- [x] 6.1 Add hierarchy-validated Memory scope service using FE-F3B ownership.
- [x] 6.2 Add Memory list/detail/history/create revision APIs.
- [x] 6.3 Add explicit accepted-candidate promotion endpoint with idempotency.
- [x] 6.4 Freeze source LearningCandidate/evidence provenance into Memory revision.
- [x] 6.5 Promotion denied before acceptance.
- [x] 6.6 Memory update never silently creates Identity/Workflow/Channel revisions.
- [x] 6.7 Archive keeps memory history readable.

## 7. Delivery / Identity / Home integration

- [x] 7.1 Hook confirmed receipt flow to idempotent Studio publication materialization without changing delivery transaction semantics.
- [x] 7.2 Keep unknown delivery excluded until confirmed.
- [x] 7.3 Replace Identity Content Memory placeholder with real scoped-memory projection.
- [x] 7.4 Add ready_for_review LearningCandidate to Home pending decisions with lower precedence than operational blockers/review decisions.
- [x] 7.5 Do not add HomeTask or duplicate learning state.

## 8. Learning frontend

- [x] 8.1 Replace `/learning` placeholder with lazy LearningWorkspace.
- [x] 8.2 Historical Recovery: Studio/external records, coverage, filters and observation timeline.
- [x] 8.3 Long-term Analysis: cohort filters, metric-specific summaries, Insights and coverage warnings.
- [x] 8.4 Learning Candidates: evidence, contradictions, validation and promotion actions.
- [x] 8.5 Content Memory: scope filters, current/history, source candidate and limitations.
- [x] 8.6 Identity Memory tab reads same canonical memory APIs.
- [x] 8.7 Missing data is visibly unknown/missing, never rendered as zero.
- [x] 8.8 Pagination/bounded fetches for large history.

## 9. FE-P1 performance

- [x] 9.1 `/learning` remains lazy.
- [x] 9.2 No TipTap/XYFlow/ProductionDesigner in Learning initial static graph.
- [x] 9.3 Existing `/projects` bundle budget remains green.
- [x] 9.4 Add Learning route budget check if supported by existing budget tooling.

## 10. Targeted regression tests

- [x] 10.1 owner isolation for all new resources
- [x] 10.2 confirmed receipt only publication sync
- [x] 10.3 unknown/failed/authorized-only does not publish
- [x] 10.4 studio sync idempotency
- [x] 10.5 external import idempotency/provenance
- [x] 10.6 coverage missing != zero
- [x] 10.7 observation append-only/correction
- [x] 10.8 metric key isolation/no cross-key sum
- [x] 10.9 free-text feedback no fabricated numeric metric
- [x] 10.10 Insight provenance/limitations/supersede
- [x] 10.11 LearningCandidate lifecycle/evidence validation
- [x] 10.12 acceptance requires evidence + validation summary
- [x] 10.13 no automatic stable-domain mutation
- [x] 10.14 promotion denied before acceptance
- [x] 10.15 promotion idempotency
- [x] 10.16 Memory append-only revision/scope validation
- [x] 10.17 Home learning decision/dedupe
- [x] 10.18 incomplete cohort warning
- [x] 10.19 analyzer unavailable no fake Insight
- [x] 10.20 F3B/F4/F5A regressions green

## 11. Verification and handoff

- [x] 11.1 Full backend suite + targeted F5B tests.
- [x] 11.2 Frontend TypeScript/Vite build + FE-P1 budget.
- [x] 11.3 OpenSpec all strict + git diff --check + relevant Ruff checks.
- [x] 11.4 Isolated browser: confirmed Studio publication → metric → Insight → LearningCandidate → validation → Memory.
- [x] 11.5 Isolated browser: external historical import with missing coverage.
- [x] 11.6 Verify Identity Memory shows promoted memory while identity revisions remain unchanged.
- [x] 11.7 Verify Home pending learning decision and reload persistence.
- [x] 11.8 Independent review before archive; no archive/commit/push/merge/deploy without explicit authorization.

## 12. SPEC review boundary regressions

- [x] 12.1 Distinguish confirmation time from verified publication time; test receipt-less reconciliation and both generic/legacy receipt hooks.
- [x] 12.2 Enforce snapshot/interval/unit/window grain, correction tip isolation, cutoff and no double-counting.
- [x] 12.3 Validate owner scope for all references and derive truthful coverage; prevent source/provider provenance spoofing.
- [x] 12.4 Serialize candidate lifecycle/evidence/acceptance; freeze exact evidence and method provenance with expected_revision/409.
- [x] 12.5 Close direct Memory create/revision bypass, archived mutation, promotion races/destination conflicts and revision conflicts.
- [x] 12.6 Inspect all four MODIFIED deltas for canonical retention before eventual sync/archive.
- [x] 12.7 Add explicit owner-authorized confirm-reconciled publication recovery and UI entry point; verify no unresolved unknown, exact Candidate/hash, atomic Receipt/history/events, retry/conflict behavior and unchanged remote/Target/Attempt state.
