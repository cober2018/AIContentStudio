## MODIFIED Requirements

### Requirement: Production stages expose ordered independent creative Skill controls
The existing creative hierarchy SHALL support multiple exact Skill/method references per production stage, ordered execution, editable compatible parameters, individual enabled flags and a stage-level creative-Skill switch. Missing new fields SHALL preserve legacy behavior. Existing whole-profile replacement and snapshot semantics SHALL remain unchanged. Stage overrides SHALL remain project scoped unless explicitly saved as a new Persona default. A work-level production-stage setting SHALL override only the stages it names; stages it does not name SHALL keep the Persona selections.

#### Scenario: User disables one of several methods
- **WHEN** one method is disabled and another remains enabled
- **THEN** effective preview and the frozen execution package include only the enabled method's instructions in their declared order and retain the disabled selection for later reuse

#### Scenario: User turns off all creative Skills in a stage
- **WHEN** the stage switch is off
- **THEN** the Agent receives task goals, adopted Persona context and applicable execution contracts without the disabled creative instructions, and no Skill is enabled merely because of the model name

#### Scenario: A work enables only the script stage
- **WHEN** a persona video work saves production stages naming only `script`
- **THEN** its edit package still loads the Persona's sound, picture, caption, packaging, finish and review methods
