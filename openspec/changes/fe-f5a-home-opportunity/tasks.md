## 1. Baseline and additive persistence

- [ ] 1.1 Before apply, verify the active workspace exposes FE-P1 commit `85b8c08`, canonical `fe-p1-frontend-bundle-performance`, and the archived FE-P1 change; stop before business-code changes if the connector/workspace is still on the older FE-F4 baseline.
- [ ] 1.2 Add the three owner-scoped opportunity models, lifecycle constraints, revision/signal indexes, and an additive Alembic migration; do not backfill or mutate existing Topic/Source/Project rows.
- [ ] 1.3 Add stable serialization and authorization helpers for opportunities, signals, assessments, and conversion provenance; preserve append-only assessment and immutable signal semantics.

## 2. Opportunity domain and conversion

- [ ] 2.1 Implement owner-scoped opportunity CRUD, lifecycle transitions, filtering, pagination, and stable project events.
- [ ] 2.2 Implement signal creation/readback with SourceDocument/DataSnapshot lineage validation and manual-signal fallback; never rewrite source rows or historical signals.
- [ ] 2.3 Implement append-only assessment revisions with checksum, identity-scope validation, confidence, risks, and suggestion-state serialization.
- [ ] 2.4 Implement explicit qualified-opportunity conversion with current-assessment and idempotency gates, one project plus Brief v1 and durable origin provenance, optional selected SourceDocument bindings, and atomic rollback; never create Topics, FactPacks, Fact Boundaries, or IdentitySnapshots.
- [ ] 2.5 Add the FE-F3A project-core conversion entry point while preserving Brief revision, Source binding, Fact Boundary, ownership, and archived-project invariants.

## 3. Home and Opportunity workspaces

- [ ] 3.1 Add bounded `/content-opportunities`, `/content-opportunities/{id}`, and `/home` read APIs that compose authoritative opportunity, project Overview, ProjectEvent, Review, Delivery, and identity-readiness facts without a duplicate status table.
- [ ] 3.2 Add route-level Home and Opportunity page modules, replacing the two placeholders while preserving shell navigation and FE-P1 lazy-loading boundaries.
- [ ] 3.3 Implement opportunity triage/detail/assessment/conversion UI with explicit suggestion labels, signal lineage, risks, confidence, and links to existing Source/Evidence/Project routes.
- [ ] 3.4 Implement Home sections for opportunities, pending decisions, active projects, blocked/stale/unknown/identity risks, and recent project activity; preserve partial-data warnings and link actions to authoritative pages.
- [ ] 3.5 Keep “近期计划” out of the domain unless a persisted scheduling contract exists; display recent activity/updated projects with truthful labels.

## 4. Verification and handoff

- [ ] 4.1 Run isolated additive migration upgrade/rollback checks and the existing backend regression suite without writing to a production database or adding a new test suite; manually verify analyzer-unavailable behavior if the optional capability is absent.
- [ ] 4.2 Run frontend TypeScript/Vite build, FE-P1 bundle budget, OpenSpec strict validation, and `git diff --check`; confirm Home/Opportunity route chunks do not pull TipTap/XYFlow or regress `/projects` initial budget.
- [ ] 4.3 Perform isolated browser verification for opportunity lifecycle, assessment revision, explicit conversion, no auto-bound evidence, Home projection links, ownership filtering, and refresh persistence.
- [ ] 4.4 Update README, progress, findings, and implementation plan with actual evidence; request independent review before archive. Do not push, merge, deploy, or run production migrations.
