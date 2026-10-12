## ADDED Requirements

### Requirement: Persona creative provenance is frozen on accepted Master revisions

When an accepted Creation Recipe proposal creates a Master revision, its verified provenance SHALL include the frozen IdentitySnapshot plus exact effective creative-profile origin, Studio Skill/Preset/Quality refs, explicit Capability Memory method revisions, model route and Stage/attempt hashes used for the accepted proposal. User edits remain separately identified.

#### Scenario: Same method changes later
- **WHEN** a built-in Skill/Persona profile receives a later version after Master save
- **THEN** the historical Master continues to identify the exact creative configuration that produced it

### Requirement: Deterministic Graphic composition preserves normal Master truth

A deterministic Graphic composer MAY produce a canonical graphic.master.v2 proposal from semantic plan/preset/exact asset refs. Explicit adoption SHALL still create a normal ContentMasterRevision and all existing asset/evidence/context validation applies. The composer MUST NOT write render-output truth or bypass Master save gates.
