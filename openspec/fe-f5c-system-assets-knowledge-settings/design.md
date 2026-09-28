## Context

Existing durable resources:
- `SourceDocument` + `Fact` for imported documents/web/files and extracted evidence candidates.
- `FactPack` + immutable snapshot items for explicit evidence boundaries.
- `Material` + immutable `MaterialRevision` for reusable media bytes and rights metadata.
- FE-F3A `ProjectSourceBinding` and `ProjectMaterialReference`.
- FE-F2 `ProjectWorkflowOutput` and Data Source Plugin descriptors.
- existing generic Connector/Endpoint APIs that produce SourceDocument/Fact rows.
- Channel Registry and content-harness Plugin Registry.
- existing model/image/runtime/security settings.
- existing User/role read APIs.

Current gaps:
- `/assets` is still a placeholder.
- Source/Material/FactPack are split across legacy pages with inconsistent list/filter/usage views.
- There is no Knowledge Collection grouping object.
- current Settings is large and infrastructure-centric, with no product-level Data Source Plugin, Channel and Rule inventory sections.

## Goals / Non-Goals

**Goals**
- one product workspace for system/shared reusable assets and knowledge;
- no duplicated binary/text/evidence truth stores;
- clear provenance, rights and usage explanations;
- Knowledge Collections that organize existing resources by reference;
- product-level Settings over existing registries/configuration;
- explicit editable vs read-only vs unavailable states;
- preserve project reuse-by-reference and evidence safety;
- preserve current V1 shared-system scope honestly.

**Non-Goals**
- multi-tenant organization/workspace ownership migration;
- replacement of SourceDocument, Material or FactPack;
- new ContentAsset/Candidate semantics;
- automatic public-use rights inference;
- new Notion/Obsidian/media/API/SQL connector implementation;
- new channel registry persistence;
- new rule engine;
- production-grade invitation/SSO/team administration;
- deletion of legacy routes.

## Hard prerequisite before apply

Apply only from the real post-F5B canonical baseline:
- FE-F5B archive and canonical specs visible;
- migration head `f5b000000001` or later reconciled head;
- FE-P1 performance capability canonical;
- no tracked changes outside the task scope.

## 1. System library is a projection, not a new Asset truth store

Do NOT create a generic `SystemAsset`, `LibraryAsset`, or replacement table that copies existing resources.

Add service:
`services/system_library.py`

Unified list item types:
- `material`
- `source`
- `fact_pack`
- `knowledge_collection`

Each item returns bounded metadata:
- stable type/id
- title/name
- subtype/kind/source_type
- lifecycle status
- latest revision/version/checksum where applicable
- provenance summary
- rights/readiness summary
- usage summary/counts
- created_at / updated-ish timestamp
- deep-link target

List endpoint must not load raw Source text, Material bytes, full FactPack snapshots or full Candidate manifests.

## 2. Current library scope remains system-shared

Existing SourceDocument, Material and FactPack are global/shared under the current V1 auth model; they do not have owner_user_id.

F5C MUST NOT pretend they are owner-scoped.

Product UI/API labels this scope truthfully as `system_shared`.

Read:
- authenticated users follow current library-read semantics.

Mutation:
- existing editor/admin role gates remain.

F5C does not retrofit tenant ownership or infer owner from `created_by`.
Existing projects/history remain unchanged.

A future production-auth change may introduce organization/workspace tenancy explicitly.

## 3. KnowledgeCollection organizes references only

Add `KnowledgeCollection`:
- id
- name
- description nullable
- status `active|archived`
- created_by
- created_at
- updated_at

Add `KnowledgeCollectionItem`:
- id
- collection_id
- item_type `source_document|fact_pack`
- source_document_id nullable
- fact_pack_id nullable
- sort_order
- note nullable
- status `active|detached`
- added_by
- added_at
- detached_at nullable

Constraints:
- exactly one resource FK set;
- item_type must match the populated FK;
- uniqueness per collection/resource;
- archived collection rejects mutation.

Collections do NOT contain copied raw text, Fact rows, FactPack snapshots or Material bytes.

F5C intentionally limits collection membership to SourceDocument and FactPack. Media remains in Material library; ContentMemory remains in the Learning/Identity domain.

## 4. Knowledge Collection is organizational, not evidence authority

KnowledgeCollection is not:
- FactPack;
- Project Fact Boundary;
- DataSnapshot;
- Candidate evidence;
- ContentMemory.

Adding a Source or FactPack to a Collection does not grant public-use permission or freeze evidence.

Project use:
- a Source may be explicitly attached through normal ProjectSourceBinding;
- a frozen FactPack may be explicitly selected/bound through existing Project Fact Boundary flow;
- a Collection itself cannot be bound as Fact Boundary.

If UI offers “use in project”, it must resolve to explicit underlying resource actions and show the resulting scope.

## 5. Material rights projection

Material rights truth comes from MaterialRevision.

Library material summary uses current/latest revision and reports:
- rights_status
- public_use_allowed
- model_use_allowed
- commercial_use_allowed
- attribution presence
- revoked/status state
- source_kind/source_url/provider metadata

