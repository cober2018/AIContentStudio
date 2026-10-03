## ADDED Requirements

### Requirement: Graphic v2 is a structured multi-canvas content model
The system SHALL support `graphic.master.v2` with stable canvas and layer IDs. Visible text, image/chart references, geometry, order and canvas dimensions are content and SHALL be versioned in ContentMasterRevision.

### Requirement: Graphic embedded media uses exact MaterialRevision refs
Every image/chart layer SHALL reference a project-visible exact MaterialRevision also declared through ContentMasterAssetRef. Raw URLs/paths/bytes MUST NOT bypass the asset contract.

### Requirement: Graphic text is approved content
Text-on-image SHALL participate in Candidate hash, Review and final render. Publisher/renderer MUST NOT silently rewrite approved text.

### Requirement: Graphic rendering is input-bound
Final render output SHALL bind exact graphic payload/context/assets/evidence through render-input hash. Every canvas must have exact output coverage before Candidate freeze.

### Requirement: Graphic Studio supports professional multi-canvas editing
The frontend SHALL support canvas creation/reorder/duplicate, text/image/chart layers, bounded geometry, project assets, channel size presets, revision history and structured diff.

### Requirement: Graphic provider output becomes MaterialRevision before use
Search/generation/variation outputs SHALL be materialized with provenance, rights and hash before they can enter a canvas. Unverified capability MUST remain unavailable.

### Requirement: Graphic checks are schema-aware
Graphic v2 SHALL use structure, identity/text, platform, rights/evidence and render checks with exact currentness semantics.

### Requirement: Graphic history remains compatible
Historical `graphic.master.v1` and old v4 Candidates SHALL remain readable and hash-stable; professional editing from v1 requires an explicit append-only v2 fork.
