## ADDED Requirements

### Requirement: Workflow stage recipes are reusable methods, not Workflow truth

Capability Memory `recipe` MAY store content schema `workflow.stage.recipe.v1` containing an allowlisted stage config/prompt patch plus exact base Workflow/node/plugin/feedback provenance. It MUST NOT contain or replace the authoritative Workflow graph/definition.

#### Scenario: Save a successful stage method
- **WHEN** the user captures an accepted tuned stage as a method
- **THEN** a Capability candidate is created while the current Workflow remains unchanged until a separate explicit apply/save action

### Requirement: Applying a stage recipe is explicit and bounded

Applying an applicable saved/pinned workflow-stage recipe SHALL require exact artifact revision selection, display the node/config diff and allow only fields declared tunable by the current Stage Contract. It creates no hidden scope precedence and no automatic default update.

#### Scenario: Recipe references a different plugin version
- **WHEN** the saved recipe's base plugin/stage contract is incompatible with the current node
- **THEN** apply is blocked rather than coercing the old patch

### Requirement: Feedback may create candidates but never auto-promote

Accepted stage feedback/override evidence MAY deterministically create a Capability Memory candidate. Rejection/use frequency alone MUST NOT make it saved/pinned or alter any Workflow definition.
