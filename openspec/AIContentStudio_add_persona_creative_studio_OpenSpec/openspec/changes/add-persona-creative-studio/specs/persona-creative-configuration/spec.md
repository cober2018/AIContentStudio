## ADDED Requirements

### Requirement: Persona is the primary creative-default scope

Creative style, default methods and media-specific creative configuration SHALL belong to the frozen Content Identity hierarchy rather than the owning User. Persona SHALL be the normal creative root; Account and Series MAY explicitly replace a modality creative profile. Owner-scoped provider/model configuration and generic technical methods MUST NOT become an implicit creative style shared across Personas.

#### Scenario: One owner operates two Personas
- **WHEN** the same owner creates content for AI科技研发技术博主 and 日常生活方式博主
- **THEN** each Unit resolves its own Persona creative profile and no writing/visual/audio default from one Persona silently affects the other

### Requirement: Creative profiles reuse versioned identity JSON

The system SHALL support bounded `text_creative_profile`, `graphic_creative_profile`, `audio_creative_profile` and `video_creative_profile` fields in existing identity revisions. Missing fields inherit, explicit null clears, and a structured object override replaces the inherited modality profile as a whole. Effective values/origins SHALL freeze into IdentitySnapshot and its checksum.

#### Scenario: Account replaces Text creative profile
- **WHEN** Persona defines a Text creative profile and Account saves its own Text creative profile
- **THEN** the effective Account identity uses the complete Account object and reports Account as origin without hidden deep merge

#### Scenario: Historical snapshot after Persona edit
- **WHEN** Persona creative defaults advance after a Unit pinned an IdentitySnapshot
- **THEN** the historical Unit/Run/Master continues to expose the old frozen creative profile

### Requirement: Creative configuration supports auto custom and composed modes

Each modality creative profile SHALL use `auto`, `custom` or `composed` configuration mode.

- `auto` uses exact persona defaults plus existing executable capability routing;
- `custom` pins exact versioned Skill/Preset/Quality/model choices and fails closed when unavailable;
- `composed` uses one exact Studio built-in base method plus an explicit ordered list of exact Capability Memory revisions and optional explicitly executable Installed Agent Skill selections.

The resolver MUST NOT silently select or merge multiple applicable Capability Memory artifacts.

#### Scenario: Explicit custom model becomes unavailable
- **WHEN** a Persona custom Text profile pins a model profile that is no longer executable
- **THEN** readiness/execution is blocked unless the saved fallback policy explicitly allows normal configured routing

#### Scenario: Composed method order
- **WHEN** the user composes a built-in writer with two exact Persona Capability revisions
- **THEN** preview and execution preserve that explicit order and exact revision IDs

### Requirement: Resolution is deterministic and inspectable

Creative resolution SHALL apply hard Stage/rights/channel rules first, then run override, Project Workflow Stage config, frozen effective identity creative profile, built-in product fallback and finally only authorized provider-route fallback. Preview SHALL expose each source scope/revision/hash and the final method stack, style preset, quality profile, provider/model and fallback reason.

#### Scenario: Series-specific visual style
- **WHEN** a Series replaces its Graphic creative profile
- **THEN** a new Series-bound Unit preview shows the Series profile as the effective source while the Persona's historical/profile data remains unchanged

### Requirement: Two starter Persona blueprints are shipped

The product SHALL ship versioned starter blueprints `starter.ai-tech-engineer.v1` and `starter.lifestyle-observer.v1`. Blueprint preview is read-only. Explicit apply SHALL create ordinary ContentPersona revision/default Workflow records using existing services and SHALL persist blueprint key/version provenance inside the persona creative profile.

A same-name manually authored Persona MUST NOT be overwritten or silently treated as blueprint-owned. Reapplying an initialized blueprint MUST be idempotent/reviewable and MUST NOT reset later user edits without explicit action.

#### Scenario: Initialize both starter personas
- **WHEN** an authorized owner explicitly applies both starter blueprints in an empty identity tree
- **THEN** two independent normal Personas and their default recipes are created with exact blueprint provenance and no new identity truth table

### Requirement: Starter AI technology persona has engineering defaults

`starter.ai-tech-engineer.v1` SHALL encode engineering-first positioning, AI Agent/software-architecture domains, evidence/trade-off orientation, low-hype expression, technical-editorial/diagram-first visual defaults and calm-clear technical audio defaults. Its default methods SHALL avoid marketing-style exaggeration and require truthful evidence/time boundaries for factual claims.

#### Scenario: Technology Persona Text preview
- **WHEN** a new Text Unit uses the starter AI technology Persona
- **THEN** Effective Preview identifies the deep-technical Text preset, technical quality profile and versioned built-in methods from that Persona snapshot

### Requirement: Starter lifestyle persona has observational defaults

`starter.lifestyle-observer.v1` SHALL encode current/near-future interesting topics, everyday observations/reflections, warm conversational expression, non-preachy/non-clickbait boundaries, warm-magazine/documentary-photo visual defaults and warm conversational audio defaults. Current factual claims MUST require fresh evidence; future speculation MUST remain explicitly distinct from confirmed facts.

#### Scenario: No fresh source for current event
- **WHEN** the lifestyle Persona asks to discuss a current event but the production context contains no qualifying fresh source
- **THEN** the system does not present stale model knowledge as verified current fact and instead blocks that claim or switches only by explicit user choice to reflection/speculation mode
