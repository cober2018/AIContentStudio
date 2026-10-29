## ADDED Requirements

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
