## ADDED Requirements

### Requirement: Task-oriented identity directories and detail views
The Identity Workspace SHALL provide separate role, owned account, series and brand directories with URL-preserved search, status and pagination. Overview, profile editing, immutable revision history and advanced configuration SHALL be independently addressable. Existing hierarchy, inheritance, revision contracts and persona links SHALL remain available. Independent owned accounts MUST NOT require a Persona.

#### Scenario: Open identity entry
- **WHEN** the user opens the default identity workspace
- **THEN** role selection and next actions are clear without displaying all forms or automatically initializing a role

#### Scenario: Existing persona link
- **WHEN** a production work links to identities with its persona parameter
- **THEN** the correct role opens without selecting an unrelated default identity or changing a snapshot

#### Scenario: Edit and conflict
- **WHEN** an authorized editor explicitly saves a profile revision and receives a conflict
- **THEN** input remains available for explicit comparison with the latest revision, without automatic retry or overwriting inherited data

#### Scenario: Read-only or archived identity
- **WHEN** permission is unknown, read-only or an applicable identity ancestor is archived
- **THEN** the workspace exposes readable data but no permitted mutation path through its UI

#### Scenario: Change selected identity during a read
- **WHEN** an earlier identity read completes after navigation to another identity
- **THEN** that response does not replace the selected identity's values or draft
