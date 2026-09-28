# FE-F5C System Assets, Knowledge and Settings Implementation Plan

> **For agentic workers:** Use executing-plans for controller integration and dispatching-parallel-agents for disjoint backend/frontend tasks. Track verified completion only.

**Goal:** Productize Assets and Settings over existing authoritative resources, with reference-only Knowledge Collections and honest rights/capability state.

**Architecture:** Add two collection tables and lightweight, SQL-bounded Library/Usage and safe Settings projections. Preserve current shared-library scope and exact existing API permissions; private Project/Opportunity usage remains ownership-scoped. Keep both routes lazy and heavy legacy tools behind explicit actions.

**Tech Stack:** Existing FastAPI/SQLAlchemy/Alembic/pytest and React/TypeScript/TanStack Query/Vite; no new runtime dependencies.

## Execution boundary

- Subsequent user authorization: local commit and integration into main are authorized. Preserve the worktree for canonical sync/archive; no push, deploy or production migration.

- Base main49d6c4b, code head f5b000000001, isolated branch codex/fe-f5c-system-assets-knowledge-settings.
- User explicitly authorized targeted regression tests and implementation following complete spec review. Do not commit, merge, archive, push, deploy or run production migrations in this apply phase.
- User source package/ZIP remains untouched. Standard artifacts: openspec/changes/fe-f5c-system-assets-knowledge-settings/.

## 1. /// Review and baseline

- [x] Compare all five specs and preserve old MODIFIED requirement/scenario blocks; independent safety SPEC review.
- [x] Record strict/diff-check, isolated full pytest, build/bundle before business edits.
- [x] Get OpenSpec apply instructions and execute pending tasks without treating CLI validation as semantic acceptance.

## 2. /// Library and Collections backend

Files: apps/api/app/models.py; apps/api/alembic/versions/f5c000000001_system_knowledge.py; app/services/{system_library,library_usage,knowledge_collections}.py; app/routers/system_library.py; tests/test_system_library.py; tests/test_knowledge_collections.py.

- [x] Write expected endpoint/constraint tests, run and observe missing-feature failures.
- [x] Two exact-FK constrained collection tables, revision CAS, active/detached unique items, explicit note/order/reorder, archive read-only.
- [x] Library list returns items,total,offset,limit with type/id/title/status/scope and small rights/provenance fields; SQL UNION pagination and no raw Source text/media/snapshots in list/summary.
- [x] Usage counts/links filter owned Project/Opportunity references, expose category coverage and avoid arbitrary manifest scans.
- [x] Rights derive exact latest MaterialRevision and FactPackItem snapshot/revocation fields. Source publication rights not_decided_at_source_level; false, NULL and revoked distinct.
- [x] Reuse existing POST project sources/material references and explicit Fact Boundary APIs, no new attach engine.
- [x] Isolated SQLite up/down/up; compile PostgreSQL DDL only, do not claim real PG concurrency acceptance.

## 3. /// Settings backend

Files: app/services/product_settings.py; app/routers/product_settings.py; tests/test_product_settings.py.

- [x] Test roles, secret-bearing nested values/URLs, registry parity and unavailable plugin before implementation.
- [x] GET /settings/product, /settings/data-sources, /settings/channels, /settings/rules, /settings/team over existing sources only.
- [x] Safe allowlisted metadata, exact underlying role gates, admin-only dangerous config inventories; never pass through SystemSetting/Connector raw data.
- [x] Data Source plugin executability remains descriptor-derived; rules/prompts/templates distinct; no invites/SSO pretend capability.

## 4. /// Assets frontend

Files: apps/web/src/product/{SystemAssetsKnowledgePage,systemLibraryTypes}.tsx/ts.

- [x] Five real tabs, stable query keys including currentUser, bounded search/pagination, useful error/loading/empty states.
- [x] Collections create/edit/archive, explicit Source/FactPack add/detach/reactivation and ordered reference edits using current revision.
- [x] Lazy details and previews, rights and authorized usage panels; source import and material upload use existing APIs with explicit permissions.
- [x] Exact MaterialRevision/Source project actions and explicit frozen FactPack boundary selection; archived users/resources/project fail closed.
- [x] Preserve legacy tooling via explicit deep links, not initial heavy workspace imports.

## 5. /// Settings frontend and controller integration

Files: app/main.py; apps/web/src/App.tsx; apps/web/src/product/ProductSettingsPage.tsx; apps/web/src/pages/Settings.tsx only if needed for explicit subsection reuse; apps/web/scripts/check-bundle.mjs.

- [x] Wire two routers and lazy Assets/Settings routes; preserve /legacy/settings and other compatibility paths.
- [x] Six sections with real read_only/editable/unavailable states; authorized existing model/image mutation controls stay reachable without inventing save APIs.
- [x] Add named /assets and /settings bundle gates; preserve projects raw/gzip reporting and exclude TipTap/XYFlow.
- [x] Independent SPEC then QUALITY review of each slice; fix relevant findings with regression evidence.

## 6. /// Full acceptance and handoff

- [x] DATABASE_URL=sqlite:////tmp/<isolated>/studio.db NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 /Users/mshengran/Project/AIContentStudio/apps/api/.venv/bin/python -m pytest -q from worktree/apps/api.
- [x] npm run build from worktree/apps/web, relevant Ruff, openspec validate --all --strict, git diff --check.
- [x] Isolated API/Vite browser: all Assets/Settings tabs, source/material/reference/collection persistence, explicit evidence gate and masked/unavailable state.
- [x] Update README, task_plan.md, progress.md, findings.md and OpenSpec task checkboxes only for actually verified results. Report remaining tasks honestly; leave archive/commit/main integration for separate authorization.

## Flow

System MaterialRevision / SourceDocument / FactPack
→ bounded shared Library metadata
→ explicit authorized Project reference / Fact Boundary action

KnowledgeCollection → Source / exact FactPack references only (not evidence authority)

Registry / safe configuration → role-filtered Settings projection
→ editable / read_only / unavailable
