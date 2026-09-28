## 0. Baseline and scope gate

- [ ] 0.1 Verify post-F5B canonical main, FE-P1 spec and migration head `f5b000000001`; record actual base commit.
- [ ] 0.2 Create `codex/fe-f5c-system-assets-knowledge-settings`.
- [ ] 0.3 Preserve all existing user-supplied untracked artifacts and exclude them from commits.
- [ ] 0.4 Record backend/frontend/bundle/OpenSpec/diff-check baseline.
- [ ] 0.5 No push, merge, deploy, production migration, tenant-auth rewrite or new external connector implementation.

## 1. Knowledge Collection persistence

- [ ] 1.1 Add KnowledgeCollection.
- [ ] 1.2 Add KnowledgeCollectionItem with exact-one-FK/type constraints.
- [ ] 1.3 Add active/detached item lifecycle and archive-safe collection semantics.
- [ ] 1.4 Add reversible migration after actual F5B head; no synthetic collections/backfill.
- [ ] 1.5 Validate SQLite up/down/up and PostgreSQL-compatible DDL.

## 2. Unified System Library backend

- [ ] 2.1 Add bounded unified list/summary service over Material, SourceDocument, FactPack and KnowledgeCollection.
- [ ] 2.2 Add typed filters/search/pagination.
- [ ] 2.3 Add Material rights/provenance summary from current MaterialRevision.
- [ ] 2.4 Add Source parse/trust/provenance summary with `not_decided_at_source_level` rights state.
- [ ] 2.5 Add FactPack status/evidence/rights aggregate summary.
- [ ] 2.6 Add bounded usage projection for Material/Source/FactPack.
- [ ] 2.7 Do not load raw Source text, media bytes, full FactPack snapshots or Candidate manifests in list endpoints.
- [ ] 2.8 Explicitly expose library scope as current `system_shared`; do not fabricate owner isolation.

## 3. Knowledge Collection APIs

- [ ] 3.1 CRUD/archive KnowledgeCollection.
- [ ] 3.2 Add/detach/reactivate SourceDocument items.
- [ ] 3.3 Add/detach/reactivate FactPack items.
- [ ] 3.4 Duplicate active add is idempotent/conflict-safe.
- [ ] 3.5 Archived collection rejects mutation but remains readable.
- [ ] 3.6 Collection membership never copies source/fact data or changes rights/evidence state.

## 4. Project reuse integration

- [ ] 4.1 Add UI/API helper to attach exact MaterialRevision through ProjectMaterialReference.
- [ ] 4.2 Add UI/API helper to attach SourceDocument through ProjectSourceBinding.
- [ ] 4.3 FactPack from library deep-links/uses existing explicit Fact Boundary flow.
- [ ] 4.4 KnowledgeCollection itself cannot bind as Fact Boundary.
- [ ] 4.5 Reuse actions enforce Project ownership and archive safety.
- [ ] 4.6 Verify no byte/text duplication.

## 5. `/assets` frontend

- [ ] 5.1 Replace placeholder with lazy SystemAssetsKnowledgePage.
- [ ] 5.2 Implement All tab with unified search/filter/pagination.
- [ ] 5.3 Material tab reuses upload/generate/search/detail/revision/rights actions.
- [ ] 5.4 Documents & Web tab reuses Source import/detail/parse/fact actions.
- [ ] 5.5 Evidence Packs tab reuses FactPack builder/detail/version/freeze semantics.
- [ ] 5.6 Knowledge Collections tab create/archive/add/detach/order items.
- [ ] 5.7 Add usage/provenance/rights panels with truthful unknown/not-decided states.
- [ ] 5.8 Add explicit Project reuse actions; no silent Fact Boundary bind.
- [ ] 5.9 Preserve legacy routes as compatibility links.

## 6. Product Settings read models

- [ ] 6.1 Add `product_settings` service.
- [ ] 6.2 Models section composes existing safe/masked settings.
- [ ] 6.3 Data Sources section composes Data Source Plugin descriptors + Connector state.
- [ ] 6.4 Channels section mirrors Channel Registry and editability metadata.
- [ ] 6.5 Rules section mirrors Rule Registry plus versioned templates/prompts/discoverability resources.
- [ ] 6.6 Team section shows current users/roles and development/header auth limitation.
- [ ] 6.7 Advanced section preserves existing runtime/storage/security/dsh/skills/MCP diagnostics.
- [ ] 6.8 No plaintext secret in any new projection.

## 7. `/settings` frontend productization

- [ ] 7.1 Restructure sections into Models & AI / Data Sources / Channels / Rules & Templates / Team & Permissions / Advanced.
- [ ] 7.2 Keep existing model/image/settings mutations functional.
- [ ] 7.3 Data Source Plugin cards show available/unavailable reason and capabilities.
- [ ] 7.4 Existing generic Connector management remains clearly separate from plugin executability.
- [ ] 7.5 Channel registry shown read-only where no durable mutator exists.
- [ ] 7.6 Rules vs Prompt/Template labels remain distinct.
- [ ] 7.7 Team UI explicitly states current development auth limitations.
- [ ] 7.8 Advanced runtime controls remain admin gated.

## 8. FE-P1 performance

- [ ] 8.1 `/assets` and `/settings` remain lazy route boundaries.
- [ ] 8.2 `/assets` initial graph excludes ProductionDesigner/TipTap/XYFlow and full raw resource payloads.
- [ ] 8.3 `/settings` initial graph remains within canonical budget; heavy advanced panels may lazy-load if needed.
- [ ] 8.4 Existing `/projects` budget remains green.

## 9. Targeted regression tests

- [ ] 9.1 collection create/archive/read
- [ ] 9.2 collection item exact-one-FK/type constraints
- [ ] 9.3 duplicate add/reactivation
- [ ] 9.4 archived mutation rejection
- [ ] 9.5 collection no source/fact copy
- [ ] 9.6 collection cannot bind Fact Boundary
- [ ] 9.7 system library bounded list
- [ ] 9.8 material rights unknown/revoked
- [ ] 9.9 source rights not-decided-at-source-level
- [ ] 9.10 FactPack rights aggregate
- [ ] 9.11 usage projection correctness
- [ ] 9.12 project reuse by reference/no duplication
- [ ] 9.13 Data Source Plugin settings parity
- [ ] 9.14 disconnected plugin remains unavailable
- [ ] 9.15 Channel settings parity/no duplicate persistence
- [ ] 9.16 Rule vs prompt/template inventory
- [ ] 9.17 secret masking
- [ ] 9.18 admin mutation gates
- [ ] 9.19 Team development-auth truthfulness
- [ ] 9.20 F2/F3A/F3B/F4/F5A/F5B regressions green

## 10. Verification and handoff

- [ ] 10.1 Full backend suite + targeted F5C tests.
- [ ] 10.2 Frontend TypeScript/Vite build + FE-P1 bundle budgets.
- [ ] 10.3 OpenSpec all strict + git diff --check + Ruff.
- [ ] 10.4 Isolated browser: Material/Source/FactPack/Collection flows and Project reference reuse.
- [ ] 10.5 Isolated browser: Settings all six sections, unavailable plugin reasons, channel/rule truth, secret masking.
- [ ] 10.6 Reload persistence and legacy-route compatibility.
- [ ] 10.7 Independent review before archive.
- [ ] 10.8 No archive/commit/push/merge/deploy/production migration without explicit authorization.
