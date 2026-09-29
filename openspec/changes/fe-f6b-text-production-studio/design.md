## Context

Verified base before this specification:
- workspace `AIContentStudio`
- local `main@ca52aa5`
- FE-F6A archived and canonical
- working tree clean
- `production-content-master` is canonical
- F6B implementation has not started

Current Text reality:
- `ContentMasterRevision` + exact asset/evidence refs + checks + Candidate v4 are durable production truth.
- `TextStudioShell` is still a raw JSON textarea.
- `text.master.v1` allows `markdown`, optional `document`, optional `structured`; Markdown is the deterministic v1 render source.
- legacy `/workspace` has TipTap + Markdown serialization, selection rewrite, Draft fact-check and citation display.
- Draft `document_json` is a compatibility composition model where Markdown remains truth.
- `DraftClaim` and `DraftCheckRun` are Draft-specific and must not become the new Text Studio data model.
- v4 Review/Approval/Delivery already operate on immutable Master Candidates.

## Apply prerequisite

This document/package is a proposal only.

Business-code apply MUST NOT start until:
1. this F6B specification is reviewed;
2. the user explicitly authorizes F6B apply;
3. connector re-verifies the actual apply baseline commit and clean state;
4. no later canonical change conflicts with these deltas.

No push, deploy, production migration or F6C/F6D work is implied.

## Goals

- professional structured Text creation inside Production Workspace;
- one authoritative v2 document model;
- exact assets/evidence/citations;
- selection and block-level AI assistance with explicit accept;
- identity/fact/platform/readability feedback;
- immutable Master revision saves and structured diff;
- v1/Draft compatibility without rewriting history;
- Candidate v4 / Review / local package remains the publication path;
- Text editor code remains lazy from common Production.

## Non-goals

- Graphic canvas editor;
- Video timeline/NLE;
- real-time multi-user collaboration;
- comments/track-changes workflow comparable to Google Docs;
- replacing Review decisions;
- automatic Identity/ContentMemory mutation;
- automatic channel adaptation;
- new connectors or publishers;
- remote publishing changes;
- deleting Draft/MotherRevision/legacy Workspace;
- storing TipTap/ProseMirror JSON as the durable business schema;
- introducing a second suggestion/check/revision table.

---

# 1. Text schema versioning

F6B SHALL make Text schema dispatch explicit.

Supported:
- `text.master.v1`: existing compatibility schema; readable/freezeable under existing rules.
- `text.master.v2`: new professional Text Studio schema; default for new user-authored Text revisions and new Draft seeds after F6B.

The production modality registry SHALL dispatch by `(modality, payload_schema)`, not only by modality.

Recommended API/service shape:

```py
adapter_for(modality: str, payload_schema: str | None = None)
default_payload_schema(modality: str) -> str
supported_payload_schemas(modality: str) -> tuple[str, ...]
```

For Text:
- default = `text.master.v2`
- `text.master.v1` remains registered for history.

Historical v1 Master rows MUST NOT be rewritten.

---

# 2. `text.master.v2` payload

The authoritative payload is:

```json
{
  "title": "string",
  "document": {
    "schema": "studio.text.document.v1",
    "blocks": [],
    "citations": []
  }
}
```

Optional bounded metadata MAY be added only when it is part of content rather than infrastructure. There is no editable `markdown` truth in v2.

The deterministic renderer produces Markdown for preview/Candidate/package.

Renderer implementation: citation labels are escaped literal text, not inferred links. When CommonMark delimiter flanking cannot preserve emphasis at punctuation or adjacent marked runs, the renderer emits only fixed server-generated inline `strong`/`em` tags while escaping all user content. This is still the deterministic Markdown projection, not an HTML export artifact or a raw-HTML input capability. Inline code containing line breaks is rejected in favor of an explicit code block; code-only whitespace is not padded or collapsed.

## 2.1 Stable block IDs

Every block SHALL have a stable user-content ID:
- string;
- non-empty;
- max 150 chars;
- unique inside the document.

Generated IDs are client-created and server-validated. Reordering preserves IDs.

## 2.2 Inline runs

Text-bearing blocks use Studio inline runs, not ProseMirror JSON:

```json
[
  {"text":"Example ","marks":[]},
  {"text":"important","marks":[{"type":"bold"}]}
]
```

Supported initial marks:
- `bold`
- `italic`
- `code`
- `link` with bounded `http`/`https` href

Marks SHALL be normalized deterministically and invalid/overlapping engine-specific state SHALL not enter storage.

## 2.3 Block types

### heading

```json
{
  "id":"b1",
  "type":"heading",
  "level":2,
  "content":[...]
}
```

Levels: 1–4.

### paragraph

```json
{"id":"b2","type":"paragraph","content":[...]}
```

### quote

```json
{
  "id":"b3",
  "type":"quote",
  "content":[...],
  "attribution":"optional"
}
```

### bullet_list / ordered_list

```json
{
  "id":"b4",
  "type":"bullet_list",
  "items":[
    {"id":"li1","content":[...]}
  ]
}
```

