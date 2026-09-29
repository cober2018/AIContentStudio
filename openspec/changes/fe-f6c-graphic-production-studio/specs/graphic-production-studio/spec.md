## ADDED Requirements

### Requirement: Graphic v2 is a bounded multi-canvas content document
The system SHALL persist `graphic.master.v2` as ordered canvases with stable canvas and layer IDs, bounded dimensions/geometry, text/image/chart/shape layers and deterministic canonical hashing. A canvas variant MAY point to an existing same-document source canvas by stable ID, but SHALL remain independently versioned content. Visible text, placement, order and styles SHALL be content. Unknown layers, non-finite geometry, raw bytes and infrastructure URLs/paths MUST be rejected.

The new Graphic Studio SHALL explicitly submit v2; legacy API writes without a schema marker SHALL retain Graphic v1 semantics rather than silently rewriting historical callers.

#### Scenario: Save a valid multi-canvas revision
- **WHEN** an editor explicitly saves two canvases with unique stable IDs and bounded ordered layers
- **THEN** one append-only Master revision stores the canonical document/hash and a reload returns the same order and content

#### Scenario: Invalid layer data
- **WHEN** a layer contains an unknown type, non-finite coordinate or local storage path
- **THEN** save is rejected without a partial Master, ref or event

#### Scenario: Duplicate as a variant
- **WHEN** an editor duplicates a canvas as a variant and then changes its text or layout
- **THEN** the new canvas has a distinct stable ID, records its source canvas ID and freezes its own content and final render independently

### Requirement: Graphic layer media is an exact project-visible reference
Every image/chart layer SHALL bind an exact project-visible MaterialRevision ID and hash through a matching ContentMasterAssetRef. Repeated placement of one revision SHALL use distinct layer IDs and placement refs without copying bytes. Revoked, foreign, wrong-kind or mismatched revisions MUST NOT pass save/freeze/approval/package gates.

#### Scenario: Reuse one image on two canvases
- **WHEN** two distinct layers use the same valid MaterialRevision
- **THEN** two exact placement refs are stored, each bound to its canvas/layer, and both survive reload

#### Scenario: Foreign or revoked media
- **WHEN** a layer references a raw global or now-revoked MaterialRevision
- **THEN** the applicable save or live action fails without expanding project visibility

### Requirement: Graphic visible text and claims remain approval content
Text-layer runs and styles SHALL enter Master/Candidate/render hashes, structured diff and Review. Claims SHALL bind exact current FactPackItem evidence with a canvas/layer/range locator when evidence is asserted. A semantic checker MUST report unavailable or partial coverage when no trusted provider can evaluate meaning; it MUST NOT convert deterministic structure validation into semantic pass.

#### Scenario: Change approved-looking text
- **WHEN** a text layer changes after a final render was attested
- **THEN** the render binding becomes invalid and a new Candidate cannot freeze from the changed Master without new checks/render

#### Scenario: Missing semantic coverage
- **WHEN** model-based identity or claim checking is unavailable
- **THEN** the result explicitly reports unavailable/partial coverage rather than verified semantic consistency

### Requirement: Graphic channel rules use an exact image-classified profile
Canvas presets and mandatory media/dimension limits SHALL come from the published exact channel/content-form profile. The Studio SHALL show the resolved profile and SHALL NOT silently rewrite manually valid dimensions or reclassify a legacy text-classified form as Graphic.

The optional exact-form `graphic_requirements` contract SHALL distinguish mandatory `min_canvases`, `max_canvases`, `allowed_dimensions`, `cover_required` from suggestion-only `presets`. A required cover SHALL use an explicit first-canvas `role=cover`; absence of a declared rule SHALL NOT invent a restriction. Unknown or invalid rule configurations MUST NOT be treated as passing checks.

#### Scenario: Exact image profile
- **WHEN** an image-classified profile declares canvas count, dimensions or cover requirements
- **THEN** Graphic checks use those exact rules and the UI offers matching presets without changing saved canvases silently

