## Context

Current project code has:
- `ContentPersona(id, owner_user_id, name, created_at)` as the only content-identity entity.
- `PersonaWorkflowDefault(persona_id, modality, workflow_id, revision)` implemented and already used by FE-F2.
- `BrandVoiceVersion` as an immutable/versioned voice primitive used by legacy Topic generation.
- No Brand entity, Account entity, Series/Column entity, IdentitySnapshot, Content Memory domain, or LearningCandidate.
- `ContentUnit` pins `persona_id`, modality, channel, workflow version, and FE-F2/F3A history.
- `WorkflowRun` freezes workflow version/checksum but not content identity.
- FE-F3A Versions explicitly reports no fabricated IdentitySnapshot.
- Historical Topic/ContentAsset records may reference BrandVoiceVersion, but there is no evidence that they used the future hierarchy.

The Frontend Product Contract requires `Workspace → Brand → Persona/Role → Account → Series/Column`, identity detail tabs, Persona × Modality defaults with lower-level overrides, and identity as a horizontal axis across planning, production and approval.

## Goals / Non-Goals

**Goals**
- Durable Brand/Persona/Account/Series hierarchy.
- Append-only identity revisions with optimistic concurrency.
- Deterministic server-side inheritance.
- Reuse BrandVoiceVersion instead of a duplicate voice system.
- Immutable IdentitySnapshot pinned to new production.
- Account/Series workflow-default inheritance over existing Persona defaults.
- A real `/identities` workspace with current/effective/revision views.
- Preserve FE-F2/F3A history and archive safety.
- Make legacy identity absence explicit rather than fabricated.

**Non-Goals**
- New Workspace/Organization tenancy model.
- Automatic performance learning.
- LearningCandidate or automatic Content Memory mutation.
- Opportunity, Review Center, new publishers, new connectors.
- Full production-grade organization auth.
- Rewriting TopicBrief or historical ContentAsset to the new hierarchy.
- Replacing BrandVoiceVersion.

## Decisions

### 1. Keep ContentPersona as the Persona stable entity

Do not introduce `IdentityPersona` or another parallel Persona table.

Extend `content_persona` additively:
- `brand_id nullable`
- `status active|archived` with default `active`

Existing rows remain valid with `brand_id = null`. A legacy Persona does not receive an invented Brand assignment during migration.
The existing brandless `POST /content-personas` route remains compatible. A new brand-scoped route may create a Persona with an explicit Brand ID; neither route silently assigns a Brand to historical rows. Stable parent links are immutable after creation, so a later hierarchy edit cannot reinterpret old snapshots.

### 2. Separate stable identity entities from append-only revisions

Stable entities:
- `ContentBrand`
- existing `ContentPersona`
- `ContentAccount`
- `ContentSeries`

Append-only profile rows:
- `ContentBrandRevision`
- `ContentPersonaRevision`
- `ContentAccountRevision`
- `ContentSeriesRevision`

Stable rows contain name, hierarchy relation, lifecycle status and timestamps. Profile rows contain only identity configuration/version state.

Do not update an old revision. Save creates revision N+1 using an `expected_revision` precondition. Concurrent same-revision saves are protected by `(entity_id, revision_no)` uniqueness and converted to HTTP 409.

Current revision is derived as highest committed revision number. Do not add mutable “current profile JSON” to stable entity rows.

### 3. Use one typed override profile contract

Implement Pydantic/server validation in a dedicated identity service/schema.

Supported canonical profile fields:
- `positioning`
- `target_audience`
- `content_domains`
- `expression_style`
- `visual_language`
- `long_term_views`
- `value_propositions`
- `content_boundaries`
- `risk_boundaries`
- `public_fact_policy`
- `brand_voice_version_id`

Recommended value shapes:
- positioning: string | null
- target_audience: list[str] | null
- content_domains: list[str] | null
- expression_style: dict | null
- visual_language: dict | null
- long_term_views: list[dict] | list[str] | null
- value_propositions: list[str] | null
- content_boundaries: list[str] | null
- risk_boundaries: list[str] | null
- public_fact_policy: dict | null
- brand_voice_version_id: int | null

Persist only keys explicitly authored at that hierarchy level. Missing keys are meaningful and must not be auto-filled. Unknown fields return 422.

### 4. Deterministic inheritance, not prompt-side merging

Resolution order: `Brand → Persona → Account → Series`.

Per field:
- missing key = inherit current accumulated value
- present non-null value = override
- present null = clear inherited value
- arrays/objects = replace the entire inherited value
- never implicit-deep-merge arbitrary JSON

The resolver returns both:
- `effective_profile`
- `field_origins`, e.g. `{"target_audience":"account","visual_language":"brand"}`

The frontend uses `field_origins` to label inherited vs overridden values.