Item IDs are stable/unique inside the list. A list-item locator SHALL include both the containing `block_id` and `list_item_id`; item-local offsets never address an implicit concatenation of different items.

### callout

```json
{
  "id":"b5",
  "type":"callout",
  "tone":"info|note|warning",
  "content":[...]
}
```

### code

```json
{
  "id":"b6",
  "type":"code",
  "language":"python",
  "code":"..."
}
```

### image

```json
{
  "id":"b7",
  "type":"image",
  "material_revision_id":123,
  "alt_text":"...",
  "caption":"..."
}
```

### chart

Same exact-reference pattern as image but material kind must be chart-compatible.

### divider

```json
{"id":"b8","type":"divider"}
```

No unknown block type is silently persisted.

---

# 3. Document bounds and canonicalization

Add a dedicated Text Document service, recommended:

`apps/api/app/services/text_documents.py`

Responsibilities:
- validate schema/version;
- validate block/runs/marks;
- enforce depth/count/string/URL bounds;
- stable-ID uniqueness;
- validate embedded exact references;
- canonical normalize;
- render plain text;
- render Markdown;
- generate block lookup and text-offset maps;
- compute document hash;
- deterministic v1/Draft conversion;
- structured diff.

Recommended hard bounds, subject to implementation review:
- max 2 MB canonical JSON inherited from Production Core;
- max 2,000 blocks;
- max 5,000 list items;
- max 20,000 inline runs;
- max 500 chars title;
- max 150 chars block/item IDs;
- max 1,000 chars link URL;
- no file/local/storage/render infrastructure paths.

Use existing Production Core JSON bounds as an outer bound; Text validation is stricter.

---

# 4. One truth: document authoritative, Markdown derived

For `text.master.v2`:
- `document` is authoritative.
- renderer derives `body_markdown`.
- Candidate manifest freezes both the v2 structured payload and deterministic render snapshot.
- local package uses the frozen render.
- Review preview may show structured metadata but the human-readable text projection comes from the frozen deterministic render.

The save API SHALL reject a client-supplied editable v2 `markdown` field to prevent dual truth.

The renderer SHALL be deterministic across dictionary ordering and repeated calls.

---

# 5. Text v2 adapter

Introduce schema-specific Text adapters.

Recommended classes:

```py
TextMasterV1Adapter
TextMasterV2Adapter
```

`TextMasterV1Adapter` preserves current behavior.

`TextMasterV2Adapter`:
- validates structured document;
- builds bounded preview;
- renders deterministic Markdown;
- computes render input/content hash;
- provides package projection;
- declares text-specific required/conditional checks.

Graphic/Video adapters are not otherwise changed.

---

# 6. Dynamic check requirements

The adapter contract SHALL evolve from a fixed tuple to an exact schema-aware requirement resolver, e.g.:

```py
required_checks(db, master) -> list[str]
```

Common v2 Text checks:
- `master_schema`
- `evidence`
- `rights`
- `render`
- `text_structure`
- `text_fact`
- `text_identity`
- `text_platform`

Conditional:
- `text_discoverability` only when a published discoverability profile resolves for exact channel/content_form.

Historical v1 retains its historical/common check behavior unless explicitly saved as v2.

Candidate freeze SHALL use the exact schema-specific current requirement list.

---

# 7. Text structure check

`text_structure` is deterministic.

It covers:
- document schema/version;
- block IDs/types;
- inline runs/marks;
- duplicate IDs;
- empty/invalid lists;
- image/chart exact refs;
- citation locators;
- heading hierarchy warnings;
- empty document;
- title/content structural bounds;
- channel/form hard deterministic limits when they are document-structural.

Result uses normal ContentMasterCheckRun semantics:
- pass
- warning
- blocker
- incomplete
- stale

---

# 8. Evidence and citations

F6B reuses `ContentMasterEvidenceRef`; no citation table is added.

Document citations:

```json
{
  "id":"cite-1",
  "block_id":"b2",
  "start":10,
  "end":42,
  "fact_pack_item_id":83,
  "label":"optional"
}
```

Rules:
- citation IDs unique;
- block exists and is text-bearing;
- offsets refer to canonical plain text for that block;
- `0 <= start < end <= len(block_plain_text)`;
- exact FactPackItem must also be declared in `evidence_refs`;
- ContentMasterEvidenceRef locator must match the citation block/range;
- snapshot checksum stays outside payload in the exact evidence ref;
- removing a citation removes its use from the next revision but never mutates FactPack history.

The editor SHALL show facts from the exact current Project Fact Boundary, not a global unrelated pack.

Existing project fact-boundary + FactPack detail APIs SHOULD be reused; F6B SHOULD NOT create a second Evidence library endpoint unless current APIs prove insufficient.

---

# 9. Image/chart blocks and exact assets

Image/chart document blocks embed only `material_revision_id`.

The corresponding revision SHALL also be declared in `asset_refs` with exact content hash.

