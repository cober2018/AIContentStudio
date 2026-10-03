## ADDED Requirements

### Requirement: Text Master v2 uses a Studio-owned structured document as the only editable truth

New professional Text production SHALL use `text.master.v2` whose authoritative content is a bounded Studio Text Document. Editable Markdown or TipTap/ProseMirror JSON MUST NOT be persisted as a second truth. Markdown SHALL be a deterministic render/export projection.

#### Scenario: Save professional Text content
- **WHEN** an editor saves a valid v2 Text document
- **THEN** the new ContentMasterRevision stores the structured document and exact refs, while Markdown is derived by the server renderer

#### Scenario: Client submits editable v2 Markdown
- **WHEN** a v2 save attempts to persist an independent editable `markdown` field
- **THEN** the server rejects the dual-truth payload rather than choosing one silently

### Requirement: Text document blocks are stable, portable and editor-independent

The Studio Text Document SHALL use stable block/item IDs and an explicit schema independent of TipTap. F6B SHALL support heading, paragraph, quote, bullet list, ordered list, callout, code, image, chart and divider blocks, plus bounded inline marks. Unknown editor-specific nodes MUST NOT be silently persisted.

#### Scenario: Reorder a block
- **WHEN** the user moves an existing paragraph to a new position
- **THEN** its stable block ID remains unchanged in the saved revision

#### Scenario: Unsupported editor node
- **WHEN** the frontend editor contains a node or mark outside the Studio schema
- **THEN** save is blocked or the unsupported content is explicitly surfaced before persistence rather than silently discarded

### Requirement: Text rendering is deterministic

The backend SHALL canonically validate and render `studio.text.document.v1` into Markdown and plain-text projections. Identical documents SHALL produce identical render output and hashes independent of JSON key order or browser/editor implementation.

#### Scenario: Repeat render
- **WHEN** the same canonical v2 document is rendered twice
- **THEN** Markdown and render content hash are identical

### Requirement: Text image and chart blocks use exact project-visible asset references

Image and chart blocks SHALL embed only exact MaterialRevision IDs and MUST be backed by corresponding ContentMasterAssetRef rows for the same revision. The server SHALL validate project visibility, type, hash and rights through Production Core; no file path or copied bytes belong in the Text document.

#### Scenario: Insert project image
- **WHEN** the user inserts a project-visible image revision into a Text document
- **THEN** the document block references its MaterialRevision and the next Master stores the exact ContentMasterAssetRef without copying bytes

#### Scenario: Raw foreign material ID
- **WHEN** a document embeds a MaterialRevision absent from declared authorized refs
- **THEN** save is rejected without attaching or disclosing it

### Requirement: Text citations bind exact evidence to stable document locators

Citations SHALL bind a FactPackItem to an exact text-bearing block and bounded character range. The same evidence use SHALL exist as a ContentMasterEvidenceRef with matching locator and snapshot checksum. Citation editing MUST NOT mutate the FactPack or Fact Boundary.

#### Scenario: Bind selected text to evidence
- **WHEN** a user selects a valid range and chooses an item from the current exact Fact Boundary
- **THEN** the local document citation and evidence-ref draft state point to the same block/range and exact FactPackItem

#### Scenario: Citation range becomes invalid
- **WHEN** the cited block/range does not exist in the submitted canonical document
- **THEN** save is rejected rather than preserving a dangling citation

### Requirement: Text Studio uses the exact Project Fact Boundary

The Evidence panel SHALL read the ContentProject's current Project Fact Boundary and its frozen FactPack items. It MUST NOT substitute a global/unrelated FactPack or change the boundary from inside Text Studio.

#### Scenario: Boundary changes while editing
- **WHEN** the project Fact Boundary advances before save
- **THEN** the server rejects or marks stale incompatible evidence bindings under the existing context/CAS rules and history remains unchanged

### Requirement: TipTap is a lazy UI engine, not the backend contract

The Text Studio MAY use TipTap for editing, but Studio Document ↔ TipTap conversion SHALL occur at the frontend boundary. Persisted payloads SHALL contain Studio Text Document data only.

#### Scenario: Replace the UI editor implementation
- **WHEN** a future editor engine produces the same Studio document
- **THEN** the backend schema, hashes, Candidate and Review contracts do not change

### Requirement: Text edits are local until explicit Master save

Typing, formatting, asset insertion, citation binding and accepted AI patches SHALL modify local Text Studio state only. A durable ContentMasterRevision SHALL be created only on explicit save through the Production Core append-only API.

#### Scenario: Accept AI suggestion without saving
- **WHEN** a user accepts a suggestion and navigates within the current dirty editor state without saving
- **THEN** no new Master revision, check or Candidate is created

#### Scenario: Save after edits
- **WHEN** the user explicitly saves the valid current editor state
- **THEN** exactly one new immutable v2 Master revision is created under the existing idempotency/CAS rules

### Requirement: Historical Text v1 stays immutable and upgrades explicitly to v2

`text.master.v1` SHALL remain readable/freezeable under its historical contract. Continuing professional editing from a current v1 Master SHALL require explicit v2 upgrade/fork that creates a new revision. No v1 revision or historical Candidate may be rewritten.

#### Scenario: Preview v1 upgrade
- **WHEN** the user requests upgrade preview for a current v1 Master
- **THEN** the server returns a deterministic proposed v2 document and conversion warnings without mutation

#### Scenario: Commit v1 upgrade
- **WHEN** the user explicitly accepts the upgrade with current expected revision/hash
- **THEN** a new v2 child revision is created and the v1 parent remains unchanged

### Requirement: New Draft workflow seeds create v2 Text Masters

After F6B, the existing verified Draft ProjectWorkflowOutput seed path SHALL create `text.master.v2` for new Text seeds while retaining exact Draft/Run/Step/Attempt provenance. Historical v1 seed revisions remain unchanged.