### 5. Reuse BrandVoiceVersion

`BrandVoiceVersion` remains the only voice-version entity.

The current `BrandVoiceVersion` table has no owner column: published versions are existing global resources, not owner-scoped assets. FE-F3B therefore does not invent a user-ownership check for this table. If a profile explicitly provides `brand_voice_version_id`:
- referenced row must exist
- it must be `published` before a new IdentitySnapshot can use it
- an archived/draft voice is rejected for a new revision or snapshot; historical snapshots keep their frozen reference

The effective profile resolves the nearest explicit BrandVoice reference.

Do not rewrite `TopicBrief.brand_voice_version_id`. Do not backfill historical Topic/ContentAsset into new snapshots.

### 6. IdentitySnapshot freezes the production identity

`IdentitySnapshot` stores:
- owner_user_id
- brand_id / brand_revision_id nullable
- persona_id / persona_revision_id nullable
- account_id / account_revision_id nullable
- series_id / series_revision_id nullable
- brand_voice_version_id nullable
- `effective_profile_json`
- `field_origins_json`
- checksum
- created_by / created_at

Snapshot is immutable. Checksum canonicalization includes all referenced revision IDs and effective identity data.

A new or explicitly rebound ContentUnit after FE-F3B pins an IdentitySnapshot. A WorkflowRun created from a ContentUnit copies the unit's exact `identity_snapshot_id`. The run never resolves “latest identity” at read time.
For a legacy brandless Persona with no profile revision, an explicit new binding still creates a truthful snapshot with the existing Persona ID, null absent revision IDs, and an empty effective profile. The UI must label this as incomplete identity; it must not infer a Brand or authored positioning. A legacy unit is not silently rebound.

### 7. Historical honesty

Migration MUST NOT generate IdentitySnapshots for existing ContentUnits or WorkflowRuns.

Historical records remain `identity_snapshot_id = null`.

API/UI semantics:
- null snapshot + existing historical content = `legacy_identity`
- display `Legacy / 未冻结身份`
- no claim about Brand/Account/Series/version beyond what old records actually contain

A user may explicitly rebind an active ContentUnit to current identity. That operation creates a real snapshot at that moment and follows safe lifecycle rules.

### 8. Extend ContentUnit identity path

Add nullable:
- `account_id`
- `series_id`
- `identity_snapshot_id`

Hierarchy validation:
- Account must belong to selected Persona.
- Series must belong to selected Account.
- Persona brand relationship must match selected Brand when Brand context exists.
- All hierarchy objects must belong to current owner.
- Request path/IDs never grant ownership.

A ContentUnit always retains `persona_id` as the stable minimum identity axis. Account/Series are optional.
On identity rebind, omitted Account/Series means keep the existing selection only if it still belongs to the selected parent; otherwise reject with 422 and require an explicit null or replacement ID. Do not silently drop a child scope when a parent changes. An explicit Series requires its Account in the resolved selection.
Creating a new unit, explicitly rebinding one, saving a scoped default, or starting a new run rejects archived entities anywhere in the selected hierarchy. Reading existing units, snapshots and runs remains allowed. A title/channel-only edit does not refresh identity.

### 9. Reuse FE-F2/F3A safe rebind semantics

No execution history means no Run, DataSnapshot, or ProjectWorkflowOutput for the unit.

Before history:
- identity rebind may happen in place
- create a fresh IdentitySnapshot
- update persona/account/series/snapshot
- resolve and pin selected workflow
- incompatible project override may be detached according to existing FE-F2 rules

After history:
- create replacement ContentUnit
- archive old ContentUnit
- old unit keeps old IdentitySnapshot and runs
- replacement gets new IdentitySnapshot/workflow pin
- no historical row is rewritten

Title/channel-only edits retain existing semantics.

### 10. Add Account/Series workflow-default bindings

Keep `PersonaWorkflowDefault`.

Add:
- `AccountWorkflowDefault(account_id, modality, workflow_id, revision)`
- `SeriesWorkflowDefault(series_id, modality, workflow_id, revision)`

Resolution: `Series > Account > Persona`.

Default resolution returns workflow ID/version/checksum, source scope `series|account|persona|unbound`, and binding revision.

Save-as-default:
- explicit target scope
- immutable Workflow new version
- FE-F2 definition validation
- FE-F2 portability gate
- optimistic binding revision
- authorization through hierarchy ownership
- does not mutate sibling scopes
- never rebinds old units automatically

Use workflow keys:
- existing `persona.{persona_id}.{modality}`
- `account.{account_id}.{modality}`
- `series.{series_id}.{modality}`
Extend the shared FE-F2 workflow authorization and legacy raw Workflow API guards for `account_default` and `series_default` scopes. A scoped workflow remains owned by its creator and is visible for a unit only through an authorized same-owner hierarchy. Do not treat a raw Workflow ID or key string as authorization.

