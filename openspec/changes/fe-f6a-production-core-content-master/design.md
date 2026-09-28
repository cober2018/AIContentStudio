## Context

Current production state:
- `ContentUnit` already pins Persona/Account/Series, modality, channel, IdentitySnapshot and Workflow.
- `WorkflowRun` freezes the exact workflow definition/checksum and IdentitySnapshot.
- `ProjectWorkflowOutput` records verified Draft/MaterialRevision/Candidate outputs.
- `ProductionDesigner` already provides Context Header, Workflow Mini Canvas, Node Inspector, Shared Assets and three modality shells.
- Candidate v3 freeze in `services/project_review.py` only accepts `ProjectWorkflowOutput(output_kind=draft)` and validates Draft → ContentJob → TopicBrief → FactPack lineage.
- `ContentAsset` still carries text-centric compatibility fields (`draft_id`, `final_body`, `mother_revision_id`).
- `ArtifactKind` lacks a real `video` value.
- `MotherRevision` remains a legacy Topic-level global mother-draft abstraction and MUST NOT become the new project production root.

North Star requires:
`ContentProject × Identity/Perspective × Modality → ContentMasterRevision`
and Text/Image/Video as peer production engines.

## Hard prerequisite before apply

Specification/review may proceed now, but business-code apply MUST NOT start until:
1. FE-F5C is archived;
2. `system-assets-knowledge` and `product-settings` are canonical;
3. the actual final post-F5C `main` commit is visible through the connector;
4. the actual Alembic head is recorded;
5. canonical FE-P1 remains green.

If F5C is still active or connector points at `main@ac6d4dc`, STOP before business-code apply.

Local audit baseline: `main@661e30a`, archived F5C and five synchronized canonical specs, Alembic code head `f5c000000001`. External connector freshness and user apply confirmation remain open gates; local reads do not prove external connector freshness. No database migration was run.

## Goals / Non-Goals

**Goals**
- one immutable revision root for all three modalities;
- exact context lineage on every revision;
- shared asset/evidence refs without duplication;
- common Master checks/readiness/staleness;
- v4 Candidate freeze from Master;
- v3 Draft Candidate compatibility;
- review/diff/package compatibility;
- split Production control shell from modality-specific editor;
- safe extension points for F6B Text, F6C Graphic, F6D Video.

**Non-Goals**
- no full block editor;
- no final Graphic canvas editor;
- no NLE/video timeline implementation;
- no automatic video/image generation provider;
- no automatic channel adaptation engine;
- no deletion/migration of legacy Draft/MotherRevision;
- no global “one mother draft” abstraction;
- no automatic refresh to latest Identity/Brief/Evidence.

## 1. ContentMasterRevision

Add `ContentMasterRevision`:

- `id`
- `project_id`
- `content_unit_id`
- `revision_no`
- `parent_revision_id nullable`
- `modality` (`text|graphic|video`)
- `channel_id nullable`
- `content_form nullable`
- `payload_schema`
- `payload_json`
- `payload_hash`
- `context_hash`
- `identity_snapshot_id`
- `creative_brief_revision_id nullable`
- `fact_boundary_revision_id nullable`
- `origin_workflow_run_id nullable`
- `origin_project_output_id nullable`
- `source_kind` (`workflow_seed|user_edit|context_rebase|system_import`)
- `edit_summary_json`
- `idempotency_key`
- `created_by`
- `created_at`

Constraints:
- unique `(content_unit_id, revision_no)`;
- unique `(content_unit_id, idempotency_key)`;
- parent revision must belong to same ContentUnit;
- project_id/content_unit_id/modality must match the real ContentUnit at save;
- identity_snapshot_id must be the unit's current pinned snapshot for a new revision;
- content_form must resolve against Channel Registry when channel is present;
- historical rows are immutable.

`payload_hash` covers canonical modality payload.
`context_hash` covers exact identity/brief/boundary/channel/content-form references and immutable checksums.

## 2. Save semantics and optimistic concurrency

Master save is explicit and append-only.

Recommended API:
`POST /content-projects/{project_id}/units/{unit_id}/master-revisions`

