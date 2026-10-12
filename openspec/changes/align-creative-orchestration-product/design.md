## Context

AIContentStudio is a single-machine production application using SQLite, local immutable media and loopback-only API/Web. Current implementation already provides the difficult business truth: Project/Identity/Brief/Fact Boundary, append-only Text/Graphic/Video Masters, exact MaterialRevision references, ChannelVariant v5, Candidate v3/v4/v5, Review/Approval, Delivery/Receipt, native ProviderGenerationTask with Unknown/no-auto-retry semantics, and evidence-backed Learning/Memory.

The remaining gap is product orchestration. The main navigation still exposes a legacy section; `/production` is a placeholder rather than a current-work queue; System Assets links to legacy Materials/Sources/FactPack pages for several writes; Project Evidence still deep-links to legacy fact extraction/FactPack editing; Product Settings retains legacy administration; and Video Studio has a deeper NLE-shaped surface than the product now intends to compete on.

The approved North Star is:

> AIContentStudio owns content, creative decisions, provenance and acceptance. It performs simple/high-frequency generation directly, delegates complex/high-quality execution to replaceable Agents/professional tools through MCP, accepts results back into existing immutable truth, and explicitly preserves reusable methods so the system becomes easier and more personalized with use.

This is a reframe of product emphasis, not a rewrite of historical data.

## Goals / Non-Goals

**Goals**

- One coherent daily product surface without losing still-used legacy actions or historical reads.
- Persist creative intent together with content revisions.
- A media-agnostic Creative Execution contract for complex work, with a first Director Package schema for video.
- Same-machine MCP handoff for Codex/Claude/other Agents with exact context/input/output provenance.
- Explicit staged-result acceptance into the existing MaterialRevision library.
- Checkpoint/recovery/Unknown semantics that make side-effecting Agent work recoverable without blind retries.
- Versioned Capability Memory that can retain high-quality methods and user preferences through explicit promotion.
- Content-first Production UI and a director-first Video experience, while keeping old Video v1/v2/Candidate history compatible.
- Preserve current single-machine production simplicity.

**Non-Goals**

- Replacing Premiere, Resolve, After Effects, Photoshop, a DAW or other professional editors.
- A generic remote Agent platform, multi-user job marketplace or cloud orchestration service.
- Executing arbitrary Capability Memory code inside the AIContentStudio backend in the first version.
- Replacing ProviderGenerationTask for ordinary native image/video/TTS generation.
- Automatically changing Identity, facts, Workflow defaults, Channel strategy, Master/Variant content or approved Candidates from learned preferences.
- Treating execution completion, local ZIP, draft-box creation or MCP success as public publication.
- Deleting historical legacy data or force-migrating old v1/v2/v3/v4/v5 rows.
- Serverization, PostgreSQL/MinIO/JWT/multi-host work.

## Decisions

### 1. The product boundary is “define, execute appropriately, accept,” not “own every editor”

AIContentStudio SHALL own the business truth needed to create content: Identity, Brief, facts/evidence, source content, creative intent, exact assets, target form, channel expression, approval and publication/learning facts.

A task stays native when it is high-frequency, bounded and maintainable: text generation/rewrite, ordinary image generation, basic TTS/ASR, subtitle suggestions and other existing provider tasks. A task moves to Creative Execution when quality/control requirements would otherwise grow AIContentStudio into a professional editor.

No media type is permanently “internal” or “external.” Complexity and control determine the route.

### 2. Existing native generation and new professional execution are separate truths

`ProviderGenerationTask` remains authoritative for current model/media generation with its durable one-send receipt, result staging, explicit acceptance and accepted MaterialRevision. It SHALL NOT be migrated into or relabeled as CreativeExecution.

`CreativeExecution` represents a different operation: an exact creative package handed to an external/local Agent or professional-tool workflow. UI MAY project native generation and external execution together as “Create & Execute,” but write paths and idempotency stay schema-specific.

Both paths converge only at accepted immutable `MaterialRevision` and later explicit Master/Variant saves.

