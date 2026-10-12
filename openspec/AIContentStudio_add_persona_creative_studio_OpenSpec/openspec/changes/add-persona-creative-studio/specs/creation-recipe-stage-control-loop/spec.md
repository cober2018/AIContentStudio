## ADDED Requirements

### Requirement: Creation Recipe resolves Persona creative defaults

Effective Stage resolution SHALL consume the Unit's frozen IdentitySnapshot creative profile and derive exact Studio Skill, Style Preset, Quality Profile and model policy before applying saved Project Stage config and run-only overrides according to the documented precedence. Preview and attempt receipt SHALL freeze those exact identities/hashes.

#### Scenario: Same recipe topology under two Personas
- **WHEN** two Units use the same stage topology but different Persona creative profiles
- **THEN** preview/execution use each Persona's exact methods/styles while preserving the same Workflow process truth

### Requirement: Intermediate creative stages use accepted attempt outputs

Creation Recipe SHALL support `stage.creative.method@1` for bounded intermediate artifacts such as research brief, angles, outline, visual direction, card plan, spoken adaptation, voice direction and video shot plan. Intermediate acceptance remains WorkflowStepAttempt truth and MUST NOT create a synthetic Master/Material/Variant entity.

#### Scenario: Accept an outline
- **WHEN** the user accepts one exact outline candidate
- **THEN** downstream draft generation may consume its exact attempt/candidate hash while no ContentMasterRevision is created merely for the outline

### Requirement: Stage Handoff is thin exact lineage

Downstream Stage input SHALL identify accepted upstream run/attempt/node/output schema/hash plus concise summary and exact business refs needed by the Stage Contract. It MUST NOT implicitly re-derive or copy complete unrelated run histories into every prompt.

#### Scenario: Draft consumes accepted outline
- **WHEN** the draft stage follows research/angle/outline stages
- **THEN** its receipt identifies the exact accepted upstream outputs and hashes rather than treating the current mutable WorkflowStep output as unversioned context

### Requirement: Persona starter recipes are complete normal-mode journeys

The two starter Personas SHALL provide normal-mode default recipes for Text and Graphic plus one-click Audio output flow, and Video planning/handoff. A supported user SHALL be able to complete those journeys without opening raw Workflow JSON/canvas or writing a Prompt from scratch.

#### Scenario: New AI technology Persona project
- **WHEN** a user chooses the starter AI technology Persona and creates a Text Unit
- **THEN** its default recipe offers research → angle → outline → draft → quality/refine → final acceptance using shipped built-in methods

### Requirement: Audio output reuses existing media truth

Creation Recipe MAY add spoken-adaptation/voice-direction/TTS/QC stages to an accepted Text/Video source. TTS dispatch/acceptance remains ProviderGenerationTask/MaterialRevision truth and SHALL NOT introduce an Audio Master or duplicate media result table.

#### Scenario: Generate an audio version of an article
- **WHEN** the user runs the Persona's Audio output flow from an accepted Text Master
- **THEN** the final authoritative file is an accepted MaterialRevision with exact TTS/QC provenance