Input:
- `expected_revision`
- `expected_context_hash optional`: compare the editor's context expectation on a new save; identical authorized replay remains tied to the original request intent.
- `idempotency_key`
- `payload_schema`
- `payload`
- `content_form optional`
- `asset_refs`
- `evidence_refs`
- `edit_summary optional`

Server resolves current:
- ContentUnit + modality/channel;
- IdentitySnapshot;
- latest CreativeBriefRevision if present;
- current ProjectFactBoundaryRevision if present.

If Brief or Fact Boundary is absent, revision MAY still be saved for drafting, but readiness exposes `brief_missing` / `evidence_missing` and Candidate freeze is blocked.

Stale expected_revision or DB race returns 409 with no partial refs/checks/events.

Repeated same idempotency key returns the existing revision.

This applies only after authorization and when the canonical request fingerprint is identical; replay lookup precedes stale expected_revision rejection. Same key with different payload/refs/context intent returns 409. Fingerprint includes source/action, requested context expectations, normalized payload, ordered asset/evidence refs and edit provenance. Revision-head CAS/locking, same-unit parent, refs and ProjectEvent commit atomically; unique constraints alone are not expected_revision enforcement.

Master saves and upstream Project/Unit/Brief/Fact Boundary mutations share a project-row transaction lock. Before committing a new Master, the server refreshes Unit and relevant context heads and rejects changed modality, archived state or context hash with rollback. PostgreSQL and SQLite both use a no-op Project UPDATE to hold the write/row lock without altering the Project timestamp; SQLite writer contention returns 409. Real PostgreSQL race acceptance remains a separate gate.

## 3. Master context never silently advances

Historical revision context is frozen.

Later changes to:
- IdentitySnapshot;
- CreativeBrief revision;
- Project Fact Boundary;
- ContentUnit channel;
- content form
do not rewrite prior Master revisions.

A new explicit save can create N+1 using current context, even when payload is unchanged. Such a revision is effectively a context rebase and must rerun required checks.

Derived current-state projection:
- `current`
- `stale_identity`
- `stale_brief`
- `stale_evidence`
- `stale_channel`
- `incomplete_context`

No mutable “master status” table is required.

Identity currentness follows FE-F3B: compare Master with the unit's actual pinned snapshot, not latest hierarchy revisions. Hierarchy drift may be advisory but MUST NOT silently repin or automatically invalidate pinned production. Applying a new identity remains explicit rebind/Fork + Archive. A same-unit context rebase uses its pinned identity plus current Brief/Boundary. Content form has no current ContentUnit column: select and persist a Registry-validated form on Master; do not invent a mutable unit field or treat a Registry default change as user-approved form change.

## 4. Minimal modality payload envelopes

F6A defines only stable top-level envelopes. F6B/C/D define professional editor schemas later.

### text.master.v1

Minimum:
- `title nullable`
- `document nullable`
- `markdown nullable`
- `structured nullable`
- `citations/declarations optional`

At least one of document/markdown must contain content before Candidate freeze.

### graphic.master.v1

Minimum:
- `title nullable`
- `canvases` array
- optional `render_asset_ref`
- optional `metadata`

F6A validates stable IDs/order and referenced asset slots. It does not define full layer editing behavior.

Candidate freeze requires a validated final render asset when no deterministic graphic renderer exists.

### video.master.v1

Minimum:
- `title nullable`
- `script`
- `shots` array
- `timeline`
- optional `render_asset_ref`
- optional `metadata`

F6A validates stable structure only. It does not implement shot editing/NLE.

Candidate freeze requires a verified final video render asset when no deterministic video renderer exists.

Empty structural shells may be saved as drafts but are never Candidate-ready.

## 5. ContentMasterAssetRef

Add immutable `ContentMasterAssetRef`:

- `id`
- `master_revision_id`
- `material_revision_id`
- `role`
- `slot_key nullable`
- `sort_order`
- `placement_json`
- `rights_snapshot_json`
- `content_hash_snapshot`
- `created_at`

Allowed common roles include:
`cover|inline|canvas_layer|chart|broll|overlay|audio|subtitle_asset|render_output|other`.

A Master revision may reference only MaterialRevision already visible to that Project through:
- ProjectMaterialReference; or
- verified ProjectWorkflowOutput.

A raw global MaterialRevision ID alone is insufficient.