### 3. Creative intent is versioned with content instead of creating a parallel content tree

Add optional bounded `creative_intent_json` and server-derived `creative_intent_hash` to ContentMasterRevision and ChannelVariantRevision.

The structure is typed/versioned and MAY include:

- objective / why-now;
- audience;
- must_keep;
- must_avoid;
- creative_freedom;
- narrative/visual/audio intent;
- rationale entries keyed to stable content/scene/slot IDs;
- human-confirmed decisions.

It SHALL NOT duplicate FactPack facts, Identity profile fields, full source bodies, secrets or raw model output. A content revision without creative intent remains valid legacy/current content; no historical backfill is invented.

Changing creative intent requires a new Master/Variant revision through its existing save/CAS path and changes the source's canonical intent hash. It never mutates an old revision.

### 4. CreativeExecutionPackage is immutable and source-bound

A package freezes exactly one supported current source:

- ContentMasterRevision; or
- ChannelVariantRevision.

The package stores project/unit/owner, source kind/id/hash/context/intent hash, exact Identity/Brief/Fact Boundary refs available through the source, target medium/channel/form when relevant, exact asset/evidence refs, requirements, output contract, acceptance criteria, package schema/version and a server-derived package hash.

The frozen output contract defines each output role with a stable `role_id`, `kind`, `required` flag, allowed MIME types, minimum/maximum count and maximum bytes. `required=true` SHALL have `min_count >= 1`; `required=false` SHALL have `min_count=0`; and `max_count >= min_count`. Required roles are part of the package hash and cannot be waived by an acceptance form; a changed output contract requires a new package/execution. An exact count uses `min_count=max_count`.

A package is not a Candidate, DeliveryTarget, WorkflowRun or approval state. Creating it makes no provider/professional-tool call.

First schemas:

- `creative.execution.v1` — generic bounded package;
- `director.video.v1` — video-specific package derived from current Video Master information and creative intent.

`director.video.v1` includes script blocks, scenes/shots, narration/voice intent, subtitles/overlay intent, B-roll/search requirements, selected exact assets, pacing/transition intent, target duration/aspect ratio, must-keep/must-avoid and expected outputs. Existing Video v2 timeline may be included as optional advanced guidance, not as a requirement that AIContentStudio continue evolving into an NLE.

### 5. Director-first Video reuses F6D instead of replacing it

Existing `video.master.v1/v2`, exact refs, render-input binding, manual attestation, Candidate v4, Review and packages remain readable and valid.

The new daily path can prepare a `director.video.v1` package from a current valid Video Master even when no final render is yet bound. The external execution output, once explicitly accepted as MaterialRevision, still does not mutate the Master. The editor explicitly binds the accepted final render and saves a new Video Master revision; existing F6D readiness/Candidate v4 gates then apply unchanged.

Thus F6D becomes the compatibility and final-integrity foundation while product investment shifts from internal timeline/NLE features to script/directing/execution orchestration.

### 6. CreativeExecution is a durable one-dispatch state machine

Add `CreativeExecution` with a stable id, owner/project/unit/package, idempotency key, request fingerprint, executor kind/key/version, state/revision, dispatch certainty, current checkpoint/recovery metadata, safe reason code and timestamps.

First states:

`prepared | claimed | in_progress | failed_before_dispatch | blocked | unknown | result_ready | accepted | rejected | cancelled | superseded`

Rules:

- identical owner/idempotency retry returns the same execution;
- changed request with same key returns 409;
- archived project/unit rejects new execution;
- only a current package/source may claim or start a side-effecting execution;
- stale or historical packages remain readable for inspection/comparison only; re-execution requires a new package built from the current Master/Variant;
- no automatic retry after `claimed/in_progress/unknown` when dispatch may have occurred;
- `accepted` requires accepted output slots for every required role in the frozen output contract, with accepted distinct `output_index` count at least `min_count`; optional roles do not block acceptance. First version requires file output for media execution and does not support waiving a required role.

