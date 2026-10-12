## ADDED Requirements

### Requirement: Daily product use has one primary surface

The primary product routes SHALL let an ordinary owner start from an idea, existing material/source, an Opportunity, or an existing Project without requiring legacy Dashboard/Topic/Workspace navigation. Landing SHALL enter Home. Project SHALL remain the primary container for Brief, evidence, assets, content, channel variants, creative execution, versions and activity.

#### Scenario: Start from a direct idea
- **WHEN** the user already knows what they want to create
- **THEN** they can create/open a Project directly and proceed without first creating an Opportunity or legacy Topic

### Requirement: Legacy operations retire only after operation-level parity

The product SHALL maintain an explicit operation-parity inventory for legacy pages. A legacy daily-navigation entry MAY be hidden only after every still-supported state-changing action on that page has an equivalent authorized new-surface action and regression. Historical records/URLs MUST remain readable or deep-link to the exact corresponding new record.

#### Scenario: New Assets page lists Sources but cannot confirm facts
- **WHEN** legacy Sources still owns fact confirmation
- **THEN** the legacy daily entry cannot be considered retired merely because Sources are visible in the new library

#### Scenario: Legacy route has an exact new destination
- **WHEN** a historical FactPack URL can be represented in the new Assets/Project surface
- **THEN** compatibility navigation preserves the exact entity context instead of redirecting to a generic home/list page

### Requirement: Production route is an active creation and execution queue

`/production` SHALL project current owned content units, actionable creation state, native ProviderGenerationTask state and CreativeExecution state without creating a second durable task table. It SHALL deep-link to authoritative Project/Unit/execution records.

#### Scenario: External result needs review
- **WHEN** an owned CreativeExecution becomes result_ready
- **THEN** `/production` shows the actionable result and opens its exact Project/Execution review surface
