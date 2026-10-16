## ADDED Requirements

### Requirement: Production stages expose ordered independent creative Skill controls
The existing creative hierarchy SHALL support multiple exact Skill/method references per production stage, ordered execution, editable compatible parameters, individual enabled flags and a stage-level creative-Skill switch. Missing new fields SHALL preserve legacy behavior. Existing whole-profile replacement and snapshot semantics SHALL remain unchanged. Stage overrides SHALL remain project scoped unless explicitly saved as a new Persona default.

#### Scenario: User disables one of several methods
- **WHEN** one method is disabled and another remains enabled
- **THEN** effective preview and the frozen execution package include only the enabled method's instructions in their declared order and retain the disabled selection for later reuse

#### Scenario: User turns off all creative Skills in a stage
- **WHEN** the stage switch is off
- **THEN** the Agent receives task goals, adopted Persona context and applicable execution contracts without the disabled creative instructions, and no Skill is enabled merely because of the model name

### Requirement: Effective Skill selection is traceable to actual execution
The package SHALL freeze source inventory, ID, version/revision/hash, order, enabled state and effective parameters. The execution receipt SHALL report the methods actually loaded and adaptations used. Normal pages SHALL expose configured versus effective selections. A page toggle alone MUST NOT be treated as proof of runtime enforcement.

#### Scenario: Global Agent defaults conflict with the task selection
- **WHEN** the executor cannot prevent a disabled method from affecting the managed task
- **THEN** it reports the limitation and does not claim the stage switch has been verified