### 7. Outputs are staged before MaterialRevision

`CreativeExecutionOutput` stores a bounded result role/kind, stable positive `output_index`, monotonic `attempt_no`, staging storage key, MIME, size, hash, safe tool/agent metadata, optional external project-file descriptor and acceptance state. A role may have multiple immutable output rows. A replacement for a rejected slot reuses the same `output_index` with a higher `attempt_no`; the old row remains readable and is never overwritten. Submission validates the output against the matching frozen contract role, including allowed MIME, count and byte limits.

Submission validates execution scope and writes/copies only into a private execution staging root. No arbitrary absolute caller path is accepted. Output must be a regular file inside that execution work root, within configured size/count limits, and is hashed/sniffed before it can satisfy a required role. For each role, valid staged count is the number of distinct output indexes whose latest eligible attempt is valid and not rejected; it MUST be at least `min_count` and MUST NOT exceed `max_count`. The execution reaches `result_ready` only after every required role meets that count; incomplete submissions remain in progress or blocked.

Explicit human acceptance rechecks the output and rights/license decision and then creates one immutable MaterialRevision with `source_kind=external_execution` provenance and a link back to execution/package/output. Project visibility may be added explicitly in the same accepted result flow if requested and authorized. The accepted output rights MUST NOT exceed the rights supported by every exact MaterialRevision input materialized for this execution; required attribution/license obligations remain attached, and revoked or unprovable input rights block public/model/commercial escalation.

If a required output is rejected, the execution does not become terminal `rejected`; it returns to `blocked` with safe reason `needs_output_replacement`. A new immutable output attempt for the same role/index may be submitted within the same execution, after which the execution can return to `result_ready`. Rejected output rows remain historical. Optional-output rejection does not block completion. Only an explicit user rejection of the whole execution enters terminal `rejected`, and terminal `accepted/rejected/cancelled/superseded` executions accept no new outputs.

Acceptance does NOT:

- save a Master/Variant;
- bind a render;
- freeze a Candidate;
- approve content;
- authorize delivery;
- mark publication.

Those remain existing explicit actions.

### 8. The execution work directory is the only filesystem bridge

For same-machine Agents/professional tools, AIContentStudio creates a private execution work root under a configured local state directory.

MCP tool `materialize_inputs` copies or safely materializes only exact authorized package assets to that root after live hash/rights/model-use checks appropriate to the requested execution. It returns bounded local paths and hashes.

Output submission accepts only files rooted under the same execution directory. It rejects symlink/path escape, special files, unexpected MIME/size/count, changed input package/source, or an execution that is not writable.

This allows Codex/Claude to hand files to local tools without exposing the whole media library or arbitrary filesystem.

### 9. AIContentStudio MCP is a local interface, not a second truth source

The same FastAPI process exposes a loopback-only Streamable HTTP MCP endpoint. It does not reuse the existing Settings list of external MCP servers as its truth.

Use a dedicated local bearer secret from ignored runtime configuration plus an explicit existing local owner-user ID. The secret is never serialized, logged or stored in SystemSetting. The MCP endpoint refuses non-loopback clients and resolves every project/entity access through existing authorization.

First read resources/tools provide:

- project/unit context;
- Identity/Brief/current Fact Boundary summaries;
- current Master/Variant metadata and creative intent;
- Creative Execution Package;
- exact input manifest;
- saved/pinned applicable Capability Memory;
- execution state.

First mutation tools provide:

- claim/start an already prepared execution;
- materialize exact inputs;
- report progress/blocker/checkpoint;
- submit bounded output;
- mark/reconcile unknown;
- request human review.

MCP MUST NOT expose:

- arbitrary SQL;
- arbitrary filesystem reads;
- plaintext secrets;
- raw provider errors;
- automatic Content Approval;
- automatic Delivery Authorization/publication;
- direct mutation of Master/Variant payloads.

### 10. Checkpoint/recover is an interoperability contract