The exact MaterialRevision and hash are frozen in the Master ref. Live revocation is still checked at Candidate freeze/approval/delivery.

No bytes are copied.

## 6. ContentMasterEvidenceRef

Add immutable `ContentMasterEvidenceRef`:

- `id`
- `master_revision_id`
- `fact_pack_item_id`
- `role`
- `content_locator_json`
- `sort_order`
- `snapshot_checksum`
- `created_at`

The referenced FactPackItem must belong to the Master revision's exact Fact Boundary FactPack and have a frozen snapshot checksum.

Common roles:
`claim|citation|visual_basis|script_basis|context`.

Evidence refs do not change FactPack or Fact Boundary.

A Master without a Fact Boundary cannot persist FactPackItem evidence refs.

## 7. ContentMasterCheckRun

Add append-only `ContentMasterCheckRun`:

- `id`
- `master_revision_id`
- `check_kind`
- `profile_key nullable`
- `profile_version nullable`
- `input_hash`
- `status` (`pass|warning|blocker|incomplete|stale`)
- `report_json`
- `provider_key nullable`
- `provider_version nullable`
- `created_at`

Required common check kinds:
- `master_schema`
- `evidence`
- `rights`
- `render`

Future modality slices may add:
- text fact/platform/SEO/domain;
- graphic layout/text-overflow/platform;
- video subtitle/voice/timeline/platform.

Check `input_hash` covers Master payload/context/assets/evidence.
Checks are never copied forward as current when a new Master revision is created.

Check rows never mutate to stale; staleness is a read projection of input/profile/adapter versions and live authorization. Freeze selects the latest applicable result per required kind; an older pass cannot hide a later blocker. Warning dispositions bind exact results/inputs and do not carry forward. F6A common checks are deterministic; future network/AI checks require explicit capability/action.

## 8. ProductionModalityAdapter

Add a server-side modality adapter registry, separate from Channel Registry and Workflow Plugin Registry.

Descriptor contract:
- `modality`
- `payload_schema`
- `validate_payload`
- `required_check_kinds`
- `build_preview`
- `build_render_snapshot`
- `build_package_projection`
- `candidate_freeze_available`
- unavailable reason

Initial adapters:
- text
- graphic
- video

Text can produce deterministic markdown/document preview.
Graphic/video may be Candidate-freeze-ready only when exact `render_output` MaterialRevision satisfies type/hash/rights requirements.

No adapter may fabricate generated media.

Real media bytes alone do not prove a render of this Master. A `render_input_hash` covers payload/context/non-render asset/evidence inputs, excluding the final render reference to avoid a hash cycle. Bind exact project-visible final revisions through verified renderer provenance or an explicit editor-confirmed manual-render attestation stored on the new Master, labeling the two origins distinctly. Verify bytes/hash, MIME/kind and live rights. Multi-canvas content requires all declared outputs, not silently one image. Changed input invalidates the binding. Unsupported channel/form/modality combinations stay unavailable; F6A adds no channel format or publisher by inference.

## 9. Workflow output → Master seed

Add explicit compatibility action:

`POST /content-projects/{project_id}/units/{unit_id}/master-revisions/from-output`

Initial supported source:
- verified same-unit `ProjectWorkflowOutput(output_kind=draft)` for text.

Server converts current Draft into `text.master.v1`, preserving:
- Draft ID/revision/input hash;
- WorkflowRun/output/attempt lineage;
- document/markdown/structured content;
- exact MaterialRevision uses that can be proven;
- evidence refs that can be mapped to the current Fact Boundary.

Unmappable claims/media are surfaced as warnings/incomplete, not silently invented.

Verify Draft/Run/Step/Attempt consistently and reject stale/failed/replaced attempts even when old ProjectWorkflowOutput remains. Freeze exact Draft content/hash at seed time; later Draft edits do not mutate Master. Source identity matches the pinned unit snapshot. Current Brief/Boundary used for Master are separate new context, not relabeled historical run provenance. Client origin IDs cannot fabricate association.

Graphic/video workflow assets can be attached to a manually/adapter-created Master, but F6A does not pretend a single image/video clip is automatically a complete professional Master.

## 10. ProjectWorkflowOutput compatibility

