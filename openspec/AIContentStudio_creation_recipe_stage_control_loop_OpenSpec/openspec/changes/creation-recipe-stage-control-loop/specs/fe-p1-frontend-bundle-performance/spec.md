## ADDED Requirements

### Requirement: Creation Recipe normal controls remain lightweight and advanced tooling stays lazy

The stage strip/control drawer and lightweight typed controls SHALL be available in normal Production without eagerly loading raw graph automation, TipTap, heavy Graphic/Video editors, Capability Memory management or professional-execution panels until opened.

#### Scenario: Open Production stage list
- **WHEN** the user views the recipe and a simple Text stage
- **THEN** Advanced canvas, heavy unrelated modality editors and professional execution UI remain outside the initial closure

#### Scenario: Open Advanced
- **WHEN** the user explicitly opens graph/mapping automation
- **THEN** the existing WorkflowMiniCanvas/NodeInspector bundle loads lazily without changing recipe state
