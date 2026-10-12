## ADDED Requirements

### Requirement: Persona creative provenance is frozen on accepted Master revisions

When an accepted Creation Recipe proposal creates a Master revision, its verified provenance SHALL include the frozen IdentitySnapshot plus exact effective creative-profile origin, Studio Skill/Preset/Quality refs, explicit Capability Memory method revisions, model route and Stage/attempt hashes used for the accepted proposal. User edits remain separately identified.

#### Scenario: Same method changes later
- **WHEN** a built-in Skill/Persona profile receives a later version after Master save
- **THEN** the historical Master continues to identify the exact creative configuration that produced it

### Requirement: Deterministic Graphic composition preserves normal Master truth

A deterministic Graphic composer MAY produce a canonical graphic.master.v2 proposal from semantic plan/preset/exact asset refs. Explicit adoption SHALL still create a normal ContentMasterRevision and all existing asset/evidence/context validation applies. The composer MUST NOT write render-output truth or bypass Master save gates.

#### Scenario: Compose a Graphic proposal before explicit adoption
- **WHEN** a deterministic composer produces a graphic.master.v2 proposal but the user has not adopted it
- **THEN** no authoritative Master revision or render output is written; subsequent adoption uses the existing Master validation gates

#### Scenario: Registered composition Stage seals deterministic lineage
- **WHEN** `stage.graphic.compose@1` consumes an exact accepted `graphic.card-plan.v1` handoff and frozen Persona style preset
- **THEN** its existing WorkflowStepAttempt seals the plan, preset, tool version and proposal hashes without a model call or fabricated LLMRun
- **AND** explicit Master adoption recomputes the deterministic proposal from the immutable resolution and fails closed on any mismatch; renderer acceptance remains separate