Extend project output contracts to recognize `content_master_revision` when a verified future node actually emits `content_master_revision_id`.

F6A does not require existing plugins to emit it.

Output association must verify:
- Master belongs to run's ContentUnit;
- source workflow provenance matches the run where applicable.

Existing Draft/Material/Candidate output kinds remain unchanged.

## 11. Candidate manifest v4

Candidate v4 freezes one exact ContentMasterRevision.

Required top-level sections:

- `schema_version: 4`
- `artifact_kind`
- `content_form`
- `channel`
- `project`
- `identity`
- `brief`
- `evidence`
- `content_master`
- `content`
- `assets`
- `evidence_refs`
- `checks`
- `render`
- `production`
- `citations`
- `declarations`

`content_master` includes:
- revision ID/no
- parent ID
- modality
- payload schema/hash
- context hash

`production` includes:
- origin WorkflowRun ID/version/checksum when present
- origin ProjectWorkflowOutput/node/attempt when present
- source_kind/edit provenance

Candidate hash covers all frozen visible content/context/assets/evidence/check/render/provenance.

Manifest v4 does not require Draft, TopicBrief or MotherRevision.

## 12. ContentAsset evolution

Add nullable:
- `content_master_revision_id` FK/index.

Change compatibility field:
- `final_body` MAY be null for non-text v4 Candidates.
- legacy v1/v2/v3 rows continue to populate it.

Promote `ArtifactKind.video` as a real supported value.
Graphic maps to image/graphic-compatible artifact metadata; video maps to video.

Do not rewrite historical ContentAsset rows.

`draft_id`, `topic_brief_id`, `mother_revision_id` stay nullable compatibility fields and MUST NOT be fabricated for v4.

## 13. Candidate freeze dual path

Evolve freeze input to exactly one source:

Legacy:
- `project_output_id` → current v3 Draft freeze.

New:
- `content_master_revision_id`
- `expected_payload_hash`

v4 freeze verifies:
- a manually authored Master does not require a Draft/Run; workflow-source lineage checks apply only when actual workflow origin exists;
- Project/Unit ownership;
- revision belongs to unit and is current/latest;
- revision modality/channel context matches unit;
- revision is not stale against current Identity/Brief/Fact Boundary/channel;
- required Master checks are current;
- exact assets exist, hashes match and live rights are ready;
- evidence boundary and evidence refs are valid;
- modality adapter can build a real render snapshot;
- no unsupported/fabricated render fallback.

Repeated identical freeze returns the same Candidate.

## 14. Candidate v4 readiness

Freeze is blocked when:
- no IdentitySnapshot;
- missing Brief or Fact Boundary;
- context stale;
- payload schema invalid;
- required check blocker/incomplete/stale;
- referenced asset missing/hash mismatch/revoked/not public-use-ready when required;
- evidence revoked/legacy_untyped/missing checksum;
- graphic/video final render unavailable;
- content form cannot resolve.

Warnings remain explicit and follow existing review warning-disposition contract where applicable.

## 15. Approval / live invalidation

F4 approval separation remains unchanged.

Approval for v4:
- binds exact Candidate ID/hash;
- never rewrites Master revision;
- rechecks candidate integrity;
- rechecks live evidence/material revocation;
- rejects unsupported current rights state.

A later Master revision creates a new Candidate; an old approved Candidate stays historical.

## 16. v4 Review preview and diff

Project Review supports both v3 and v4.

Preview:
- text: title + markdown/document summary;
- graphic: canvas summary + exact render asset preview when available;
- video: script/shot/timeline summary + exact render asset preview when available.

Diff compares:
- content_master payload hash/content projection;
- assets/order/placement;
- evidence refs;
- IdentitySnapshot;
- Brief/Fact Boundary;
- Workflow provenance;
- checks;
- render.

Text similarity is optional and only meaningful for text payloads.
Graphic/video must not fake text similarity scores.

## 17. v4 local delivery package

`copy_package` / `manual_handoff` supports v4 locally.

Text:
- markdown/document/render projection + referenced media.

Graphic:
- manifest + exact final rendered image bytes + referenced public-use assets as needed.

Video:
- manifest + exact final rendered video bytes + subtitle/cover/other declared package assets as available.

