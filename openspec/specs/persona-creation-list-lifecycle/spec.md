# persona-creation-list-lifecycle Specification

## Purpose
TBD - created by archiving change add-persona-creation-list-lifecycle. Update Purpose after archive.
## Requirements
### Requirement: Explicit per-unit lifecycle actions
The system SHALL expose archive and delete actions for each editable persona content unit and SHALL keep lifecycle separate from production status.

#### Scenario: User opens the content list
- **WHEN** a user opens the persona content creation list
- **THEN** each eligible unit has explicit lifecycle actions applying only to that unit, not its project or sibling units

### Requirement: Reversible user archive
The system SHALL hide user-archived units from the default list, retain their content and history, and allow eligible user-archived units to be restored.

#### Scenario: Archive and restore
- **WHEN** a user archives an eligible unit and later restores it from archived history
- **THEN** the same unit returns to the current list with its original production state, content and history intact

#### Scenario: Legacy replacement history
- **WHEN** a unit was archived by identity replacement or its parent project is read-only
- **THEN** the new restore action does not reactivate that unit and the UI explains its history-only state

### Requirement: Delete removes a unit from creation lists
The system SHALL require explicit confirmation naming the unit before logical deletion, and SHALL exclude deleted units from both current and archived creation lists.

#### Scenario: Delete a unit with saved work
- **WHEN** the user confirms deletion of an eligible unit with saved revisions
- **THEN** that unit disappears from both lists while its project, shared assets, sibling units and referenced history remain intact
- **AND** the confirmation does not claim physical media deletion or offer an unimplemented recovery path

#### Scenario: Deleted unit accessed through another entry
- **WHEN** another entry attempts to edit or start production for a deleted unit
- **THEN** the system rejects that action while preserving read access needed by existing historical references

### Requirement: Authorized and execution-safe changes
The system SHALL enforce existing project authorization and transactionally check lifecycle eligibility. It SHALL NOT use lifecycle actions to retry or cancel provider executions.

#### Scenario: Active or unresolved execution
- **WHEN** a unit has an active execution or unresolved provider outcome
- **THEN** lifecycle mutation is rejected with an actionable reason directing the user to the existing execution handling flow

#### Scenario: Unauthorized operation
- **WHEN** a user lacks the required project permission
- **THEN** lifecycle mutation is denied without changing content or list visibility

#### Scenario: Repeated or failed request
- **WHEN** the same lifecycle operation is repeated or a request fails
- **THEN** repeated success is idempotent and a failure does not falsely remove the unit from the UI

### Requirement: Compatibility and traceability
The system SHALL retain the legacy DELETE contract for existing callers and record explicit new lifecycle changes using the existing project audit mechanism.

#### Scenario: Existing caller and history
- **WHEN** an existing client uses the legacy DELETE endpoint
- **THEN** its existing contract remains unchanged and old runs, revisions and historical references remain readable

### Requirement: One-form persona creation with a locked voice

Creating a persona SHALL be one form: name, brand and voice preset are required; positioning, target audience, content domains and content boundaries are optional. Once a persona has a voice preset it SHALL not be changed; a persona created before this rule MAY pick its voice once. One voice preset MAY serve several personas.

#### Scenario: Create an e-commerce persona
- **WHEN** the user fills name 电商小助手, brand, voice 女声 and positioning, and submits
- **THEN** the persona exists under that brand with its first profile revision and voice 女声, and its voice shows as locked

#### Scenario: Voice cannot change
- **WHEN** someone tries to change that persona's voice
- **THEN** the platform refuses and keeps 女声

### Requirement: Plain profile editing

Profile fields of personas, accounts and series SHALL be edited as plain inputs without inherit / clear / override choices: a filled field belongs to that entity, an empty one is not set. Expression style and visual language SHALL be written as plain text. Public fact policy, long-term views, value propositions, brand voice version and the creative configuration SHALL sit in a collapsed advanced section. Existing data SHALL be kept.

#### Scenario: Edit without modes
- **WHEN** the user types a target audience and leaves content domains empty, then saves
- **THEN** the revision stores the audience and leaves content domains unset

