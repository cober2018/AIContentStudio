# persona-creative-configuration Specification

## Purpose
Keep versioned creative defaults rooted in each Persona with explicit whole-profile Account/Series overrides and truthful configuration readiness.
## Requirements
### Requirement: Persona is the primary creative-default scope

Creative style, default methods and media-specific creative configuration SHALL belong to the frozen Persona creative hierarchy rather than the owning User or Brand. Persona SHALL be the normal creative root; Account and Series MAY explicitly replace a modality creative profile. Brand constraints MAY enter Effective Context, but Brand MUST NOT provide an inherited Studio Skill, Style Preset, Quality Profile, Recipe, voice/graphic/writing style or creative method stack. Owner-scoped provider/model configuration and generic technical methods MUST NOT become an implicit creative style shared across Personas.

#### Scenario: One owner operates two Personas
- **WHEN** the same owner creates content for AI科技研发技术博主 and 日常生活方式博主
- **THEN** each Unit resolves its own Persona creative profile and no writing/visual/audio default from one Persona silently affects the other

#### Scenario: Two Personas under one Brand
- **WHEN** one Brand owns a technical Persona and a lifestyle Persona, and the Brand defines brand voice or boundary constraints
- **THEN** both Personas apply the applicable Brand constraints, but neither Persona inherits a Skill, Style Preset, Quality Profile, Recipe or creative method default from Brand

### Requirement: Creative profiles reuse versioned identity JSON

Persona/Account/Series revisions SHALL support bounded `text_creative_profile`, `graphic_creative_profile`, `audio_creative_profile` and `video_creative_profile` fields. Brand revisions MUST reject these fields as creative configuration. Within the creative hierarchy, missing fields inherit, explicit null clears, and a structured object override replaces the inherited modality profile as a whole. Effective values/origins SHALL freeze into IdentitySnapshot and its checksum, while Brand constraints remain separately identifiable context.

#### Scenario: Account replaces Text creative profile
- **WHEN** Persona defines a Text creative profile and Account saves its own Text creative profile
- **THEN** the effective Account identity uses the complete Account object and reports Account as origin without hidden deep merge

#### Scenario: Historical snapshot after Persona edit
- **WHEN** Persona creative defaults advance after a Unit pinned an IdentitySnapshot
- **THEN** the historical Unit/Run/Master continues to expose the old frozen creative profile

### Requirement: Audio profiles use the shared multimedia surface and exact voice bindings

Audio creative profiles SHALL use the unified image/audio generation surface defined by this change. They MAY select a user-facing `VoicePreset` or an exact provider/model/profile-scoped binding, but the effective provider, model, profile, `voice_id`, rate and adapter-supported parameters SHALL be frozen in the IdentitySnapshot and execution receipt. This is a single-user local catalog: no voice ownership, sharing ACL or multi-tenant isolation is introduced. A cloned voice is selectable only after its exact provider-scoped ID is registered and verified when the adapter requires verification.

The normal Audio UI SHALL show the selected preset and bounded common controls. An explicit Advanced Settings action SHALL reveal the exact binding and only adapter-declared fields. A catalog with hundreds of voices SHALL provide search, language/style filters, favorites and preview. Labels and preview audio are explanatory metadata, not identity.

#### Scenario: Persona voice and image/audio surface stay explicit
- **WHEN** the same Persona uses the shared multimedia surface for a Graphic Stage and an Audio Stage
- **THEN** each Stage shows its own adapter-supported controls and exact binding receipt, while neither Stage silently changes the other modality's provider/model/profile or voice configuration

#### Scenario: Exact cloned voice is unavailable
- **WHEN** a Custom Audio profile pins a missing, mismatched or disabled cloned voice ID
- **THEN** Audio readiness/execution blocks and does not substitute another voice or provider

### Requirement: Creative configuration supports auto custom and composed modes

Each modality creative profile SHALL use `auto`, `custom` or `composed` configuration mode.

- `auto` uses exact persona defaults plus existing authorized executable capability-routing fallback;
- `custom` pins one exact versioned Skill/Preset/Quality/provider/model/profile binding and fails closed when that binding is unavailable or changes;
- `composed` (shown as Custom Composition) uses one exact Studio built-in base method plus an explicit ordered list of exact Capability Memory revisions, optional explicitly executable Installed Agent Skill selections, and MAY declare an explicit ordered fallback chain of exact provider/model/profile bindings.

The resolver MUST NOT silently select or merge multiple applicable Capability Memory artifacts, discover undeclared providers, or substitute an undeclared provider/model/profile. A declared Composed fallback chain MUST be visible before execution and frozen into the attempt receipt.

#### Scenario: Explicit Custom model becomes unavailable
- **WHEN** a Persona Custom Text profile pins one exact provider/model/profile binding that is no longer executable
- **THEN** readiness/execution is blocked and no other provider/model/profile is selected

#### Scenario: Custom Composition uses its declared fallback
- **WHEN** the primary binding in a Persona Custom Composition is unavailable and the next exact binding in its saved ordered chain is executable
- **THEN** execution selects that declared next binding, shows the chain in Effective Preview, and records the selected binding plus bounded fallback reason in the attempt receipt