### 11. Archive instead of destructive deletion

Brand/Persona/Account/Series referenced by ContentUnit, IdentitySnapshot, Workflow preference, or historical production must remain readable.

DELETE endpoints archive stable entities. Archived entity revisions and snapshots remain readable. New child creation/revision/default saves under an archived ancestor are rejected. No cascading physical delete of historical identity.

### 12. Identity Workspace

Replace `/identities` placeholder.

Suggested frontend modules under `apps/web/src/product/identity/`:
- `IdentityWorkspacePage.tsx`
- `IdentityTree.tsx`
- `IdentityDetailPage.tsx`
- `IdentityProfileTab.tsx`
- `IdentityExpressionTab.tsx`
- `IdentityBoundariesTab.tsx`
- `IdentityAccountsSeriesTab.tsx`
- `IdentityWorkflowPreferencesTab.tsx`
- `IdentityMemoryTab.tsx`
- `IdentityRevisionHistory.tsx`
- `IdentityEffectiveProfile.tsx`

Detail tabs:
1. 身份
2. 表达与视觉
3. 观点与边界
4. 账号与栏目
5. 工作流偏好
6. 内容记忆

Tabs 1–5 use real persistence.

Tab 6 is truthful boundary/projection only in FE-F3B:
- may show historically linked published/approved content if reliable links exist
- must not synthesize “learned strategy”
- explicitly states automatic learning belongs to F5

### 13. Production integration

Production Workspace Context Header displays Brand, Persona, Account if any, Series if any, and frozen snapshot state/checksum/version summary.

Add `本内容使用的身份快照` read-only inspector.

Run mode reads `run.identity_snapshot_id`. Design/configuration mode may show current available identity but never silently updates the unit. Changing identity requires explicit rebind action.

### 14. FE-F3A integration

Versions:
- add real IdentitySnapshot entries linked to project units/runs
- legacy units with no snapshot show `legacy_identity`, not fake snapshot records

Overview:
- active units with missing usable IdentitySnapshot after FE-F3B adoption produce typed `identity_unready` risk
- legacy historical archived units must not block current project readiness
- stage rules remain backend deterministic

CreativeBrief:
- `identity_scope_json` may contain stable identity references
- validate ownership/hierarchy when a new Brief revision uses typed refs; preserve legacy untyped strings as historical descriptive labels without treating them as IDs
- historical Brief revisions remain unchanged

Activity:
- unit rebind/replacement events may include old/new snapshot IDs in structured payload
- identity-global revision history is represented by revision rows/AuditLog, not duplicate ProjectEvent for unrelated projects

### 15. API surface

Recommended new router: `routers/content_identities.py`, prefix `/api/v1`.

Brand:
- GET `/content-brands`
- POST `/content-brands`
- GET `/content-brands/{brand_id}`
- PATCH `/content-brands/{brand_id}` for stable metadata such as name only
- DELETE `/content-brands/{brand_id}` => archive
- GET `/content-brands/{brand_id}/revisions`
- GET `/content-brands/{brand_id}/revisions/{revision_id}`
- POST `/content-brands/{brand_id}/revisions`

Persona:
- existing GET/POST persona endpoints remain compatibility routes
- GET `/content-personas/{persona_id}`
- PATCH stable name if authorized
- DELETE => archive
- GET `/content-personas/{persona_id}/revisions`
- GET `/content-personas/{persona_id}/revisions/{revision_id}`
- POST `/content-personas/{persona_id}/revisions`
- GET/POST `/content-brands/{brand_id}/personas`

Account:
- GET/POST `/content-personas/{persona_id}/accounts`
- GET/PATCH/DELETE `/content-accounts/{account_id}`
- GET `/content-accounts/{account_id}/revisions`
- GET `/content-accounts/{account_id}/revisions/{revision_id}`
- POST `/content-accounts/{account_id}/revisions`

Series:
- GET/POST `/content-accounts/{account_id}/series`
- GET/PATCH/DELETE `/content-series/{series_id}`
- GET `/content-series/{series_id}/revisions`
- GET `/content-series/{series_id}/revisions/{revision_id}`
- POST `/content-series/{series_id}/revisions`

Resolution:
- GET `/content-identities/effective?persona_id=&account_id=&series_id=`
- GET `/identity-snapshots/{snapshot_id}`

Workflow defaults:
- GET/POST `/content-accounts/{account_id}/default-workflows/{modality}`
- GET/POST `/content-series/{series_id}/default-workflows/{modality}`
- expose an effective-default read returning source scope

ContentUnit:
extend existing project unit create/patch/rebind payloads with `account_id`, `series_id`, and explicit `rebind_identity`.

