## MODIFIED Requirements

### Requirement: Project-scoped persistent workflow

A project ContentUnit MAY pin an IdentitySnapshot. A WorkflowRun started from such a unit SHALL store the exact same snapshot ID together with its frozen workflow definition/version/checksum.

#### Scenario: Identity changes after run
- **WHEN** Brand/Persona/Account/Series receives newer revisions after a Run starts
- **THEN** the historical Run continues to reference its original IdentitySnapshot and workflow definition

### Requirement: Persona × Modality default workflow versions

Existing PersonaWorkflowDefault remains valid. FE-F3B SHALL add Account × Modality and Series × Modality overrides without replacing Persona defaults.

#### Scenario: Resolve hierarchy workflow preference
- **WHEN** a unit is bound to Series and Account
- **THEN** effective default resolution uses Series then Account then Persona and returns the source scope

#### Scenario: Scoped default portability
- **WHEN** an editor saves Account or Series default from a project workflow
- **THEN** the same FE-F2 server portability gate and immutable Workflow version rules apply

### Requirement: Real node execution and inspection

Identity updates MUST NOT change the identity context of an existing WorkflowRun.

#### Scenario: Run inspector
- **WHEN** a user inspects a historical Run
- **THEN** the run view uses its frozen IdentitySnapshot or explicit legacy/unknown state, not current hierarchy settings
