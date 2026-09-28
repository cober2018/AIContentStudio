## MODIFIED Requirements

### Requirement: Product shell

`/assets` SHALL be a real persistent System Assets & Knowledge workspace rather than a placeholder. `/settings` SHALL remain a primary workspace and SHALL expose the product-oriented Settings sections while preserving existing configuration behavior.

#### Scenario: Open Assets
- **WHEN** the user opens `/assets`
- **THEN** backend system-library data loads with truthful loading/error/empty states

#### Scenario: Open Settings
- **WHEN** the user opens `/settings`
- **THEN** Models, Data Sources, Channels, Rules, Team and Advanced sections load from real backend state
