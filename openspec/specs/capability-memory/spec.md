# capability-memory Specification

## Purpose
Support explicit version-pinned Stage learning and method reuse through the existing Capability Memory truth; feedback never silently alters workflows.
## Requirements
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

A deterministic `workflow.stage.recipe.v1` patch SHALL contain an actual explicit allowlisted tunable-field diff. Accept-with-edits content alone is evidence, not a derived instruction/config patch. Without such a diff, capture for Workflow promotion requires an explicit user-authored/selected allowed instruction or method change; no hidden inference or empty fabricated patch is accepted.

#### Scenario: Accepted feedback captures only a candidate
- **WHEN** exact accepted stage feedback is explicitly captured as a reusable method
- **THEN** only a non-authoritative candidate is created, with no automatic saved/pinned promotion or Workflow change

#### Scenario: Accepted content edit is not a Workflow instruction
- **WHEN** accepted feedback contains only content corrections and no explicit tunable-field change
- **THEN** no deterministic Workflow patch is inferred from the corrections, and any proposed method/config change must be authored or selected explicitly

### Requirement: Creative learning defaults to the active Persona hierarchy

Reusable creative methods learned from production SHALL default to the narrowest provable Project/Series/Account/Persona scope that produced them. Owner scope MAY hold generic technical methods but MUST NOT be treated as an automatic cross-Persona creative-style source.

#### Scenario: Persona-specific writing improvement
- **WHEN** an accepted run under AI科技研发技术博主 captures a reusable writing method
- **THEN** ordinary discovery for 日常生活方式博主 does not apply it unless the user explicitly broadens/selects that method

### Requirement: Composed Persona configuration uses exact Capability revisions

A Persona creative profile or Stage composition MAY reference exact saved/pinned CapabilityArtifactRevision IDs in an explicit order. Applicable discovery results are suggestions only; the resolver MUST NOT silently merge or choose among multiple artifacts.

#### Scenario: Two applicable Persona methods
- **WHEN** two saved methods match a Persona
- **THEN** composed configuration requires explicit revision selection/order rather than using usage count as hidden precedence

### Requirement: Capability Memory does not rewrite Persona creative profiles

Feedback/capture/promotion MAY create or advance Capability artifacts but SHALL NOT mutate Identity revisions or Workflow defaults without a separate explicit user action.

#### Scenario: Promote a Persona method without changing defaults
- **WHEN** an accepted method is promoted into Capability Memory without a separate Identity or Workflow save
- **THEN** Persona creative profiles and Workflow default versions remain unchanged