An executor descriptor declares whether checkpoint, revert and recover are supported. AIContentStudio stores only safe bounded references/evidence to external checkpoints; the professional tool owns the actual project state.

Before risky execution, an Agent MAY report a checkpoint. On failure:

- `failed_before_dispatch` is a terminal state that proves dispatch did not occur; retry creates a new execution with a new idempotency key and an explicit `retry_of` reference, while the failed execution remains immutable;
- `blocked` means no ambiguous side effect is pending;
- `unknown` means the system cannot prove resulting professional state and MUST NOT auto-retry;
- recovery/revert/continue require explicit Agent/user action plus current-state observation.

A reconciliation records observation hash/summary and the chosen resolution. This mirrors Delivery/Provider Unknown semantics and prevents repeated destructive edits.

### 11. Capability Memory stores reusable methods, not business facts

Add `CapabilityArtifact` root plus append-only `CapabilityArtifactRevision`.

Kinds:

- `prompt_skill`;
- `recipe`;
- `creative_pattern`;
- `preference`;
- `execution_template`;
- `tool` (externally executed/rendered definition only in v1).

Statuses:

- `candidate`;
- `saved`;
- `pinned`;
- `archived`;
- `deprecated`.

A revision stores bounded content/schema, content hash, scope, source provenance, source execution/learning references, created actor/time and safe metadata. Candidate content is not authoritative configuration.

Installed Agent Skills discovered from configured local skill directories are a separate external capability inventory. They are not Capability Memory artifacts: v1 does not automatically import, export, install, enable, overwrite or promote them. If both inventories are shown together, each item carries a distinct `source_kind` and stable identity; equal names never imply equivalence or replacement. Capability promotion never changes the existing `skills_enabled` setting.

Artifact content and argument schemas are rejected as a whole when they contain secret-like values, signed/credential URLs or other unsafe payloads. Only allowlisted provenance or diagnostic metadata outside the artifact may be omitted before persistence; the successful source execution result is never rewritten because capability capture failed.

No Capability Memory artifact may contain a Fact as a substitute for FactPack, alter Identity, or bypass evidence/rights.

### 12. Capture may be automatic; promotion is always explicit

The system MAY propose a `candidate` when:

- a deterministic external execution completed successfully and the Agent supplied a bounded reusable recipe/tool/template; or
- a CreativeExecution reached top-level `accepted` only after every required output role met its frozen minimum count and each required slot was accepted, and reusable prompt/pattern metadata was supplied; or
- validated Learning explicitly proposes a method/pattern candidate.

The candidate defaults to the narrowest safe scope derived from its source. It is hidden from ordinary default discovery until promoted. Duplicate same-kind/content-hash/scope candidates are refreshed/deduplicated rather than multiplied.

Only an authorized human action promotes to saved/pinned or broadens scope. A single successful run, use count or model suggestion can never auto-promote.

### 13. Capability Memory is scoped to avoid preference pollution

Supported scope is bounded and explicit:

`owner | persona | account | series | project | channel | executor`

Applicable discovery returns every applicable saved/pinned revision with exact scope metadata. The system MUST NOT silently merge, override or choose a winner when multiple scopes or artifacts conflict. The caller must explicitly select the applicable revision; stable UI ordering is presentation only and is not automatic precedence.

A project-specific prompt cannot silently become Persona/global behavior. Promotion to a broader scope is a separate confirmation.

Facts/evidence are never inferred from capability scope.

### 14. Capability use is observable but popularity is not truth

A `CapabilityUse` record binds exact artifact revision, requesting actor/project/execution context, rendered argument hash, use time and an optional later outcome (`used | accepted | rejected | unknown`).

Use count/last-used may support ranking or UI suggestions. They MUST NOT:

- change artifact content;
- auto-promote;
- mark quality verified;
- change Identity/Workflow/channel rules;
- alter facts.

First version renders stored prompt/recipe/template/tool content to the Agent. AIContentStudio does not execute arbitrary CapabilityArtifact code.

### 15. Learning and Capability Memory are separate, connected by explicit promotion