Server checks:
- project-visible exact revision;
- expected material kind;
- exact hash;
- current rights according to Production Core;
- no raw path/URL;
- every embedded material ID is declared;
- unused refs MAY be retained only when explicitly allowed by current Master editing state; Candidate readiness SHOULD warn on unreferenced content assets rather than silently use them.

Text Studio asset picker uses current Project Shared Assets and does not copy bytes.

---

# 10. TipTap is an editor engine, not the contract

Refactor/reuse the existing editor into a Studio adapter, recommended files:

- `apps/web/src/product/text/TextDocumentEditor.tsx`
- `apps/web/src/product/text/textTiptapAdapter.ts`
- `apps/web/src/product/text/TextEditorToolbar.tsx`

Responsibilities:
- Studio Document -> TipTap document;
- TipTap document -> Studio Document;
- preserve stable block IDs;
- preserve supported marks;
- reject unsupported engine nodes before save; any lossy conversion requires an explicit preview and user confirmation, never a silent drop;
- selection locator maps to Studio block ID + offsets;
- no TipTap/ProseMirror JSON leaves the browser as persistent content.

The existing legacy `components/editor.tsx` and `/workspace` remain compatible. Shared helper extraction is allowed only when it does not alter legacy Draft semantics.

---

# 11. Text Studio frontend composition

Replace the Text JSON textarea with a professional workspace while leaving Graphic/Video shells intact.

Recommended composition:

```text
TextStudioShell
├── TextEditorToolbar
├── TextDocumentEditor
├── TextContextPanel
│   ├── EvidencePanel
│   ├── AISuggestionPanel
│   ├── IdentityPanel
│   ├── TextChecksPanel
│   └── RevisionHistoryPanel
└── TextStatusBar
```

Existing Production context/workflow components stay outside the Text editor.

## 11.1 Master state integration

Text Studio operates on the current selected Master or a new empty v2 local draft.

It must integrate with ContentMasterPanel while preserving:
- Workflow dirty/save independent from Master dirty/save;
- historical Master read-only;
- archived project/unit read-only;
- explicit context rebase behavior;
- explicit durable Save Revision.

The raw JSON payload/ref editors SHOULD be removed from normal Text UX but MAY remain behind a development/debug details disclosure if safe and read-only.

Graphic/Video F6A JSON shells are unchanged in F6B.

---

# 12. Local edit state and durable save

Typing/formatting/AI accept modifies local browser state only.

Durable persistence occurs only on explicit:
`Save Text Master Revision`

Save calls the existing generic Master save API with:
- expected revision;
- expected context hash when applicable;
- idempotency key;
- `payload_schema=text.master.v2`;
- structured payload;
- exact asset refs;
- exact evidence refs;
- validated edit summary.

Browser unload/navigation with dirty content SHALL warn.

F6B MAY use session/local draft recovery only as non-authoritative UX protection. Such recovery:
- is never a ContentMasterRevision;
- never becomes Candidate input directly;
- must be clearly labeled unsaved;
- may be omitted in initial F6B if it complicates correctness.

---

# 13. Explicit v1 -> v2 upgrade/fork

Historical `text.master.v1` is read-only in the professional editor.

Add explicit server conversion.

Recommended APIs:

```text
GET  /content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/text-v2-upgrade-preview
POST /content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/text-v2-upgrade
```

POST input:
- `expected_revision`
- `expected_payload_hash`
- `expected_context_hash` (the context read for the preview)
- `idempotency_key`

Conversion priority:
1. preserve legacy Markdown/body as the text authority; reuse document/structured text only when its deterministic text projection can be proven equivalent to that authority;
2. otherwise parse legacy Markdown with a bounded deterministic converter, using provable document data only for exact media/layout hints and reporting mismatches;
3. map only exact declared asset/evidence refs;
4. unsupported constructs degrade predictably with explicit warnings.

Upgrade always creates a new revision:
- parent = current v1 revision;
- schema = v2;
- source_kind = explicit upgrade/fork;
- edit_summary records conversion warnings/source schema.

It never rewrites v1.

Upgrade preview returns proposed v2 document + warnings without mutation.

---

# 14. Draft -> v2 seed after F6B

The existing `from-output` endpoint remains the compatibility entry but, for new Text seeds after F6B:
- output is `text.master.v2`;
- exact Draft/Run/Attempt lineage remains;
- Draft Markdown/document is deterministically converted;
- only provable MaterialRevision and FactPackItem refs map;
- unmapped content becomes explicit conversion warning/incomplete check state;
- existing historical v1 seeds are unchanged.

A repeated idempotent seed replays the committed v2 revision without re-reading later Draft changes.

---

# 15. AI suggestion API

AI never directly writes a Master.

Recommended endpoint:

```text
POST /content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/text-suggestions
```

It may operate against unsaved local v2 content while anchoring to an authorized base Master.

Input:

```json
{
  "base_payload_hash":"...",
  "working_document": {...},
  "operation":"rewrite|expand|shorten|tone|restructure",
  "selection":{
    "block_id":"b2",
    "start":10,
    "end":40
  },
  "instruction":"optional bounded text"
}
```

