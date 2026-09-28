## 0. Baseline and scope gate

- [x] 0.1 Verify post-F5B canonical main, FE-P1 spec and migration head `f5b000000001`; record actual base commit.
- [x] 0.2 Create `codex/fe-f5c-system-assets-knowledge-settings`.
- [x] 0.3 Preserve all existing user-supplied untracked artifacts and exclude them from commits.
- [x] 0.4 Record backend/frontend/bundle/OpenSpec/diff-check baseline.
- [x] 0.5 No push, merge, deploy, production migration, tenant-auth rewrite or new external connector implementation.

## 1. Knowledge Collection persistence

- [x] 1.1 Add KnowledgeCollection.
- [x] 1.2 Add KnowledgeCollectionItem with exact-one-FK/type constraints.
- [x] 1.3 Add active/detached item lifecycle and archive-safe collection semantics.
- [x] 1.4 Add reversible migration after actual F5B head; no synthetic collections/backfill.
- [x] 1.5 Validate SQLite up/down/up and PostgreSQL-compatible DDL.

## 2. Unified System Library backend

- [x] 2.1 Add bounded unified list/summary service over Material, SourceDocument, FactPack and KnowledgeCollection.
- [x] 2.2 Add typed filters/search/pagination.
- [x] 2.3 Add Material rights/provenance summary from current MaterialRevision.
- [x] 2.4 Add Source parse/trust/provenance summary with `not_decided_at_source_level` rights state.
- [x] 2.5 Add FactPack status/evidence/rights aggregate summary.
- [x] 2.6 Add bounded usage projection for Material/Source/FactPack.
- [x] 2.7 Do not load raw Source text, media bytes, full FactPack snapshots or Candidate manifests in list endpoints.
- [x] 2.8 Explicitly expose library scope as current `system_shared`; do not fabricate owner isolation.

## 3. Knowledge Collection APIs

- [x] 3.1 CRUD/archive KnowledgeCollection.
- [x] 3.2 Add/detach/reactivate SourceDocument items.
- [x] 3.3 Add/detach/reactivate FactPack items.
- [x] 3.4 Duplicate active add is idempotent/conflict-safe.
- [x] 3.5 Archived collection rejects mutation but remains readable.
- [x] 3.6 Collection membership never copies source/fact data or changes rights/evidence state.

## 4. Project reuse integration

- [x] 4.1 Add UI/API helper to attach exact MaterialRevision through ProjectMaterialReference.
- [x] 4.2 Add UI/API helper to attach SourceDocument through ProjectSourceBinding.
- [x] 4.3 FactPack from library deep-links/uses existing explicit Fact Boundary flow.
- [x] 4.4 KnowledgeCollection itself cannot bind as Fact Boundary.
- [x] 4.5 Reuse actions enforce Project ownership and archive safety.
- [x] 4.6 Verify no byte/text duplication.

## 5. `/assets` frontend

- [x] 5.1 Replace placeholder with lazy SystemAssetsKnowledgePage.
- [x] 5.2 Implement All tab with unified search/filter/pagination.
- [x] 5.3 Material tab reuses upload/generate/search/detail/revision/rights actions.
- [x] 5.4 Documents & Web tab reuses Source import/detail/parse/fact actions.
- [x] 5.5 Evidence Packs tab reuses FactPack builder/detail/version/freeze semantics.
- [x] 5.6 Knowledge Collections tab create/archive/add/detach/order items.
- [x] 5.7 Add usage/provenance/rights panels with truthful unknown/not-decided states.
- [x] 5.8 Add explicit Project reuse actions; no silent Fact Boundary bind.
- [x] 5.9 Preserve legacy routes as compatibility links.

## 6. Product Settings read models

- [x] 6.1 Add `product_settings` service.
- [x] 6.2 Models section composes existing safe/masked settings.
- [x] 6.3 Data Sources section composes Data Source Plugin descriptors + Connector state.
- [x] 6.4 Channels section mirrors Channel Registry and editability metadata.
- [x] 6.5 Rules section mirrors Rule Registry plus versioned templates/prompts/discoverability resources.
- [x] 6.6 Team section shows current users/roles and development/header auth limitation.
- [x] 6.7 Advanced section preserves existing runtime/storage/security/dsh/skills/MCP diagnostics.
- [x] 6.8 No plaintext secret in any new projection.

