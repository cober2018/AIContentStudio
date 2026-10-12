## ADDED Requirements

### Requirement: A selected Persona makes Production immediately actionable

When a Project/Unit uses a starter or configured Persona, Production SHALL show its effective default Creation Recipe, creative readiness and next actionable stage without requiring the user to author a Workflow, Skill or Prompt first.

#### Scenario: Start a Text Unit from starter Persona
- **WHEN** the user creates a Text Unit with one of the two starter Personas and required provider capability is ready
- **THEN** the default Persona recipe is runnable immediately in normal Production mode

### Requirement: Creative configuration scope is understandable

The UI SHALL distinguish Persona default, Account override, Series override, Project Workflow configuration and one-run override. Saving a current result/method SHALL clearly state which future content will be affected.