For restructure, selection MAY instead identify a bounded contiguous block range.

Server:
- authorizes Project/Unit/Master;
- rejects archived history;
- validates base hash;
- validates working document v2;
- derives selected text/context server-side;
- loads exact pinned IdentitySnapshot/Brief/Fact Boundary;
- packs only model-use-allowed evidence;
- uses the existing configured rewrite model route;
- treats source/evidence content as data, never instructions;
- records LLMRun;
- returns a bounded structured patch;
- performs no Master write.

Operations:
- rewrite
- expand
- shorten
- tone
- restructure

---

# 16. AI patch contract

Simple operations return:

```json
{
  "kind":"replace_text",
  "block_id":"b2",
  "start":10,
  "end":40,
  "replacement":[...inline runs...]
}
```

Restructure returns:

```json
{
  "kind":"replace_blocks",
  "from_block_id":"b2",
  "to_block_id":"b4",
  "blocks":[...validated Studio blocks...]
}
```

Patch SHALL be validated against the same Text Document schema before return.

UI:
- shows before/after diff;
- user explicitly Accept or Reject;
- Accept applies to local state only;
- Reject does nothing;
- stale patch cannot apply if the target local document changed since request.

---

# 17. AI provenance without a new table

F6B targets zero new tables.

LLMRun SHALL store:
- purpose such as `text_master_edit`;
- exact request input_hash;
- raw/parsed output;
- usage/status.

For Text suggestions, `parsed_output_json` SHOULD include bounded provenance metadata:

```json
{
  "patch": {...},
  "provenance": {
    "project_id": 1,
    "unit_id": 2,
    "base_master_id": 3,
    "base_payload_hash": "...",
    "working_document_hash": "...",
    "operation": "rewrite",
    "selection_hash": "..."
  }
}
```

When saving a revision with accepted AI edits, `edit_summary.ai_edits[]` may reference LLMRun IDs, but the server SHALL verify:
- run exists/succeeded;
- purpose is supported;
- project/unit/base provenance matches;
- patch hash/output matches the accepted edit metadata.

This proves a server-issued suggestion, not acceptance by itself. Section 42 defines deterministic application receipts and the distinction between verified application and later manual modification. Provenance is a server-created envelope after output validation, never ownership/context metadata taken from model output.

Unverified client-supplied model IDs are rejected or omitted; they are never frozen as trusted provenance.

No suggestion row is required.

---

# 18. Identity context in Text Studio

Identity panel is read-only and sourced from the Master-pinned IdentitySnapshot.

It SHALL show bounded relevant profile fields and clarify:
- edits do not mutate identity;
- latest hierarchy does not silently replace pinned identity;
- rebind happens through existing explicit project/unit flow.

`text_identity` check:
- compares content with explicit pinned identity constraints;
- MAY use semantic model review when configured;
- deterministic/semantic coverage is explicit;
- unavailable semantic review MUST NOT be reported as a fully verified pass;
- a partial-coverage warning follows existing warning-disposition rules rather than silently changing identity.

---

# 19. Text fact check

`text_fact` reuses/refactors current factchecker logic at service level rather than creating Draft rows.

Input:
- deterministic rendered/plain Text v2 content;
- exact current Master Fact Boundary FactPack snapshots;
- exact model-use eligibility;
- citations/evidence refs.

Output:
- ContentMasterCheckRun report;
- issues include a best-effort structured locator (`block_id`, offsets when deterministic mapping exists);
- no DraftClaim row is created.

LLM failure falls back according to existing fact-check semantics and MUST NOT default to a fake semantic pass.

---

# 20. Platform check

`text_platform` resolves exact channel/content_form via Channel Registry.

It reuses deterministic rule descriptors where applicable:
- length/shape requirements;
- forbidden structure;
- required metadata;
- channel/content-form rules.

The check never mutates content.

Missing required rule implementation -> incomplete, not pass.

---

# 21. Discoverability check

`text_discoverability` is conditional.

When a published profile exists for exact channel/content_form:
- it becomes part of required current checks;
- report freezes profile ID/version/input hash;
- result is stored in ContentMasterCheckRun.

When no profile exists:
- the check is not required;
- UI reports `profile unavailable/not configured`;
- no generic SEO requirement is invented.

Do not create Draft-bound DiscoverabilityReport for Text Master v2.

Shared profile resolution logic MAY be refactored from current discoverability service.

---

# 22. Text checks runner

Existing Master check runner SHALL support schema-specific handlers.

Recommended organization:
- common F6A checks stay in core;
- `services/text_master_checks.py` handles v2 text-specific checks;
- adapter resolves the current required kinds;
- ContentMasterCheckRun remains the only persisted check record.

Latest exact input/profile result per kind governs readiness.

Warnings use the existing exact warning-disposition mechanism.

---

# 23. Structured Master diff

Add a Text Master diff service, recommended:

`services/text_master_diff.py`

Recommended API:

```text
GET /content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/text-diff?from_master_id=...
```

If `from_master_id` omitted, compare previous revision when available.