#### Scenario: Legacy text-classified form
- **WHEN** a Graphic Unit selects a content form currently classified as text
- **THEN** Graphic Candidate freeze remains unavailable; F6C does not infer image support from the channel name

### Requirement: Every Graphic canvas has input-bound final bytes
Graphic Candidate readiness SHALL require one real image MaterialRevision per canvas, mapped in canonical canvas order, with exact byte/hash/MIME/live-rights checks and an attestation or verified renderer lineage bound to the canonical render-input hash. The hash SHALL exclude final render refs but include all canvases, non-render assets, evidence and context. A manual attestation SHALL be labelled manual, not verified renderer output.

#### Scenario: Unverified renderer claim
- **WHEN** no project renderer capability has been verified and a client submits renderer-origin attestation
- **THEN** the API rejects the claim as unavailable without creating a new Master revision; the Studio shows automatic rendering as unavailable

#### Scenario: Multi-canvas package
- **WHEN** all canvases have distinct exact output revisions and valid input-bound attestation
- **THEN** Candidate v4 freezes their ordered bindings and the local package contains those exact bytes in canvas order

#### Scenario: Stale or incomplete render
- **WHEN** canvas text/order/assets/context change or one output is missing/wrong-kind
- **THEN** render readiness and freeze fail closed without substituting an unrelated image

### Requirement: Graphic checks and revision diff are schema-aware
Graphic v2 SHALL use append-only input-bound structure, text/fact/identity, exact profile, evidence, rights and render checks. Revision and Candidate Review diff SHALL report canvas/layer add/remove/move/resize, visible text, exact asset/evidence and render changes without inventing whole-graphic text similarity.

#### Scenario: Reorder and change a text layer
- **WHEN** two revisions differ in canvas order and one text layer
- **THEN** the diff names both changes by stable IDs and Review presents the frozen rendered content and current check status

### Requirement: Graphic provider hooks cannot fake capability or rights
Search/generation/variation controls SHALL report configured/executable/verified availability truthfully. A selected or generated image SHALL become a MaterialRevision with exact bytes, source/provider/version/prompt and rights provenance and an explicit project reference before a canvas can use it. Provider success alone MUST NOT grant public or commercial use.

#### Scenario: Disconnected provider
- **WHEN** no executable provider is configured
- **THEN** the Studio/API reports unavailable and creates no fake MaterialRevision or generated image

#### Scenario: Accepted provider result
- **WHEN** a configured provider returns real bytes and a user accepts them
- **THEN** a versioned MaterialRevision with provenance is created and rights remain subject to explicit live validation

### Requirement: Graphic Studio is a professional but bounded editor
The Graphic-only frontend SHALL support canvas create/duplicate/delete/reorder, stage zoom/selection, text/image/chart/shape layers, bounded geometry, layer order/visibility/lock, exact project asset selection, history/diff/check/readiness and explicit Master save. Workflow dirty/save SHALL remain independent. Historical/archived content SHALL be read-only.

#### Scenario: Edit and reload
- **WHEN** an editor changes two canvases and explicitly saves
- **THEN** a new Graphic v2 Master revision appears and reload preserves the canvases/layers without changing Workflow draft state

#### Scenario: Archived Unit
- **WHEN** an archived Graphic Unit is opened
- **THEN** history and frozen output remain readable while save, run, render confirmation and layer edits are disabled

### Requirement: Graphic v1 history upgrades only by explicit fork
Historical `graphic.master.v1` Masters/Candidates SHALL remain hash-stable and readable. Editing a current v1 Master as v2 SHALL require an explicit preview and CAS/idempotent append-only fork; generic save MUST reject schema crossing. Unprovable conversion SHALL warn or block, not fabricate layer/ref lineage.

#### Scenario: Explicit current-v1 upgrade
- **WHEN** the current v1 Master has a provably convertible canvas and the editor confirms a fresh upgrade preview
- **THEN** a new v2 child revision is created and the v1 parent remains unchanged

#### Scenario: Stale upgrade
- **WHEN** a concurrent Master/context change invalidates the upgrade preview
- **THEN** the fork returns conflict and creates no partial revision