Package must verify current rights/hash before reading bytes.

Unsupported render/package shapes fail closed.
Do not fall back to v3/v1 packaging for a v4 Candidate.

Remote publisher support remains capability-gated and is not added by F6A.

Dispatch on persisted manifest schema before Draft/text access. V4 remote actions stay unavailable unless an existing publisher explicitly advertises verified v4 + modality + form support; F6A grants none by inference. Local packages use frozen named references with allowlisted paths, never arbitrary payload file paths/URLs. Unknown/reconciliation and prepared→commit→side-effect ordering remain unchanged.

## 18. Project Versions and Overview

Project Versions SHALL include ContentMasterRevision with:
- unit/modality
- revision/payload hash/context hash
- exact Identity/Brief/Boundary refs
- origin WorkflowRun
- creation actor/time

Overview SHALL derive production attention when the current Master is:
- stale_context
- incomplete_context
- check_blocked
- render_unready

It must not create a second mutable stage table.

## 19. Production Workspace component split

Refactor the current monolithic `ProductionDesigner` into:
- `ProductionWorkspace`
- `ProductionContextHeader`
- `WorkflowMiniCanvas`
- `NodeInspector`
- `ProductionAssetDrawer`
- `ContentMasterPanel`
- `ModalityWorkspace`

Modality extension components:
- `TextStudioShell`
- `GraphicStudioShell`
- `VideoStudioShell`

F6A shells expose:
- current Master revision
- Save Revision
- revision history
- readiness/stale state
- shared context/assets
- minimal payload JSON/summary for development/acceptance

F6A does not deliver final professional editors.

Workflow design/debug and content editing remain separate concerns.

## 20. API

Recommended router:
`routers/content_masters.py`

Read:
- GET `/content-projects/{project_id}/units/{unit_id}/master-revisions`
- GET `/content-projects/{project_id}/units/{unit_id}/master-revisions/current`
- GET `/content-projects/{project_id}/units/{unit_id}/master-revisions/{revision_id}`
- GET `/content-projects/{project_id}/units/{unit_id}/master-revisions/{revision_id}/readiness`
- GET `/content-projects/{project_id}/units/{unit_id}/master-revisions/{revision_id}/checks`

Write:
- POST `/content-projects/{project_id}/units/{unit_id}/master-revisions`
- POST `/content-projects/{project_id}/units/{unit_id}/master-revisions/from-output`
- POST `/content-projects/{project_id}/units/{unit_id}/master-revisions/{revision_id}/checks/run`

Existing Candidate route evolves to accept v3 or v4 source.

## 21. Authorization and history safety

All Master APIs reuse ContentProject/ContentUnit ownership and archive rules.

Archived Project/Unit:
- Master history readable;
- no new revision/check/freeze.

Raw revision/ref IDs from another Project/Unit disclose nothing.

No Master revision, asset ref, evidence ref or check row is hard-deleted when referenced by Candidate/history.

Any Master is production history without requiring a Run. Extend the existing unit history predicate: selection changes Fork + Archive; deletion archives a Master-bearing unit. Include Candidate/approval history where present. New and legacy raw Asset/Export/Review/Target/Package/Run endpoints share project ownership/archive gates; unsupported legacy v4 mutation/export fails closed. Shared library visibility grants no private Master access.

## 22. Migration

Add reversible migration after the actual post-F5C head.

Create:
- `content_master_revision`
- `content_master_asset_ref`
- `content_master_evidence_ref`
- `content_master_check_run`

Alter:
- add `content_asset.content_master_revision_id`;
- allow `content_asset.final_body` nullable if required by current DB schema;
- update model-level ArtifactKind to include `video`.

No Draft/MotherRevision/ContentAsset backfill.
No production migration in this task.

Observed final_body is NOT NULL; channel/title remain required. Use schema-aware serializers and truthful channel/form gates, not fake text/channel lineage. Empty/legacy-only isolated downgrade restores original schema. If retained v4 rows have NULL body or Master-linked history, downgrade fails in a read-only preflight before destructive DDL; no deletion or fake backfill to force rollback. Validate actual PostgreSQL storage/constraints (artifact_kind currently String), not Python enum alone.

## 23. FE-P1 performance