Response covers:
- added blocks;
- removed blocks;
- moved blocks;
- modified blocks;
- title change;
- asset reference changes;
- evidence/citation changes;
- accepted AI edit provenance;
- context changes separately.

No diff table.

Diff is bounded and read-only.

v1/v2 comparisons use deterministic v1 -> comparable projection but do not persist an upgrade.

---

# 24. Review v4 behavior for v2

Candidate v4 remains unchanged as the freeze envelope.

For `text.master.v2` Candidate:
- manifest `content` freezes structured v2 payload;
- manifest `render.body_markdown` is the deterministic readable projection;
- Preview uses frozen render, not current Master;
- Changes can include structured-document change metadata when comparing v2 Candidates;
- fallback text similarity may use frozen rendered Markdown only;
- Review never assumes payload contains editable `markdown`.

Historical v1/v2/v3/v4 behavior remains readable.

---

# 25. Local package behavior

The Text v2 adapter package projection outputs deterministic `content.md` from the exact Master render.

Optional future HTML is out of scope unless an existing deterministic renderer is explicitly reused without weakening the contract.

No package reads local editor state.

No package fallback to Draft.

---

# 26. Candidate readiness

A v2 Text Master may freeze only when:
- context current;
- document valid/non-empty;
- exact asset/evidence refs valid;
- exact deterministic render ready;
- all dynamically required checks current and acceptable;
- checks have current pass/warning results at Freeze; exact warning dispositions are required at Content Approval, as in F6A, not as a new pre-freeze state;
- channel/content form resolves.

AI suggestions are not required for readiness.

The absence of AI use is valid.

---

# 27. Frontend evidence flow

EvidencePanel:
- reads current exact boundary;
- loads bounded FactPack items;
- shows evidence_kind, statement/snapshot summary, rights readiness;
- supports bind to current text selection;
- creates document citation + exact evidence ref draft state atomically in the browser;
- unbind removes both from next save state;
- never edits FactPack from Text Studio.

If boundary changes, unsaved bindings are revalidated before save and server remains authoritative.

---

# 28. Frontend asset flow

Image/chart insertion:
- opens bounded Project Shared Assets picker;
- image block only accepts supported image MaterialRevision;
- chart block only accepts supported chart material;
- block insertion also adds exact asset ref with hash from server read model;
- removing the last use removes the draft ref from the next revision state;
- rights are visible before selection;
- server rechecks everything at save/freeze.

No web-search UI is added here; assets must already be in Project Shared Assets. Web discovery belongs to the asset acquisition flow/F6C+ integration work.

---

# 29. Frontend checks and readiness

TextChecksPanel shows:
- common checks;
- text-specific checks;
- exact status;
- current/stale;
- profile/provider coverage;
- warnings and dispositions;
- run-all action.

Saving a new revision clears currentness by definition; old checks remain history.

UI must not present a stale old pass as current.

---

# 30. Revision history UX

RevisionHistoryPanel:
- lists immutable Master revisions;
- current vs historical;
- schema v1/v2;
- source_kind;
- actor/time;
- AI-edit count;
- check/readiness summary;
- structured diff action.

Historical revision:
- read-only;
- can preview/diff;
- v1 can offer explicit upgrade/fork if it is current and unit mutable;
- no in-place edit.

---

# 31. Legacy Workspace boundary

`/workspace` and Draft APIs remain available for existing/legacy Topic workflows.

F6B MUST NOT:
- redirect all Draft editing into Production;
- change Draft save semantics;
- delete DraftClaim/DraftCheckRun;
- silently make Draft the Text Master truth again.

Shared TipTap helper refactors require legacy regression tests.

---

# 32. Authorization / archive safety

All Text APIs use existing Project/Unit ownership and archive boundaries.

Rules:
- foreign raw Master/FactPack/Material/LLMRun IDs disclose nothing;
- archived Project/Unit: read history/diff, no suggestion/save/check/upgrade;
- historical Master cannot be edited or used as base for a new suggestion when a newer current revision exists, unless operation is explicitly a read-only upgrade preview;
- suggestion endpoint requires editor/reviewer permissions consistent with content editing policy;
- save remains editor-authorized.

---

# 33. No migration target

F6B SHOULD require no schema migration.

Reuse:
- ContentMasterRevision
- ContentMasterAssetRef
- ContentMasterEvidenceRef
- ContentMasterCheckRun
- LLMRun

If implementation determines a durable new field/table is necessary:
- STOP;
- update proposal/design/spec/tasks;
- obtain explicit approval;
- only then add migration.

Do not repurpose Draft-specific tables for v2.

---

# 34. Recommended backend files

New:
- `services/text_documents.py`
- `services/text_master_checks.py`
- `services/text_master_ai.py`
- `services/text_master_diff.py`
- optional `routers/text_production.py` if text-specific routes should be separated cleanly

Modified:
- `services/production_modalities.py`
- `services/content_masters.py`
- `services/candidates_v4.py` only if render/content extraction needs schema dispatch
- `services/project_review_projection.py`
- `routers/content_masters.py` or new text router
- generation/discoverability helper modules only for reusable service extraction
- `main.py` router registration if new router

