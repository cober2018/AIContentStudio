## 0. Baseline and scope gate

- [ ] 0.1 Verify `main` contains archived F5A canonical specs and real FE-P1/F3B/F4 implementation; record base commit and current migration head.
- [ ] 0.2 Create `codex/fe-f5b-performance-learning-memory` from the real baseline.
- [ ] 0.3 Preserve existing untracked user artifacts exactly; do not include them in F5B commits.
- [ ] 0.4 Record backend baseline, frontend build/bundle budgets, OpenSpec all-strict and diff-check.
- [ ] 0.5 No production migration, push, merge, deploy or external connector activation.

## 1. Additive persistence

- [ ] 1.1 Add PublishedContentRecord and coverage/provenance constraints.
- [ ] 1.2 Add PerformanceObservation immutable rows and indexes.
- [ ] 1.3 Add immutable ContentInsight.
- [ ] 1.4 Add LearningCandidate and LearningCandidateEvidence.
- [ ] 1.5 Add ContentMemoryEntry and append-only ContentMemoryRevision.
- [ ] 1.6 Add reversible migration after actual F5A head; migration itself does not fabricate published history.
- [ ] 1.7 Validate isolated SQLite upgrade/rollback/upgrade and PostgreSQL-compatible constraints.

## 2. Published history and recovery

- [ ] 2.1 Add owner-scoped PublishedContent CRUD/read/archive APIs.
- [ ] 2.2 Add idempotent Studio sync from confirmed DeliveryReceipt only.
- [ ] 2.3 Reject/skip authorized-only, failed and unresolved-unknown targets as published history.
- [ ] 2.4 Add normalized external historical import with idempotency/external provenance.
- [ ] 2.5 Add record coverage calculation/read model with explicit missing/unknown fields.
- [ ] 2.6 Preserve Candidate/Identity/Account provenance for Studio records and legacy/unknown when unprovable.

## 3. Performance observations

- [ ] 3.1 Add append-only metric/feedback/editorial/correction observation APIs.
- [ ] 3.2 Validate metric namespace/key/value/unit/time.
- [ ] 3.3 Keep cross-platform metric keys separate; no universal KPI score.
- [ ] 3.4 Reference DeliveryFeedback qualitatively without fabricating numeric metrics.
- [ ] 3.5 Add correction/supersede history without rewriting old observations.

## 4. Long-term analysis and Insight

- [ ] 4.1 Add bounded coverage and cohort-analysis endpoints.
- [ ] 4.2 Aggregate only same metric namespace/key unless explicit future normalization exists.
- [ ] 4.3 Return sample count, coverage and limitations with every analysis.
- [ ] 4.4 Add immutable ContentInsight save/read APIs with support/contradict refs.
- [ ] 4.5 Optional model analyzer must validate output and fail closed when unavailable.
- [ ] 4.6 Prevent cross-owner refs in cohort/Insight.

## 5. LearningCandidate

- [ ] 5.1 Add create/list/detail/archive with category/scope/status.
- [ ] 5.2 Add evidence bindings for published content/observation/Insight/DeliveryFeedback with support/contradict/context roles.
- [ ] 5.3 Add collecting → ready_for_review gate.
- [ ] 5.4 Add explicit accept/reject validation requiring evidence + validation method/summary.
- [ ] 5.5 Accepted/rejected history remains immutable/readable.
- [ ] 5.6 No observation/Insight/candidate action automatically mutates Identity, Workflow, Account preference or Channel config.

## 6. Content Memory

- [ ] 6.1 Add hierarchy-validated Memory scope service using FE-F3B ownership.
- [ ] 6.2 Add Memory list/detail/history/create revision APIs.
- [ ] 6.3 Add explicit accepted-candidate promotion endpoint with idempotency.
- [ ] 6.4 Freeze source LearningCandidate/evidence provenance into Memory revision.
- [ ] 6.5 Promotion denied before acceptance.
- [ ] 6.6 Memory update never silently creates Identity/Workflow/Channel revisions.
- [ ] 6.7 Archive keeps memory history readable.

## 7. Delivery / Identity / Home integration

- [ ] 7.1 Hook confirmed receipt flow to idempotent Studio publication materialization without changing delivery transaction semantics.
- [ ] 7.2 Keep unknown delivery excluded until confirmed.
- [ ] 7.3 Replace Identity Content Memory placeholder with real scoped-memory projection.
- [ ] 7.4 Add ready_for_review LearningCandidate to Home pending decisions with lower precedence than operational blockers/review decisions.
- [ ] 7.5 Do not add HomeTask or duplicate learning state.

## 8. Learning frontend

- [ ] 8.1 Replace `/learning` placeholder with lazy LearningWorkspace.
- [ ] 8.2 Historical Recovery: Studio/external records, coverage, filters and observation timeline.
- [ ] 8.3 Long-term Analysis: cohort filters, metric-specific summaries, Insights and coverage warnings.
- [ ] 8.4 Learning Candidates: evidence, contradictions, validation and promotion actions.
- [ ] 8.5 Content Memory: scope filters, current/history, source candidate and limitations.
- [ ] 8.6 Identity Memory tab reads same canonical memory APIs.
- [ ] 8.7 Missing data is visibly unknown/missing, never rendered as zero.
- [ ] 8.8 Pagination/bounded fetches for large history.

## 9. FE-P1 performance

- [ ] 9.1 `/learning` remains lazy.
- [ ] 9.2 No TipTap/XYFlow/ProductionDesigner in Learning initial static graph.
- [ ] 9.3 Existing `/projects` bundle budget remains green.
- [ ] 9.4 Add Learning route budget check if supported by existing budget tooling.

## 10. Targeted regression tests

- [ ] 10.1 owner isolation for all new resources
- [ ] 10.2 confirmed receipt only publication sync
- [ ] 10.3 unknown/failed/authorized-only does not publish
- [ ] 10.4 studio sync idempotency
- [ ] 10.5 external import idempotency/provenance
- [ ] 10.6 coverage missing != zero
- [ ] 10.7 observation append-only/correction
- [ ] 10.8 metric key isolation/no cross-key sum
- [ ] 10.9 free-text feedback no fabricated numeric metric
- [ ] 10.10 Insight provenance/limitations/supersede
- [ ] 10.11 LearningCandidate lifecycle/evidence validation
- [ ] 10.12 acceptance requires evidence + validation summary
- [ ] 10.13 no automatic stable-domain mutation
- [ ] 10.14 promotion denied before acceptance
- [ ] 10.15 promotion idempotency
- [ ] 10.16 Memory append-only revision/scope validation
- [ ] 10.17 Home learning decision/dedupe
- [ ] 10.18 incomplete cohort warning
- [ ] 10.19 analyzer unavailable no fake Insight
- [ ] 10.20 F3B/F4/F5A regressions green

## 11. Verification and handoff

- [ ] 11.1 Full backend suite + targeted F5B tests.
- [ ] 11.2 Frontend TypeScript/Vite build + FE-P1 budget.
- [ ] 11.3 OpenSpec all strict + git diff --check + relevant Ruff checks.
- [ ] 11.4 Isolated browser: confirmed Studio publication → metric → Insight → LearningCandidate → validation → Memory.
- [ ] 11.5 Isolated browser: external historical import with missing coverage.
- [ ] 11.6 Verify Identity Memory shows promoted memory while identity revisions remain unchanged.
- [ ] 11.7 Verify Home pending learning decision and reload persistence.
- [ ] 11.8 Independent review before archive; no archive/commit/push/merge/deploy without explicit authorization.