#### Scenario: Composed method order
- **WHEN** the user composes a built-in writer with two exact Persona Capability revisions
- **THEN** preview and execution preserve that explicit order and exact revision IDs

#### Scenario: Deterministic composed methods consume typed Stage parameters only
- **WHEN** a composed Graphic Stage selects a built-in deterministic layout method and ordered Capability Memory revisions
- **THEN** each selected revision is usable by that Stage only when it resolves to a matching `workflow.stage.recipe.v1` with a typed `config_patch` accepted by the exact Stage Contract
- **AND** patches apply in declared order as creative-profile defaults, saved Project Stage fields override those defaults, the explicit run override applies last, and preview/receipt freeze every source revision and content/arguments/metadata/rendered hash plus the final effective config
- **AND** an extension cannot replace the built-in method or output/package/model/provider selectors; the final selected method is validated against the final overridden output or Director package schema
- **AND** readiness applies the same matching-recipe checks to every participating deterministic node across Graphic, Audio and Video, and reports blocked when actual execution would block
- **AND** free-form instructions, unsupported fields and undeclared AI/provider behavior block the deterministic Stage rather than changing layout or calling a provider implicitly

#### Scenario: AI transformation is an explicit Stage
- **WHEN** a method requires semantic rewriting or model-assisted transformation that cannot be represented by the current deterministic Stage Contract
- **THEN** the resolver requires a visible explicit AI Stage and the deterministic layout/render Stage does not invoke a hidden provider

### Requirement: Resolution is deterministic and inspectable

Creative resolution SHALL apply hard Stage/rights/channel rules first, then run override, Project Workflow Stage config and the frozen effective identity creative profile. Auto mode MAY then use built-in product and authorized provider-route fallback; Custom single-binding mode MUST block on an unavailable exact binding; Composed/Custom Composition mode MUST use only its declared ordered binding chain. Preview SHALL expose each source scope/revision/hash and the final method stack, style preset, quality profile, exact binding or declared binding chain and fallback reason.

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

### Requirement: Production stages expose ordered independent creative Skill controls
The existing creative hierarchy SHALL support multiple exact Skill/method references per production stage, ordered execution, editable compatible parameters, individual enabled flags and a stage-level creative-Skill switch. Missing new fields SHALL preserve legacy behavior. Existing whole-profile replacement and snapshot semantics SHALL remain unchanged. Stage overrides SHALL remain project scoped unless explicitly saved as a new Persona default.

#### Scenario: User disables one of several methods
- **WHEN** one method is disabled and another remains enabled
- **THEN** effective preview and the frozen execution package include only the enabled method's instructions in their declared order and retain the disabled selection for later reuse

#### Scenario: User turns off all creative Skills in a stage
- **WHEN** the stage switch is off
- **THEN** the Agent receives task goals, adopted Persona context and applicable execution contracts without the disabled creative instructions, and no Skill is enabled merely because of the model name

### Requirement: Effective Skill selection is traceable to actual execution
The package SHALL freeze source inventory, ID, version/revision/hash, order, enabled state and effective parameters. The execution receipt SHALL report the methods actually loaded and adaptations used. Normal pages SHALL expose configured versus effective selections. A page toggle alone MUST NOT be treated as proof of runtime enforcement.

#### Scenario: Global Agent defaults conflict with the task selection
- **WHEN** the executor cannot prevent a disabled method from affecting the managed task
- **THEN** it reports the limitation and does not claim the stage switch has been verified

### Requirement: Persona in third-party briefs

Video and article / graphic briefs for a third-party model SHALL include the work's persona: name, brand, voice and the merged profile (positioning, audience, domains, expression style with banned phrases, visual language, content and risk boundaries, public fact policy). When the persona's creative profile for that modality is fully set here, the brief SHALL also carry its main skill (readable with get_craft_skill even if not the newest version), style preset, quality checks, stage instruction, parameters and extra methods; the rules SHALL say to follow it. Product works SHALL get the profile and voice only. With platform creative skills switched off, only the profile is given.

#### Scenario: Composed persona method
- **WHEN** a persona's video creative profile is fully set with a main skill and style preset
- **THEN** that persona's video brief names the skill, how to read it and the style preset settings

#### Scenario: Product work under a persona
- **WHEN** a product work belongs to a persona
- **THEN** its brief carries the persona profile and voice but no persona writing method

### Requirement: No stage-based audio production

The platform SHALL make voice audio only through the one-click voiceover. Stage-based TTS, audio QC and audio-stage ASR, the voice-director / tts / qc skills, audio quality profiles and the audio creative profile SHALL not exist. Video master loudness, video subtitle ASR suggestions, the spoken-adaptation writing skill and audio materials SHALL remain. Historical runs of removed stages SHALL stay readable and show as retired.

#### Scenario: Persona configuration
- **WHEN** a user opens a persona's creative configuration
- **THEN** only text, graphic and video are offered, and the persona's voice is chosen on its profile page

#### Scenario: Old text work
- **WHEN** a text work that once ran audio stages is opened
- **THEN** it uses the default text recipe and its past audio runs show as retired stages without errors