Avoid editing delivery/review approval semantics unless required for v2 display/package compatibility already covered by adapter.

---

# 35. Recommended frontend files

Replace/expand:
- `product/TextStudioShell.tsx`

New recommended:
- `product/text/TextDocumentEditor.tsx`
- `product/text/TextEditorToolbar.tsx`
- `product/text/textTiptapAdapter.ts`
- `product/text/EvidencePanel.tsx`
- `product/text/AISuggestionPanel.tsx`
- `product/text/IdentityPanel.tsx`
- `product/text/TextChecksPanel.tsx`
- `product/text/RevisionHistoryPanel.tsx`
- `product/text/TextRevisionDiff.tsx`
- optional hooks/types under `product/text/`

Modified:
- `ContentMasterPanel.tsx`
- `ModalityWorkspace.tsx`
- shared UI only where necessary
- bundle budget script/manifest checks

Legacy `pages/Workspace.tsx` should change only for safe shared helper extraction/regressions, not product migration.

---

# 36. FE-P1 / lazy loading

New professional Text editor dependencies SHALL be dynamically reachable only through the TextStudio lazy boundary; the existing legacy Workspace retains its own separate lazy TipTap boundary.

Requirements:
- `/projects` initial closure unchanged within existing 500k hard budget;
- common Production initial closure must not statically include TipTap;
- Graphic/Video Studio dynamic closures must not statically include TipTap;
- Text Studio may load TipTap on demand;
- record raw/gzip Text Studio and Production common baselines after implementation;
- do not invent a permanent Text chunk limit before measurement;
- existing route/chunk failure recovery remains.

---

# 37. Accessibility / editing safety

Text Studio SHALL provide:
- keyboard-accessible toolbar;
- semantic buttons/labels;
- visible selected text/AI action state;
- confirmation before discarding dirty edits on revision switch/reload/navigation where practical;
- screen-readable check/evidence status;
- no color-only warning semantics;
- keyboard alternative for block move/reorder if drag is added.

---

# 38. Required backend tests

At minimum:
1. v2 document validation per block type
2. duplicate/invalid stable IDs
3. inline mark normalization
4. link URL allowlist/bounds
5. embedded material undeclared ref rejected
6. embedded evidence undeclared ref rejected
7. citation locator invalid block/range rejected
8. citation/evidence locator mismatch rejected
9. project-visible image/chart exact refs
10. deterministic Markdown render
11. deterministic document hash
12. v1 adapter regression
13. adapter dispatch by payload schema
14. default new Text schema v2
15. v1 historical read/freeze compatibility
16. explicit v1->v2 preview
17. explicit v1->v2 append-only upgrade
18. upgrade idempotency/conflict
19. Draft seed produces v2 after F6B
20. Draft seed exact lineage still enforced
21. conversion warnings for unsupported/unmapped input
22. text_structure pass/warning/blocker
23. text_fact exact boundary input
24. text_fact no DraftClaim mutation
25. text_identity pinned snapshot input
26. unavailable semantic coverage not fake verified pass
27. text_platform exact channel/form rules
28. discoverability conditional requirement
29. no discoverability profile -> no invented required check
30. latest check authority / stale handling
31. AI suggestion authorization
32. AI suggestion archived denial
33. AI suggestion base hash conflict
34. AI working document bounds
35. rewrite patch validation
36. restructure patch validation
37. prompt-injection source treated as data
38. model-use rights respected for evidence
39. LLMRun provenance recorded
40. accepted AI edit provenance validation at save
41. fake LLMRun ID rejected/omitted
42. suggestion does not create Master
43. explicit save creates one Master
44. structured diff add/remove/move/modify
45. diff asset/evidence changes
46. v1/v2 diff bounded
47. v2 Candidate freeze
48. v2 Candidate Preview uses frozen render
49. v2 Candidate diff
50. v2 local package content.md
51. rights revocation still blocks
52. v4 approval/delivery regressions
53. archived history safety
54. foreign raw IDs denied
55. Draft/legacy Workspace regression
56. Graphic/Video F6A regression
57. F2–F6A full backend regression

---

# 39. Required frontend/browser acceptance

