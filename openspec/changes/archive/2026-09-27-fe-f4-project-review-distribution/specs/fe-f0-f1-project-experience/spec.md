## MODIFIED Requirements

### Requirement: Product shell
The frontend SHALL offer nine primary workspaces with navigable routes and loading, error, and empty views. Existing frontend pages SHALL remain reachable, using legacy aliases when a path is repurposed for a primary workspace. `/identities` SHALL load a persistent Content Identity workspace rather than a long-lived placeholder. `/review` SHALL load a persistent, project-first Review & Distribution workspace rather than a placeholder; `/review-publish` SHALL remain available for legacy Topic workflows.

#### Scenario: Browse primary navigation
- **WHEN** the user opens the application shell
- **THEN** nine primary workspaces are visible and each link resolves to a page or scoped placeholder

#### Scenario: Open identities
- **WHEN** the user opens `/identities`
- **THEN** the application loads backend Brand/Persona/Account/Series state and does not substitute browser fixture identity data

#### Scenario: Open project review
- **WHEN** the user opens `/review`
- **THEN** the workspace loads authorized ContentProjects and ContentUnits from backend state, not browser fixtures or a placeholder

### Requirement: Production entry and status semantics
The frontend SHALL navigate from a selected Content Unit to a project-scoped Production Workspace shell. Blocked, stale, unknown, ready, and waiting_human MUST have distinct labels and visual treatments. Blocked, stale, and unknown in Production and Review SHALL derive from the same persisted facts. An unknown delivery result MUST show reconciliation-needed and MUST NOT appear as success or offer generic retry.

#### Scenario: Abnormal project
- **WHEN** the user opens the abnormal fixture
- **THEN** blocked, stale, and unknown units are visibly distinguishable and their meanings are explained

#### Scenario: Unknown delivery in review
- **WHEN** the selected unit has an unresolved unknown DeliveryAttempt
- **THEN** the Review workspace shows reconciliation-needed without a generic retry action
