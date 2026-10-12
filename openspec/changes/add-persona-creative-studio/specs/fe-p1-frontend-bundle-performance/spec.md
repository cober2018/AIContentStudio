## ADDED Requirements

### Requirement: Persona creative configuration remains progressively loaded

Identity summary and lightweight creative readiness MAY load with Identity Workspace, while full Skill references, composed-method pickers, Graphic contact sheets, Audio previews and Production editors SHALL load only when the relevant tab/stage opens. Unrelated routes MUST NOT eagerly import heavy production/media/editor modules.

#### Scenario: Open Identity list
- **WHEN** the user opens `/identities` without opening Creative Configuration
- **THEN** heavy Graphic/Audio/Production bundles are not part of the initial closure
