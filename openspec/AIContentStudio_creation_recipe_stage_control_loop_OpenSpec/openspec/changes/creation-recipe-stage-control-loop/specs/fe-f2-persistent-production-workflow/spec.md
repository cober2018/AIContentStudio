## ADDED Requirements

### Requirement: Workflow Definition is Creation Recipe truth

The existing immutable Workflow Definition revision SHALL remain the only persisted process/recipe truth. Production MAY present a stage-oriented Creation Recipe view, but it MUST preserve the same Workflow ID/version/checksum, node/plugin config, mappings, dependencies and historical Run pinning.

#### Scenario: Switch from stage view to Advanced
- **WHEN** the user opens Advanced graph mode from a Creation Recipe
- **THEN** both views edit the same unsaved definition and one explicit save creates one normal Workflow revision

### Requirement: Stage-contract attempts freeze resolved inputs and receipts

WorkflowStepAttempt SHALL support bounded nullable resolved input snapshot and execution receipt for Stage Contract nodes. The receipt SHALL freeze exact definition/node/plugin/config/override/method/model/prompt/upstream/output-contract identities. Legacy attempts remain readable with these fields absent.

#### Scenario: Failed tuned attempt
- **WHEN** a tuned stage fails after resolution
- **THEN** the immutable failed attempt still records the exact resolved configuration/input receipt needed for later feedback

### Requirement: Run-only stage overrides do not mutate saved definitions

Project-scoped Run/rerun MAY accept bounded node overrides only for fields declared tunable by the exact Stage Contract. The override SHALL be execution-local, hash-bound and persisted in the attempt receipt. It MUST NOT alter the pinned Workflow revision or scoped defaults.

#### Scenario: Rerun only one stage with a different model
- **WHEN** the selected Stage Contract allows model profile override
- **THEN** the new attempt uses and records that exact profile while the saved Project Workflow remains unchanged

### Requirement: Stage result review is distinct from Run execution

The Workflow UI SHALL expose immutable attempt candidates/results for review and explicit domain adoption. Running or succeeding a node MUST NOT automatically make its proposed content the current Master/Variant unless that node's existing authoritative domain contract explicitly creates that entity and the user completed its required acceptance.

#### Scenario: Successful Master proposal node
- **WHEN** the node attempt succeeds with proposal candidates
- **THEN** the Run records success/output but current Content Master does not change until explicit adoption

### Requirement: Feedback promotion creates new Workflow versions

Applying an accepted run override/improvement to a Project or scoped default SHALL use the existing immutable Workflow save/default portability contracts and CAS. Historical runs/attempts retain their prior definition.

#### Scenario: Save successful override as Persona default
- **WHEN** portability succeeds and the binding revision is current
- **THEN** a new Persona × modality default Workflow version is created and existing Units remain pinned
