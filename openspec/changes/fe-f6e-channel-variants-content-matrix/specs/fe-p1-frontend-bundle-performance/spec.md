## ADDED Requirements

### Requirement: Matrix and Variant tools respect lazy route budgets
Project Matrix suggestion and Variant editing code SHALL load only when the relevant Project/Production feature is opened. Their adapter/editor dependencies MUST NOT enter Home, Assets, Settings, Learning or unrelated Production modality initial closures. The existing `/projects` initial-JS budget and FE-P1 automated import-graph gate SHALL remain enforced.

#### Scenario: Open ordinary Projects list
- **WHEN** a user loads `/projects` without opening Matrix suggestions or a Variant editor
- **THEN** initial JS stays within the existing FE-P1 budget and does not statically include those feature modules