1. Open Text ContentUnit and see professional editor, not raw JSON.
2. Create heading/paragraph/quote/list/callout/code.
3. Reload unsaved/saved state behavior is truthful.
4. Save v2 Master; reload exact structure.
5. Reorder blocks and preserve IDs.
6. Insert exact project image.
7. Insert exact project chart.
8. Remove asset use and save new revision without deleting material.
9. Bind selected text to exact FactPackItem.
10. Remove citation/evidence binding.
11. Run Text checks and show current statuses.
12. Advance Fact Boundary and see stale/revalidation behavior.
13. AI rewrite suggestion preview -> reject leaves content unchanged.
14. AI rewrite suggestion preview -> accept changes local only.
15. Save after accepted AI edit -> new revision with verified provenance.
16. Expand/shorten/tone operations.
17. Restructure bounded block range.
18. stale suggestion cannot apply after local target changes.
19. identity panel shows pinned snapshot and cannot mutate it.
20. v1 current Master explicit upgrade preview + v2 fork.
21. old v1 revision remains unchanged/readable.
22. Draft workflow seed creates new v2 Master with exact provenance.
23. structured Master diff shows add/remove/move/modify.
24. freeze Candidate v4.
25. Review preview/diff/checks uses frozen v2 render/content.
26. Approve + local package contains deterministic content.md.
27. Workflow dirty/save remains independent.
28. Graphic/Video shells still function.
29. archived project/unit Text Studio read-only.
30. legacy `/workspace` TipTap still works.
31. direct refresh and chunk failure recovery.
32. no console errors.

---

# 40. Final gates

- full backend suite
- targeted F6B tests
- frontend TypeScript/Vite build
- FE-P1 bundle budget
- manifest verification that TipTap is absent from common Production/Graphic/Video initial graphs
- OpenSpec `--all --strict`
- relevant Ruff
- git diff --check
- isolated browser acceptance
- independent SPEC review
- independent backend/Text document/AI review
- independent frontend/editor/accessibility/performance review
- no production migration
- no push/deploy unless separately authorized

---

# 41. Completion definition

F6B is complete only when:

```text
ContentProject
→ Text ContentUnit
→ professional structured Text Studio
→ exact asset insertion
→ exact evidence/citation binding
→ optional AI suggestion + explicit accept
→ explicit text.master.v2 save
→ text-specific checks
→ structured Master diff
→ Candidate v4 freeze
→ Review
→ Approval
→ local package
```

and:
- IdentitySnapshot remains unchanged;
- Fact Boundary remains unchanged;
- ContentMemory remains unchanged;
- Workflow remains unchanged unless separately edited;
- historical Draft/text.master.v1/Candidates remain unchanged;
- Graphic/Video production behavior remains intact.

---

# 42. SPEC review calibration against main@ca52aa5

These are implementation boundaries, not additional product slices. All 162 tasks remain unexecuted. The original package and canonical specs remain unchanged during this review.

## 42.1 Locator units, repeated uses and edit safety

- Text offsets are zero-based, half-open Unicode scalar/code-point offsets into the exact canonical inline-text concatenation, excluding markup. They are not JavaScript UTF-16 offsets or ProseMirror positions. The browser adapter translates explicitly; invalid/unpaired surrogate input is rejected. No implicit NFC/NFKC normalization changes stored characters.
- Heading/paragraph/quote/callout locators use `block_id`; list items additionally use `list_item_id` and item-local text. Non-text-bearing image/chart/divider blocks cannot be cited. Code blocks are not selectable fact-citation targets in this slice.
- A citation and matching EvidenceRef locator include `citation_id`, block/item path, offsets, and a SHA-256 `selected_text_hash` over the selected UTF-8 text. The checksum of the FactPackItem remains in EvidenceRef. The same FactPackItem MAY appear at several distinct locations, with one ref per citation use; deduplicating by item ID alone is forbidden. Duplicate citation-use identities or conflicting locators are rejected.
- Editing before a range may deterministically remap offsets only while the selected text and its hash remain identical. Editing/deleting/restructuring the cited text must surface an invalidated binding and require explicit rebind/removal; syntactically in-bounds offsets alone do not prove the same claim. Save validates the exact document/ref correspondence atomically, and rejects unresolved/dangling bindings rather than silently retaining them.
- Asset declarations obey the existing 250-ref bound and payload JSON limits; a reused exact media revision may serve multiple blocks without duplicating bytes. Block placement uses bounded JSON, not a 150-character block ID squeezed into the 100-character slot_key column. Images require image-kind/renderable bytes; charts require chart-kind with a supported image render MIME, exact hash and rights. Metadata-only/non-renderable charts remain incomplete, never pretend to be an image.

## 42.2 Conversion, first save and schema compatibility

- Historical v1/Draft body is Markdown-authoritative. A contradictory composition `document_json` cannot supersede it. Unsupported Markdown/editor constructs are preserved as bounded text where possible with explicit lossy warnings; content cannot be discarded on an ordinary save without confirmation.
- Preview is read-only and may describe authorized history; upgrade commit requires the latest current mutable v1 parent, exact payload hash, revision CAS and context CAS. A retry replays the committed request before rereading later source/context; changed reuse of a key conflicts. Only the trusted upgrade service may set derived source provenance. Generic save cannot manufacture workflow/upgrade origins.
- The v2 default applies to an empty/new Text unit and verified new seed/explicit upgrade. Generic save MUST NOT bypass the explicit upgrade gate by posting v2 over a current v1 parent, nor silently downgrade a v2 head to v1. Existing v1-only save/freeze callers retain their declared legacy contract until an explicit upgrade.
- AI requires an authorized current saved v2 base. A new unsaved document with no base must first be explicitly saved; its AI buttons explain this prerequisite. No hidden initial save occurs. Archived/stale/historical bases reject suggestions, and context/base drift during a provider call makes the result stale rather than applicable.
- Refactor ALL persisted-schema call sites: serialization/readiness/check inputs, Versions/Overview, Candidate builder/live validator, from-output, Review and package. Modality-only defaults must never reinterpret a persisted v1 row. Unsupported versions fail closed.