Do not accept arbitrary client-created IdentitySnapshot IDs as a way to bypass hierarchy checks. Server resolves/creates the snapshot for normal rebind/create flows.

### 16. Services

Add `services/content_identity.py`:
- canonical identity schema validation
- hierarchy authorization
- current revision loading
- inheritance resolution
- BrandVoice validation
- snapshot checksum/build
- create snapshot
- unit identity binding helpers

Add/extend `services/identity_workflows.py` or existing project workflow service:
- effective default resolution Series > Account > Persona
- Account/Series default save with FE-F2 portability/validation
- no duplicate workflow validator

Extend:
- `services/project_versions.py`
- `services/project_overview.py`
- workflow start logic
- project/unit APIs
- production serialization

Avoid circular imports by keeping identity core service independent of routers.

### 17. Migration plan

Create additive migration after `f3a000000001`.

Create tables:
- content_brand
- content_brand_revision
- content_persona_revision
- content_account
- content_account_revision
- content_series
- content_series_revision
- identity_snapshot
- account_workflow_default
- series_workflow_default

Alter:
- content_persona: brand_id nullable, status
- content_unit: account_id nullable, series_id nullable, identity_snapshot_id nullable
- workflow_run: identity_snapshot_id nullable

Constraints:
- unique `(brand_id, revision_no)`
- unique `(persona_id, revision_no)`
- unique `(account_id, revision_no)`
- unique `(series_id, revision_no)`
- unique `(account_id, modality)`
- unique `(series_id, modality)`
- ownership lookup indexes

Migration MUST preserve all current FE-F3A/FE-F2 rows. No synthetic snapshots. No synthetic Brand rows.

Validate isolated SQLite up/down/up and PostgreSQL-compatible DDL patterns.

### 18. Security and authorization

All new identity routes use persisted owner hierarchy. Do not trust brand_id, persona/account/series combinations, raw workflow_id, or snapshot_id from the client as proof of access.

Cross-owner objects return 404/no disclosure where consistent with project authorization. A snapshot is readable only by its owner or through an authorized project/unit context. Archived identities are readable but reject mutation/new children/new defaults.

### 19. Test plan

Targeted backend tests must include:
1. hierarchy ownership and parent-child validation
2. cross-owner IDs rejected
3. revision append-only behavior
4. stale expected_revision 409
5. database race uniqueness converts to 409
6. missing-key inherit semantics
7. explicit-null clear semantics
8. arrays/objects replace semantics
9. field-origin reporting
10. BrandVoice inheritance/override and invalid voice rejection
11. immutable snapshot/checksum
12. existing historical unit/run stays null snapshot
13. new unit gets real snapshot
14. run copies exact unit snapshot
15. Persona revision advance does not change old unit/run
16. pre-history identity rebind updates in place
17. post-history rebind replaces unit + archives old
18. archived identity read-only
19. Series default beats Account; Account beats Persona
20. Account/Series default save uses portability gate
21. new defaults do not silently rebind units
22. cross-owner raw workflow cannot become scoped default
23. Versions reports snapshot/legacy truthfully
24. Overview reports identity readiness deterministically
25. Brief identity scope validation preserves old revisions
26. FE-F2/F3A project/run/stale/output regressions remain green

Frontend/local acceptance:
- create Brand→Persona→Account→Series
- create revisions at each level
- inspect inherited/overridden/cleared fields
- reload all identity routes
- select BrandVoice
- configure Persona/Account/Series workflow defaults
- create ContentUnit and verify resolved workflow + IdentitySnapshot
- change Persona revision and verify old unit still shows frozen snapshot
- explicit rebind before and after history
- historical legacy unit clearly shows legacy/unknown
- `/identities` tabs persist and reload

### 20. Rollout sequence

1. migration/models + hierarchy authorization
2. revision service + inheritance resolver
3. IdentitySnapshot + ContentUnit/Run pinning
4. Account/Series workflow defaults
5. unit create/rebind integration
6. project Versions/Overview/Brief integration
7. Identity Workspace frontend
8. Production context/snapshot inspector
9. targeted regression and isolated DB/browser acceptance
10. independent review before archive

## Risks / Trade-offs

- Identity hierarchy becoming a generic configuration tree → keep explicit Brand/Persona/Account/Series tables and typed profile contract.
- Silent historical drift → snapshots pin resolved identity and old null remains legacy.
- Duplicate Voice systems → reuse BrandVoiceVersion.
- Defaults silently changing production → resolve/pin at unit bind; defaults never auto-rebind.
- JSON inheritance ambiguity → strict missing/value/null/replace semantics.
- Archive trees becoming inconsistent → reject child mutation when an ancestor is archived.
- Legacy Topic path divergence → preserve it; migration to project identity is explicit, not retroactive.
- Identity Memory scope creep → FE-F3B only establishes boundary; F5 owns learning/promotion.
