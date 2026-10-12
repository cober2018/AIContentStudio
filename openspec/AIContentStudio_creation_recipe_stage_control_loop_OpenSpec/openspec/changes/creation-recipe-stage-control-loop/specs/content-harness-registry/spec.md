## ADDED Requirements

### Requirement: Node descriptors may expose a versioned Stage Contract

The node/plugin registry SHALL support an optional bounded Stage Contract descriptor containing typed config/UI/input/output/tunable-field and execution-preview capabilities. The contract is metadata/validation truth for product controls and MUST NOT make an unavailable executor executable.

#### Scenario: Legacy node without Stage Contract
- **WHEN** an old plugin has no Stage Contract
- **THEN** it remains executable through its existing advanced workflow behavior but is not given invented normal-stage tuning controls

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