## 7. `/settings` frontend productization

- [x] 7.1 Restructure sections into Models & AI / Data Sources / Channels / Rules & Templates / Team & Permissions / Advanced.
- [x] 7.2 Keep existing model/image/settings mutations functional.
- [x] 7.3 Data Source Plugin cards show available/unavailable reason and capabilities.
- [x] 7.4 Existing generic Connector management remains clearly separate from plugin executability.
- [x] 7.5 Channel registry shown read-only where no durable mutator exists.
- [x] 7.6 Rules vs Prompt/Template labels remain distinct.
- [x] 7.7 Team UI explicitly states current development auth limitations.
- [x] 7.8 Advanced runtime controls remain admin gated.

## 8. FE-P1 performance

- [x] 8.1 `/assets` and `/settings` remain lazy route boundaries.
- [x] 8.2 `/assets` initial graph excludes ProductionDesigner/TipTap/XYFlow and full raw resource payloads.
- [x] 8.3 `/settings` initial graph remains within canonical budget; heavy advanced panels may lazy-load if needed.
- [x] 8.4 Existing `/projects` budget remains green.

## 9. Targeted regression tests

- [x] 9.1 collection create/archive/read
- [x] 9.2 collection item exact-one-FK/type constraints
- [x] 9.3 duplicate add/reactivation
- [x] 9.4 archived mutation rejection
- [x] 9.5 collection no source/fact copy
- [x] 9.6 collection cannot bind Fact Boundary
- [x] 9.7 system library bounded list
- [x] 9.8 material rights unknown/revoked
- [x] 9.9 source rights not-decided-at-source-level
- [x] 9.10 FactPack rights aggregate
- [x] 9.11 usage projection correctness
- [x] 9.12 project reuse by reference/no duplication
- [x] 9.13 Data Source Plugin settings parity
- [x] 9.14 disconnected plugin remains unavailable
- [x] 9.15 Channel settings parity/no duplicate persistence
- [x] 9.16 Rule vs prompt/template inventory
- [x] 9.17 secret masking
- [x] 9.18 admin mutation gates
- [x] 9.19 Team development-auth truthfulness
- [x] 9.20 F2/F3A/F3B/F4/F5A/F5B regressions green

## 10. Verification and handoff

- [x] 10.1 Full backend suite + targeted F5C tests.
- [x] 10.2 Frontend TypeScript/Vite build + FE-P1 bundle budgets.
- [x] 10.3 OpenSpec all strict + git diff --check + Ruff.
- [x] 10.4 Isolated browser: Material/Source/FactPack/Collection flows and Project reference reuse.
- [x] 10.5 Isolated browser: Settings all six sections, unavailable plugin reasons, channel/rule truth, secret masking.
- [x] 10.6 Reload persistence and legacy-route compatibility.
- [x] 10.7 Independent review before archive.
- [x] 10.8 No archive/commit/push/merge/deploy/production migration without explicit authorization.


## 11. Review-calibrated invariants

- [x] 11.1 Verify no foreign Project/Opportunity usage IDs, titles or existence counts leak to another user.
- [x] 11.2 Add expected_revision, explicit reorder/item edit and archive-safe concurrent collection mutation checks.
- [x] 11.3 Validate type-specific filters, deterministic cross-type pagination and database-bounded lightweight queries.
- [x] 11.4 Verify false/NULL/revoked rights and empty pack readiness without invented permission fields.
- [x] 11.5 Verify safe Settings allowlists, URL/config credential redaction and role-derived editability.
- [x] 11.6 Add named Assets/Settings bundle checks and preserve all earlier canonical requirements/scenarios.
- [x] 11.7 Verify per-status template actions, cold-start rules/fallback semantics and configured-vs-verified channel capability.
- [x] 11.8 Verify complete model snapshot edits, blank-secret retention and explicit image/network side effects with exact pull roles.