Do not infer missing rights as allowed.

Historical revisions remain inspectable.

Revocation continues to use existing Material APIs and downstream stale/block behavior.

## 6. Source rights remain evidence-stage truth

SourceDocument has trust/parse/source metadata but no canonical public-use authorization field.

System Library MUST report Source publication rights as:
`not_decided_at_source_level`

Fact/evidence public/model-use decisions remain in FactPackItem.

Do not add a fake Source `public_use_allowed` merely for UI consistency.

Source detail may show:
- parse state
- as_of
- trust level
- source URL/type
- checksum
- Fact counts/status
- collections
- usage

## 7. FactPack readiness/rights projection

FactPack detail/list summarizes:
- draft/frozen/archived
- version/checksum
- item count
- evidence-kind counts
- public-use allowed/unknown/revoked counts
- model-use allowed/unknown/revoked counts
- source count
- project-bound usage count

A FactPack is not “public-ready” solely because it is frozen.
Rights summary is derived from item snapshots.

Existing immutable/clone/freeze semantics remain authoritative.

## 8. Usage/readback is a bounded projection

Add `services/library_usage.py`.

Material usage MAY include:
- DraftMedia uses
- ProjectMaterialReference
- ProjectWorkflowOutput pointing at MaterialRevision
- Candidate manifest refs where bounded and queryable

Source usage MAY include:
- ProjectSourceBinding
- OpportunitySignal
- Fact counts / FactPack references through Facts

FactPack usage MAY include:
- ProjectFactBoundaryRevision
- legacy TopicBrief refs

Return bounded counts plus recent/deep-link refs.
Do not load full project/candidate histories.

Usage is read-only; it does not create bindings.

## 9. System library API

Recommended router: `routers/system_library.py`

- GET `/system-library`
  - filters: type, q, status, material_kind, source_type, rights, collection_id
  - bounded pagination
- GET `/system-library/summary`
- GET `/system-library/{resource_type}/{resource_id}/usage`

Knowledge:
- GET/POST `/knowledge-collections`
- GET/PATCH/DELETE `/knowledge-collections/{id}` (DELETE = archive)
- GET `/knowledge-collections/{id}/items`
- POST `/knowledge-collections/{id}/items`
- DELETE `/knowledge-collections/{id}/items/{item_id}` (detach/reactivate-safe semantics)

Resource detail continues to use existing `/materials`, `/sources`, `/fact-packs` APIs where practical.

## 10. `/assets` workspace

Replace placeholder with lazy `SystemAssetsKnowledgePage`.

Tabs:
1. 全部
2. 素材
3. 文档与网页
4. Evidence Packs
5. 知识集合

All tab:
- unified metadata cards/list;
- global search;
- type/status filters;
- no heavy content payload.

Material:
- image/video/audio/chart/etc
- preview
- immutable revisions
- rights/provenance
- usage
- upload / AI generation / search actions reuse existing APIs.

Documents & Web:
- SourceDocument import
- parse status
- raw/detail drawer on demand
- extracted Fact summaries
- usage
- archive.

Evidence Packs:
- version/status/checksum
- rights aggregate
- source/evidence count
- deep link to existing FactPack builder/detail.

Knowledge Collections:
- create/archive
- add/detach SourceDocument/FactPack
- ordered items
- no hidden copy.

## 11. Project reuse remains by reference

From system library:
- Material use in Project → existing ProjectMaterialReference against exact MaterialRevision.
- Source use in Project → existing ProjectSourceBinding.
- FactPack use → existing explicit Fact Boundary bind only if frozen/checksum-valid.

No library action silently copies bytes/text or creates a new FactPack.

Project Shared Assets continues to merge explicit project Material refs + workflow-generated material outputs.
System library is broader and cross-project; it does not replace project asset drawer.

## 12. Product Settings information architecture

Refactor `/settings` into:
1. 模型与 AI
2. 数据源
3. 渠道
4. 规则与模板
5. 团队与权限
6. 高级运行环境

The Settings page must distinguish:
- `editable`
- `read_only`
- `unavailable`

No section may imply editability when backend has no durable mutator.

## 13. Models & AI

Reuse:
- `/api/v1/settings`
- model profiles/routes
- LLM override
- image provider settings
- connection tests

Secrets remain masked and never returned in plaintext.

Prompt/provider details stay Advanced where normal users do not need them.

Do not create a second model registry.

## 14. Data Sources settings

Add product settings read model combining:
- FE-F2 Data Source Plugin descriptors
- existing generic Connectors/Endpoints
- plugin availability/reason
- connection mode/capabilities
- configured connector counts/last pull status where relevant

Data Source Plugin registry remains authoritative.

`studio.source` shows executable/internal.
`media.data`, `notion`, `obsidian`, `api`, `sql` show truthful availability/reason.

Existing generic Connector management remains admin-editable.
Do NOT mark a disconnected plugin connected merely because a generic Connector exists unless an explicit mapping contract proves it.

No new connector implementation in F5C.

## 15. Channels settings

Use existing Channel Registry.

