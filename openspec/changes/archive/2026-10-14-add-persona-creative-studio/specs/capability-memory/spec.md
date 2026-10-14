## ADDED Requirements

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