Content Learning continues to answer “what content strategy may work?” using published/performance evidence. Capability Memory answers “how do we reliably perform this creative task?”

An accepted LearningCandidate may explicitly propose a Capability Memory candidate with frozen source evidence. It cannot directly update a saved capability. Conversely, capability usage evidence may be cited by Learning but does not count as publication-performance evidence.

ContentMemory remains long-term learned content context; CapabilityArtifact is reusable execution/creative method context.

### 16. One daily product surface; legacy parity precedes retirement

Main daily routes remain Home, Opportunities, Projects, Creation/Execution, Review/Delivery, Identities, Assets/Knowledge, Learning, Settings.

Required UX changes:

- `/` enters `/home`, not legacy dashboard.
- `/production` becomes a real current-work/creative-execution queue rather than a placeholder.
- Project remains the primary container and gains a coherent Content/Execution path without forcing users to understand internal F6/F7 names.
- System Assets supports ordinary Material upload/native generation/search, Source text/URL/file import, fact extraction/review/edit, FactPack create/clone/add/remove/freeze and project reuse without requiring legacy navigation.
- Settings supports normal Connector actions, template/rule management and explicit advanced local-runtime tooling without a permanent “go to legacy settings” dependency.
- Review/Delivery stays based on FE-F4 Candidate/Approval/Delivery truth.

For every legacy route/action, maintain a documented parity inventory with: legacy operation, authoritative data/API, new surface, historical behavior, regression, retirement state.

A legacy menu item may exit daily navigation only after all still-supported writes have a new path and E2E coverage. Compatibility deep links MAY remain. Removing React pages is a final cleanup, never the migration mechanism.

### 17. Production workspace becomes content-first

Per-unit Production shows current content, creative intent, assets, channel variants and active native/external execution first.

Workflow Mini Canvas/Node Inspector remain available under an Advanced/Automation surface and keep all existing persistence and run semantics. Hiding workflow controls does not change WorkflowRun truth.

Channel Variant editing remains append-only through the existing F6E service. Editing one target does not mutate source Master or sibling variants.

### 18. Single-machine production remains unchanged

This change uses current SQLite/local-media/loopback operation. The MCP is local-only and reuses the same process. New local state directories are private and recoverable.

No JWT, PostgreSQL, MinIO, container, reverse proxy, remote agent service or multi-host execution is required.

Backup/recovery must include the new execution/capability tables and any accepted MaterialRevision bytes. Temporary execution staging is not authoritative after outputs are accepted or intentionally discarded.

### 19. Post-enable schema lifecycle correction and retained regressions (2026-10-05)

The separately authorized formal enablement advanced the local SQLite through
`f7d000000001 -> f8a000000001 -> aco000000001`. The current local approved schema
and default readiness target are now `aco000000001`; the earlier F8 `f7d` restore
and no-identity-column acceptance remain historical evidence, not the current target.
The nullable User issuer/subject columns exist only as migration ancestry and
remain null/inert in the current formal database. Schema presence does not enable
or accept JWT/production authentication. Keep development_header, SQLite, local
media, loopback services, credentials and the existing Worker topology unchanged.
Do not downgrade or roll back the live database to reconcile stale documentation.

Closeout MUST retain isolated repository regressions for CreativeExecution
stale/Unknown/multi-output replacement/derived rights, MCP loopback/auth/tool
restrictions, Capability lifecycle/scope/secrets/Installed Skills separation, and
ACO upgrade/history/downgrade guards plus the inert identity ancestry. These tests
use disposable databases/media only, never the formal SQLite or real providers.
This targeted review authorizes the corresponding F8 schema/readiness and recovery
documentation corrections only; unrelated F8-owned edits remain preserved.

## Risks / Trade-offs