Show:
- channel key/label
- supported content forms
- artifact kinds
- workflow keys
- renderer
- rule sets
- discoverability profile
- publisher/capability state where available

F5C Channels section is read-only unless an existing durable mutation API already exists for the exact field.

Do not create a second ChannelProfile table just to make UI editable.

Existing Channel Template/legacy tools may remain deep-linked under Advanced/Rules.

## 16. Rules & Templates settings

Add bounded inventory read model over:
- content-harness Rule Registry descriptors
- domain rules
- ChannelTemplateVersion
- DiscoverabilityProfileVersion where available
- PromptVersion
- BrandVoiceVersion references when relevant

Registry rules are read-only descriptors.
Versioned templates/prompts use existing admin APIs for allowed clone/publish/archive operations.

UI must distinguish deterministic Rule from Prompt/Template.

Do not label Prompt as Rule.

## 17. Team & Permissions settings

Current auth is development Header identity, not production organization tenancy.

Team section truthfully shows:
- current user
- existing User rows/roles
- active state
- current auth mode = development/header

Do not claim:
- invitation workflow
- organization membership
- SSO
- production RBAC administration

unless separately implemented.

Existing `/users` read behavior remains authoritative.
Any role mutation is out of scope unless a current validated API exists.

## 18. Advanced Runtime / Security

Preserve existing advanced settings:
- DB/queue status
- object storage
- SSRF/upload limits
- dsh
- skills/MCP
- raw provider/runtime diagnostics
- app/version

Normal workflow should not require entering these sections.

Dangerous filesystem/local path settings remain admin-only and are clearly labeled local runtime configuration.

## 19. Product settings read APIs

Recommended service: `services/product_settings.py`

Recommended endpoints:
- GET `/settings/product`
- GET `/settings/data-sources`
- GET `/settings/channels`
- GET `/settings/rules`
- GET `/settings/team`

These aggregate existing sources of truth and expose editability/capability metadata.

Existing mutation endpoints remain authoritative:
- `/settings/models`, `/settings/llm`, `/settings/image`, etc.
- `/connectors`
- `/templates/*`

Do not add write wrappers that can diverge from existing persistence unless required for atomic UX.

## 20. Authorization

System library preserves current shared-library V1 semantics:
- authenticated read;
- editor mutation for Source/Material/FactPack/Knowledge collection;
- admin-only infrastructure settings where already required.

Settings:
- non-admin may read safe/masked product settings allowed by existing contracts;
- admin-only mutations remain admin-only;
- secrets never exposed.

Cross-project project attachments still enforce Project ownership.

F5C does not claim tenant isolation for global system library.

## 21. Migration

Add additive reversible migration after `f5b000000001` or actual reconciled head.

Create only:
- `knowledge_collection`
- `knowledge_collection_item`

Do not add owner_user_id to legacy SourceDocument/Material/FactPack in F5C.
Do not rewrite existing rows.
Do not create synthetic collections.

No production migration in this task.

## 22. FE-P1 performance

`/assets` and `/settings` remain lazy route boundaries.

Initial `/assets` must not load:
- ProductionDesigner
- TipTap
- XYFlow
- full raw Source contents
- Material binary bytes
- full FactPack item snapshots

Details/preview load on demand.

Existing `/projects` budget remains green.
Add route budgets for Assets/Settings if existing FE-P1 tooling supports named routes.

## 23. Required tests

Backend:
1. KnowledgeCollection create/read/archive
2. exactly-one-resource FK constraint
3. duplicate item idempotency/reactivation
4. archived collection mutation rejection
5. collection does not copy Source/FactPack data
6. collection cannot bind as Fact Boundary
7. library list bounded/paginated
8. material rights projection reflects unknown/revoked
9. source rights explicitly not-decided-at-source-level
10. FactPack aggregate rights counts
11. usage projection material/source/factpack
12. library action uses Project references, no byte/text copy
13. Data Source Plugin settings matches descriptors
14. disconnected plugin remains unavailable
15. Channel settings mirrors registry without duplicate persistence
16. Rule inventory distinguishes rule vs prompt/template
17. secret masking remains intact
18. admin mutation gates remain intact
19. Team settings truthfully reports development auth
20. F2/F3A/F3B/F4/F5A/F5B regressions green

Frontend/local:
- `/assets` all five tabs
- upload Material, inspect rights/revision
- import Source, inspect parse/facts
- inspect frozen FactPack
- create KnowledgeCollection and add Source/FactPack
- attach Material/Source to Project by reference
- verify FactPack requires explicit Evidence bind
- Settings sections render editable/read-only/unavailable correctly
- Data Source plugin unavailable reasons visible
- Channel/Rule inventory truthful
- no plaintext secrets
- reload persistence
- FE-P1 budgets green

## 24. Rollout sequence

1. migration/models for KnowledgeCollection
2. unified library projection + usage
3. KnowledgeCollection APIs
4. project reuse actions/deep links
5. `/assets` frontend
6. product Settings read models
7. Settings frontend restructure
8. targeted/full tests + bundle checks + isolated browser
9. independent review
10. canonical spec sync/archive only after explicit authorization
