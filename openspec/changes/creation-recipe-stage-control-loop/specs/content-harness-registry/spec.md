## ADDED Requirements

### Requirement: Node descriptors may expose a versioned Stage Contract

The node/plugin registry SHALL support an optional bounded Stage Contract descriptor containing typed config/UI/input/output/tunable-field and execution-preview capabilities. The contract is metadata/validation truth for product controls and MUST NOT make an unavailable executor executable.

Stage activation SHALL use a distinct new registered plugin version pinned with its exact contract schema/version in a newly saved Workflow definition. Existing media/check/human plugin versions and historical definitions/reruns MUST NOT inherit new contract validation or execution/review semantics merely because registry metadata changed.

#### Scenario: Legacy node without Stage Contract
- **WHEN** an old plugin has no Stage Contract
- **THEN** it remains executable through its existing advanced workflow behavior but is not given invented normal-stage tuning controls

#### Scenario: Stage controls are added for a media or check plugin
- **WHEN** a new stage-capable version is registered while old Workflow definitions remain pinned to the original version
- **THEN** only explicitly saved definitions selecting the new version activate that Stage Contract and historical reruns keep the old behavior

### Requirement: Stage executors consume the exact resolved contract

A Stage Contract executor SHALL receive the canonical ResolvedStageExecution/effective config produced by the server resolver. It MUST NOT read a conflicting hidden parameter source for fields declared tunable. Any exposed field that the executor cannot consume MUST fail validation rather than be ignored.

#### Scenario: Prompt exists in config but executor ignores it
- **WHEN** a plugin declares prompt/instruction tunable but its execution adapter cannot bind that value
- **THEN** the definition is rejected as an invalid Stage Contract implementation

### Requirement: Project-native stage plugins do not redefine legacy plugins

New modern Master/Variant/Creative Execution stage plugins SHALL use distinct plugin identities/versioning and existing domain services. Legacy `builtin.generate` and historical workflow behavior remain unchanged.

#### Scenario: Historical Draft workflow
- **WHEN** an old Run uses `builtin.generate`
- **THEN** it continues its frozen Draft-oriented behavior and is not reinterpreted as a Master proposal stage
