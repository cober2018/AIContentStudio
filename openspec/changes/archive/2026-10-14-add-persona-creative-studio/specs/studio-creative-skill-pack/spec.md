## ADDED Requirements

### Requirement: Studio built-in Skills are a distinct versioned inventory

The product SHALL ship a versioned `studio_builtin_skill` inventory distinct from Capability Memory and Installed Agent Skills. Built-in Skills SHALL be usable without external Skill installation and SHALL expose stable key/version/method contracts. Equal display names across inventories MUST NOT imply equivalence or replacement.

#### Scenario: Same method name in three inventories
- **WHEN** a Studio built-in Skill, Capability Memory artifact and Installed Agent Skill share a display name
- **THEN** preview/listing identifies distinct source kinds and exact versions/revisions and never silently substitutes one for another

### Requirement: Built-in Skill packages have concise instructions and machine contracts

Each built-in Skill SHALL provide concise `SKILL.md` instructions, machine-readable `STUDIO-CONTRACT.json`, provenance `STUDIO-META.md`, optional on-demand references and test fixtures. The machine contract SHALL declare modality/purpose, compatible Stage schemas, required context, input/output schema keys, tunable fields/defaults, prompt sections, registered tool/rule references, compatible style/quality profiles and bounds.

The runtime MUST NOT execute arbitrary code merely because a Skill package contains text or a script path. Deterministic actions require explicit registered application Tool/Rule/Provider contracts.

#### Scenario: Skill references unknown tool
- **WHEN** a built-in Skill contract references a missing tool key/version
- **THEN** persistent validation fails and the Skill is unavailable rather than executing a path from its documentation

### Requirement: The first built-in creative pack covers the normal production loop

The shipped first version SHALL include at least:

- research/evidence brief and angle lab;
- Text outline/longform/answer/social-short/humanize/title-hook;
- Graphic visual-director/card-plan/image-brief plus deterministic layout-compose and Graphic QC;
- Audio spoken-adapt/voice-director/TTS method/QC;
- Video script/shot-director/director-package.

Each item SHALL have an exact version and contract tests.

#### Scenario: New installation has no external Skills
- **WHEN** no Installed Agent Skill or saved Capability Memory method exists
- **THEN** the two starter Persona default recipes still resolve their required creative methods from the Studio built-in pack

### Requirement: Style Presets are versioned declarative resources separate from Skills

The product SHALL ship versioned Text, Graphic and Audio Style Presets. Presets SHALL describe creative language/configuration and MUST NOT contain credentials or arbitrary executable code. Persona creative profiles select exact preset refs; Account/Series replacement overrides remain explicit.

#### Scenario: Change only Persona visual style
- **WHEN** a Persona switches from technical-editorial to architecture-diagram preset
- **THEN** the Graphic creative profile revision changes while the underlying Graphic Skill version and historical outputs remain unchanged

### Requirement: Built-in resource provenance and licensing are explicit

Every Skill/Preset/tool resource SHALL record source/provenance classification. Method inspiration, adapted rules, vendored code and self-developed implementation MUST be distinguished. Code copied or vendored from third parties requires explicit license-compatible handling; method inspiration alone SHALL NOT be represented as copied code.

#### Scenario: Easel-inspired method design
- **WHEN** a Studio Skill adopts an engineering pattern learned from Easel without copying its source files
- **THEN** STUDIO-META records method/reference provenance and no vendored-code claim is made

### Requirement: Persistent validators prevent declaration/runtime drift

Repository tests SHALL verify resource structure, frontmatter/contracts, references, provenance, secret/path safety, exact tool/rule keys and all Persona blueprint/default-recipe refs. They SHALL also verify that every exposed tunable field is actually consumed by the resolver/executor/tool contract.

#### Scenario: UI exposes an unused parameter
- **WHEN** a Skill/Stage contract declares a tunable field that the resolved executor does not consume
- **THEN** persistent validation fails before release rather than shipping a decorative control
