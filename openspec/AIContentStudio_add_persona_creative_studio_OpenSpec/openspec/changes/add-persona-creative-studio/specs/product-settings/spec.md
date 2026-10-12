## ADDED Requirements

### Requirement: Settings separates Studio built-ins external Skills and learned methods

Product Settings SHALL present Studio Built-in Skills/Style Presets/Quality Profiles as read-only product resources, Installed Agent Skills as external inventory and Capability Memory as user-managed reusable methods. Equal names do not imply the same source or executability.

#### Scenario: Inspect creative inventories
- **WHEN** the user opens the creative capability inventory
- **THEN** source kind, exact version/revision, executable/read-only state and provenance are visible without installing/enabling/importing anything

### Requirement: Provider configuration remains infrastructure not Persona style

Global provider/model/capability settings SHALL remain execution infrastructure. Persona-specific creative style/method defaults belong in Identity Workspace and MUST NOT be stored as global user/provider settings.