Production route remains its own lazy boundary.

Refactor must not pull:
- legacy Workspace TipTap editor into generic Production shell;
- XYFlow global Workflow page;
- Graphic/Video future heavy editors before their modality route section is needed.

Modality-specific code SHOULD be lazy-loaded within Production where practical.

Existing `/projects`, `/assets`, `/settings`, `/learning` budgets remain green.

## 24. Required tests

Backend:
1. Master owner/project/unit authorization
2. append-only revision + expected_revision conflict
3. idempotent save
4. parent same-unit constraint
5. exact IdentitySnapshot pin
6. exact Brief/Fact Boundary refs
7. save allowed with missing context but readiness incomplete
8. context staleness after identity/brief/boundary/channel advance
9. asset ref must already belong to project shared pool
10. asset bytes are not copied
11. evidence ref must belong to exact frozen boundary
12. Master check append-only/input-hash behavior
13. new revision does not inherit checks as current
14. text/graphic/video payload adapter validation
15. graphic/video no fake Candidate without real final render
16. Draft output → text Master lineage
17. foreign ProjectWorkflowOutput rejected
18. ContentAsset v4 has master link and no fabricated Draft/MotherRevision
19. ArtifactKind video
20. v4 manifest canonical hash stability
21. v4 freeze idempotency
22. stale Master freeze rejected
23. live asset/evidence revocation blocks freeze/approval/package
24. v3 freeze regression remains green
25. v1/v2/v3 history readable
26. v4 Review diff modality-aware
27. v4 local package text
28. v4 local package graphic/video with exact render bytes
29. unsupported package fails closed
30. Project Versions includes Master
31. Overview master stale/readiness projection
32. archived Project/Unit history safety
33. F2/F3A/F3B/F4/F5 regressions green

Frontend/browser:
- create/save Text Master revision
- create/save Graphic shell revision
- create/save Video shell revision
- revision conflict/reload
- context stale after upstream change
- seed Text Master from real Draft workflow output
- run Master checks
- freeze v4 text Candidate
- freeze graphic/video only with exact render asset
- Review preview/diff/check
- approval + local package
- old v3 Candidate remains readable
- Production shell/workflow debugger behavior unchanged
- FE-P1 budgets green

## 25. Rollout sequence

1. prerequisite reconciliation after F5C archive
2. migration/models
3. Master save/read/stale projection
4. asset/evidence refs
5. Master checks
6. modality adapter registry
7. Draft→Text Master compatibility seed
8. Candidate v4 freeze
9. Review/diff/package v4
10. Project Versions/Overview integration
11. Production Workspace component split
12. three minimal modality shells on Master
13. targeted/full tests + browser + bundle gates
14. independent review
15. canonical sync/archive only after explicit authorization

## 26. Audited decisions and risks

- Complete MODIFIED blocks preserve post-F5C requirements/scenarios; partial deltas would delete unrelated contracts at archive.
- Save/freeze share ordered transaction locking/CAS with unit history mutations and context updates; revalidate head/context/live rights at commit. Concurrent save/archive/context/rights changes produce a serialized valid result or 409, not an invalid Candidate. Approval/new authorization require a current context-valid Master. Existing authorized historical delivery retains frozen target/reconciliation semantics and live rights checks, without retargeting.
- Bound payload bytes/depth/canvas/shot/ref counts and paginated reads server-side. Typed validation resolves slots/locators and every embedded media/evidence reference; reject dangling/duplicate IDs, non-finite JSON and arbitrary file paths. Safe projections omit infrastructure paths and credentials.
- Authoritative hashes include frozen refs/order/placement/context/provenance with separately verified render-input binding. Freeze retry reuses the exact check set; new authoritative check results intentionally change frozen inputs, but execution timestamps alone are not content changes.
- F6A is common core, not F6B/C/D editors, tenancy or remote publishing. This phase writes no tests; targeted regression generation needs user authorization.

## Open gates before implementation

1. Explicit user confirmation of calibrated proposal/apply and targeted test-code authorization.
2. Real connector read of post-F5C main661e30a or descendant, canonical F5C and code migration head; local evidence is not external verification.
3. Fresh isolated tests/build/FE-P1 baseline after creating or reusing an available worktree; no production migration.
