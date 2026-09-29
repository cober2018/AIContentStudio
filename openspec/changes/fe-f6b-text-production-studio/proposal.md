## Why

FE-F6A completed the shared Production Core and made ContentMasterRevision the durable production root for Text, Graphic and Video. The Text modality is still only a minimal JSON shell: `TextStudioShell` edits a raw `text.master.v1` payload, while the richer TipTap editor, selection rewrite, DraftClaim/fact-check, and Markdown/document composition remain in the legacy Draft workspace.

The product strategy requires Text to be a first-class professional Production Engine rather than a Markdown textarea. New Text production must preserve exact IdentitySnapshot, CreativeBrief, Fact Boundary, assets, evidence, model/runtime provenance and immutable revisions while remaining compatible with legacy Draft and `text.master.v1` history.

F6B therefore introduces a structured Text Studio on top of the F6A core without creating a second production/version/review system.

## What Changes

- Add `text.master.v2` as the default schema for new professional Text Studio revisions.
- Make a Studio-owned structured Text Document the authoritative content model for v2; Markdown becomes a deterministic render/export projection rather than a second editable truth.
- Keep `text.master.v1`, Draft, Draft.document_json, MotherRevision and historical Candidates readable and hash-stable.
- Add explicit v1/Draft-to-v2 conversion/fork behavior; never rewrite historical revisions in place.
- Reuse TipTap as a frontend editing engine through a Studio document adapter; ProseMirror/TipTap JSON is not persisted as the backend contract.
- Add stable document blocks: heading, paragraph, quote, bullet/ordered list, callout, code, image, chart and divider.
- Bind image/chart blocks only to exact project-visible MaterialRevision references already frozen through ContentMasterAssetRef.
- Bind citations/evidence to exact FactPackItem references and stable block/range locators through ContentMasterEvidenceRef.
- Add text-specific Master checks: structure, fact, identity, platform and conditional discoverability, persisted in ContentMasterCheckRun.
- Add AI editing suggestions for rewrite, expand, shorten, tone change and restructure. Suggestions never mutate a Master automatically; users explicitly accept a local patch and explicitly save a new Master revision.
- Validate AI provenance against persisted LLMRun input/output metadata without adding a suggestion table.
- Add structured Master revision diff for block/content/asset/evidence/AI-edit changes.
- Update v4 Text Candidate preview/diff/package behavior to render from the exact frozen structured document.
- Keep Workflow editing and Text editing as independent dirty/save states.
- Preserve Graphic/Video Studio shells and F6A common Production behavior.
- Keep TipTap in a TextStudio-specific lazy chunk so common Production, Graphic and Video initial dependency graphs remain free of TipTap.
- Target zero new database tables/migrations. If implementation proves a migration is unavoidable, stop and amend the specification before applying it.

## Capabilities

### New Capability

- `text-production-studio`: structured Text Master v2, professional editor behavior, exact evidence/asset binding, AI suggestion flow, text-specific checks, schema upgrade, structured diff and browser acceptance.

### Modified Capabilities

- `production-content-master`: schema-versioned Text adapters, v2 deterministic render/package, Draft seed/v1 upgrade compatibility, dynamic text check requirements.
- `fe-f4-project-review-distribution`: Text v2 Candidate preview/diff uses the frozen structured document and deterministic render without assuming editable Markdown exists in the payload.
- `fe-p1-frontend-bundle-performance`: TipTap may load only inside the Text Studio dynamic boundary and must not regress common Production/Graphic/Video initial loading.

## Impact

Backend:
- new Text Document validation/render/conversion/diff services;
- schema-aware Text adapter dispatch (`text.master.v1` and `text.master.v2`);
- new project-scoped text suggestion and explicit upgrade APIs;
- text-specific checks using existing ContentMasterCheckRun and existing generation/fact/rule infrastructure;
- no replacement Draft or review tables.

Frontend:
- replace the Text JSON textarea with a professional structured editor;
- project asset insertion, evidence binding, AI suggestion diff, identity/check panels and Master revision diff;
- legacy `/workspace` remains compatible and lazy.

Review/Delivery:
- existing Candidate v4, Approval, Delivery Authorization and local package contracts remain authoritative;
- v2 content is frozen as structured payload plus deterministic rendered Markdown.

This change does not implement Graphic/Video professional editors, cross-modality/channel adaptation, new connectors, new remote publishers, production auth/tenancy, or deployment work.