- **Large cross-cutting product change** → implement in gated phases; legacy routes remain until operation parity is proven.
- **Capability Memory can become junk** → candidates are hidden/non-authoritative, deduplicated and require explicit promotion; broader scope requires explicit confirmation.
- **Dynamic tools can become a code-execution vulnerability** → v1 only renders/returns stored tool definitions to external Agents; backend arbitrary-code execution is out of scope.
- **MCP can bypass UI gates** → all tools call the same project authorization/domain services; MCP never writes Master/Variant/Approval/Delivery directly.
- **Professional execution may have uncertain side effects** → checkpoint/recovery metadata plus Unknown/no-auto-retry; inspect/reconcile before retry.
- **Duplicating native generation state** → ProviderGenerationTask stays independent and is projected alongside CreativeExecution only in UI.
- **Video reframe may break old projects** → no v1/v2 rewrite; Director Package is additive and final accepted render still uses existing Master/Candidate gates.
- **F6E is implemented but lifecycle-active** → do not rewrite its package; resolve canonical sync/archive before overlapping canonical deltas are synchronized.
- **Current F8 docs are independently dirty** → no reset, no mixed commit, no assumption that this change owns them.

## Migration Plan

### Phase A — specification and surface inventory

1. Land approved North Star document.
2. Create complete legacy operation parity inventory.
3. Obtain independent SPEC review.
4. Resolve lifecycle ordering with completed F6E and current F8 doc-only calibration before canonical synchronization.

No business code or database migration.

### Phase B — daily surface consolidation

Move ordinary daily operations into new Home/Project/Assets/Settings/Production surfaces using existing APIs first. Keep legacy pages/routes alive. Browser acceptance must complete common end-to-end work without legacy navigation before menu retirement.

No new execution tables are required for this phase.

### Phase C — additive creative orchestration persistence

On an isolated copied SQLite database, add:

- Master/Variant creative-intent JSON/hash columns;
- CreativeExecutionPackage;
- CreativeExecution;
- CreativeExecutionOutput;
- CapabilityArtifact;
- CapabilityArtifactRevision;
- CapabilityUse.

Use restrictive FKs, scope constraints, bounded values, idempotency/CAS indexes and downgrade preflight that refuses destructive removal when retained history exists. No live database migration under spec approval.

### Phase D — Creative Execution service/UI

Implement package builder, execution state machine, private work root, result staging/acceptance, director.video.v1, Project/Production UI, Home decision projection and exact MaterialRevision provenance.

### Phase E — local MCP

Expose same-process loopback MCP with dedicated local secret/owner binding, resources/tools, materialization/output staging and Unknown reconciliation. Validate with a controlled local Test Agent before Codex/Claude usage.

### Phase F — Capability Memory

Implement candidate capture, promotion/versioning, scope, search/use, safe rendering, usage/outcome records and UI management. Integrate MCP discovery/use but not arbitrary server-side execution.

### Phase G — Video reframe and professional-tool pilots

Reorganize Video daily UI around Script/Director Package/Assets/Voice/Subtitles/External Execution. Preserve advanced current timeline/render under compatibility/advanced. Pilot real professional-tool orchestration only after the generic Test Agent closure passes.

### Phase H — legacy retirement and closeout

Remove legacy items from the daily menu only when the parity matrix proves no supported action is orphaned. Historical URLs/data remain readable through new/compatibility routes. Run full regression, browser, backup/restore and independent backend/security/frontend/product review before any canonical sync/archive.

## Open Questions

No product-direction question blocks specification review. Implementation details that MAY be adjusted during review without changing the North Star:

- exact names/icons for “创作与执行” UI;
- exact candidate-retention count/TTL for unpromoted capability candidates;
- whether first professional-tool pilot is After Effects, Premiere, Resolve or Photoshop;
- whether an external project file is accepted as a normal `MaterialRevision(kind=other)` or only as a bounded execution metadata reference. The first implementation should prefer ordinary file MaterialRevision when possible and must not store unsafe arbitrary paths as business truth.

Any implementation that requires a second content truth store, automatic capability self-modification, arbitrary backend code execution, destructive migration, or weakened Candidate/Delivery/rights gates must stop and revise the specification.
