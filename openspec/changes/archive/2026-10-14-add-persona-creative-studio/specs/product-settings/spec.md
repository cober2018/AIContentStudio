## ADDED Requirements

### Requirement: Settings separates Studio built-ins external Skills and learned methods

Product Settings SHALL present Studio Built-in Skills/Style Presets/Quality Profiles as read-only product resources, Installed Agent Skills as external inventory and Capability Memory as user-managed reusable methods. Equal names do not imply the same source or executability.

#### Scenario: Inspect creative inventories
- **WHEN** the user opens the creative capability inventory
- **THEN** source kind, exact version/revision, executable/read-only state and provenance are visible without installing/enabling/importing anything

### Requirement: Provider configuration remains infrastructure not Persona style

Global provider/model/capability settings SHALL remain execution infrastructure. Persona-specific creative style/method defaults belong in Identity Workspace and MUST NOT be stored as global user/provider settings.

#### Scenario: Save Persona style separately from provider settings
- **WHEN** a user changes a Persona's creative style or method defaults
- **THEN** the change is saved through Identity Workspace without writing creative style into global provider/model settings

### Requirement: Image and Audio settings share one multimedia configuration surface

Models & AI settings SHALL expose one multimedia generation configuration surface for Image and Audio, with modality-specific sections driven by adapter-declared capabilities. The normal view SHALL show common controls, selected preset/binding summary and candidate count where supported. An explicit Advanced Settings action SHALL show exact provider/model/profile, image references/aspect/size or audio voice ID/rate/other supported fields. Unsupported fields SHALL be hidden or visibly unavailable. Settings SHALL not expose credentials or create per-user voice ownership records.

#### Scenario: Configure image candidates and an audio voice together
- **WHEN** the user configures a four-candidate image request and a Persona audio voice
- **THEN** each modality shows only its supported controls, preserves separate exact bindings and exposes one preview/receipt model without merging the image and audio payloads

#### Scenario: Large voice inventory remains usable
- **WHEN** the local voice catalog has hundreds of entries
- **THEN** the settings page provides search/filter/favorite/preview and Advanced Settings rather than an unbounded dropdown