#### Scenario: Seed a new Text Master from Draft
- **WHEN** a current verified Draft output is seeded after F6B
- **THEN** the server deterministically converts content/refs into v2 and preserves truthful source lineage and conversion warnings

### Requirement: AI editing returns suggestions and never mutates Master automatically

Text Studio SHALL support rewrite, expand, shorten, tone and restructure operations through a project-scoped suggestion API. The server SHALL authorize the base Master, validate the supplied working document, derive selected context server-side, invoke the configured rewrite route and return a bounded validated patch without writing a Master.

#### Scenario: Generate rewrite suggestion
- **WHEN** an editor requests rewrite for a valid selection
- **THEN** the response contains a validated patch and LLMRun provenance while the persisted Master count is unchanged

#### Scenario: Reject suggestion
- **WHEN** the user rejects the returned patch
- **THEN** local and persisted content remain unchanged

### Requirement: AI suggestions are input-bound and stale-safe

A suggestion SHALL bind the authorized base Master, base payload hash, working document hash, operation and selection. A patch MUST NOT apply silently after the local target changes.

#### Scenario: Local content changes after request
- **WHEN** the target block/range no longer matches the suggestion input
- **THEN** the UI refuses direct apply and requires a new suggestion

### Requirement: Accepted AI provenance is verifiable without a new suggestion table

AI calls SHALL record LLMRun. Accepted AI edit metadata included in a later Master save SHALL be trusted only when the server can verify the LLMRun status, purpose, project/unit/base provenance, input hashes and returned patch hash. Arbitrary client-provided model/run IDs MUST NOT become frozen provenance.

#### Scenario: Fake LLMRun ID
- **WHEN** a save claims an unrelated or failed LLMRun as an accepted AI edit
- **THEN** the claimed provenance is rejected or excluded from trusted edit history

### Requirement: Text-specific checks persist in ContentMasterCheckRun

Text v2 SHALL use schema-aware Master checks in the existing ContentMasterCheckRun system. Required checks SHALL include structure, fact, identity and platform in addition to common Production Core checks. Discoverability SHALL be required only when an exact published profile exists for channel/content form.

#### Scenario: Save new Text revision
- **WHEN** a v2 revision is created after previous checks passed
- **THEN** prior check history remains but none is current for the new revision until rerun

### Requirement: Text fact checking uses Master evidence and does not create DraftClaim

`text_fact` SHALL evaluate the v2 content against the exact Master Fact Boundary and evidence snapshots, reusing/refactoring fact-check logic without creating or mutating Draft, DraftClaim or DraftCheckRun rows.

#### Scenario: Run v2 fact check
- **WHEN** the user runs checks on a current v2 Master
- **THEN** results are persisted only as ContentMasterCheckRun and issue locators refer to the Text document where deterministically possible

### Requirement: Text identity checking uses the pinned IdentitySnapshot without mutating identity

`text_identity` SHALL read the exact Master-pinned IdentitySnapshot and surface explicit deterministic/semantic coverage. Missing semantic capability MUST NOT be represented as a fully verified pass, and Text Studio SHALL never change Brand/Persona/Account/Series identity settings.

#### Scenario: Identity provider unavailable
- **WHEN** semantic identity review cannot execute
- **THEN** coverage is reported truthfully under warning/incomplete semantics instead of fabricating a verified pass

### Requirement: Text platform and discoverability checks use registered channel truth

`text_platform` SHALL resolve exact Channel Registry content-form rules. `text_discoverability` SHALL run only when an exact published profile resolves. Missing rules/providers MUST NOT be silently treated as successful execution.

#### Scenario: No discoverability profile
- **WHEN** no published discoverability profile exists for the exact channel/content form
- **THEN** discoverability is labeled unavailable/not configured and is not invented as a required SEO gate

### Requirement: Text Master revision diff is structured and read-only

The system SHALL provide a bounded on-demand Text Master diff without adding a diff table. For v2 it SHALL identify block add/remove/move/modify plus title, asset, citation/evidence and accepted-AI provenance changes. Context changes SHALL be reported separately from content changes.

#### Scenario: Move unchanged paragraph
- **WHEN** a paragraph keeps its stable ID/content but changes order
- **THEN** diff reports a move rather than delete-plus-add

### Requirement: Text v2 Candidate/Review uses frozen structured content and deterministic render

Candidate v4 SHALL freeze the v2 structured payload plus deterministic render. Review Preview and local package SHALL use the frozen render rather than current editor state. Review MUST NOT require an editable `content.markdown` field to exist in v2 payload.

#### Scenario: Open frozen v2 Candidate after later edits
- **WHEN** a newer Master revision exists
- **THEN** Review shows the Candidate's original frozen structured content/render and hash, not the newer editor state

### Requirement: Text Studio preserves Production and legacy boundaries

Workflow dirty/save, Text Master dirty/save, Review decisions and legacy Draft editing SHALL remain distinct. F6B MUST NOT silently modify Workflow, Identity, Fact Boundary, ContentMemory, historical Draft or historical Master data.

#### Scenario: Save Text Master while Workflow draft is dirty
- **WHEN** the user saves Text content
- **THEN** the Workflow unsaved state remains unsaved and unchanged

### Requirement: Text Studio authorization and archive behavior are project-scoped

All Text-specific read/write/suggestion/upgrade/diff routes SHALL reuse Project/Unit authorization. Archived Projects/Units keep authorized history/diff reads but reject suggestion, upgrade, checks and new saves. Raw foreign IDs disclose nothing.

#### Scenario: Archived Text unit
- **WHEN** an authorized user opens its Text Studio
- **THEN** historical content/diff is readable but editing, AI suggestion, check and save actions are disabled/rejected
