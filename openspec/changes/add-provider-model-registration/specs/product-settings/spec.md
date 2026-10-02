## ADDED Requirements

### Requirement: Settings exposes provider registration and functional model choices
Models & AI SHALL expose provider API/credential registration, explicit discovery, selected model registration, a global default selector and selectors for actually integrated functional purposes. The workspace MUST reuse registered profiles and remain lazy-loaded, role-aware and truthful about unavailable capabilities.

#### Scenario: Register CPA models and choose default
- **WHEN** the administrator registers gemini-3.8-flash-high, claude-opus-4-6-thinking and grok-4.7 and selects Gemini as default
- **THEN** a refresh retains all three models and the default, functional dropdowns offer these models where compatible, and no secret is returned

#### Scenario: Read-only user
- **WHEN** a non-administrator opens the model configuration page
- **THEN** safe persisted choices are visible but provider mutation and discovery controls cannot perform administrator operations

#### Scenario: Rejected save
- **WHEN** a save conflicts or validation fails
- **THEN** the current local selections are retained and no partial default/credential update is shown as successful