## 42.3 Verifiable AI use without a new table

- Reuse LLMRun JSON for a bounded, server-generated versioned envelope containing Project/Unit/base Master ID + payload/context hashes, actor, working/before-document hash, operation/selection, validated patch/hash, deterministic after-document hash, canonicalization/patch versions and actual model/provider/prompt version. The server applies the validated patch once in memory before issuing it; it need not persist whole before-documents. Provider status success alone is insufficient: malformed/unsafe output is not eligible. Model-supplied provenance keys are ignored. Input hashing covers actual server-derived prompt/context and exact source refs, not arbitrary client owner IDs.
- The API authorizes Project/Unit/base before looking up or exposing run metadata. Missing/foreign/failed/legacy-unbound LLMRuns are ineligible. For multiple suggestions, only an ordered continuous hash chain (next before equals prior after) is eligible; its final after must equal the submitted canonical document hash. A forged patch/receipt cannot claim verified output.
- Save calculates the final document hash and records `verified_output_match` only when it equals the service-validated after hash (or the last hash of a continuous chain). This proves matching content, not a browser click or AI authorship of the entire document. Later manual edits or broken chains are explicitly labeled `subsequently_modified`/`issued` with warning or rejected as verified application; ordinary manual save remains possible. No arbitrary manual-edit proof engine is required.
- Retention may clear LLMRun parsed/raw output. Before save, a cleared receipt cannot satisfy a verified claim. Successful save freezes a compact server-generated receipt in existing edit_summary_json; immutable revision/Candidate provenance then reads the frozen receipt and does not depend on retained transient model output. No run is resurrected or falsely verified after purge.
- Evidence/asset content and excerpts sent to a real provider must meet live model-use eligibility, not merely public-use eligibility. Checks that omit forbidden content report coverage/omissions; they do not claim complete semantic review. Source/identity/brief text remains untrusted data. Mock calls are labeled mock, not real semantic verification.
- Patch application cannot introduce material/evidence IDs or dangling citations outside the locally declared exact refs. Replacing cited ranges invalidates/rebinds their uses explicitly; acceptance does not automatically assign old facts to new text. Provider failure persists truthful failed LLMRun metadata but no Master/check/Candidate.

## 42.4 Check versions and frozen packages

- Check requirement resolution freezes schema/adapter/renderer/check implementation and exact profile ID/version/checksum (or explicit unavailable state). Text discoverability matches an explicit published channel AND content_form; the existing legacy resolver's empty-channel/form fallback is not an exact F6B profile. Do not change that legacy fallback. Its input hash includes live model-use eligibility and coverage configuration where used. Profile/provider/rights changes invalidate current checks; no unavailable semantic execution is a full pass. Freeze accepts valid current pass/warning checks; Approval alone requires exact warning ID/input_hash dispositions, preserving F6A.
- Current save/freeze/approval/new authorization use current required profiles. Authorized historical package reads use the frozen schema/renderer/required-profile set and inputs, still enforcing live revocation/bytes/integrity and later blockers applicable to the same inputs. An unrelated new profile/default may not rewrite an old Candidate, and the old renderer must remain available or fail closed. Candidate reads/diffs remain historical projections, not re-rendered mutable context.
- v2 manifest citations SHALL extract exact `document.citations` into the frozen citation section and match each EvidenceRef locator/checksum; v1 top-level/structured extraction remains unchanged. Do not leave the v2 section empty merely because it is nested under document.
- v2 rendering specifies deterministic escaping, line breaks, supported mark nesting and citation labels. Media Markdown paths derive from the frozen ordered exact refs and match the ZIP media layout; no signed URL, private API URL, local path or raw evidence snapshot enters public `content.md`. Missing frozen v2 render or renderer/hash mismatch fails closed, never falls back to current Master, editable Markdown or Draft.
- TipTap and editor extensions remain absent from common Production/Graphic/Video static closures; preserve existing XYFlow isolation and the actual `<500,000` raw-byte gates. Text-only dynamic graph sizes are measured separately, not substituted for or exempted from existing common-route gates.

## 42.5 Zero-migration evidence and apply stop rule

Existing `ContentMasterRevision.payload_json/edit_summary_json`, `ContentMasterAssetRef.placement_json`, `ContentMasterEvidenceRef.content_locator_json`, `ContentMasterCheckRun.report_json/profile_*`, and `LLMRun.parsed_output_json/input_hash` provide the required storage. Column lengths and current API bounds apply to new metadata; no fake owner FK or DraftClaim persistence is introduced. This is a reviewed feasibility target, not implemented behavior. If actual implementation needs new durable columns/tables, stop and obtain a revised specification/authorization before any migration.
