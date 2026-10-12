## ADDED Requirements

### Requirement: Master revisions preserve bounded creative intent

ContentMasterRevision SHALL support optional canonical creative-intent metadata/hash that captures objective, must-keep/must-avoid/creative-freedom and stable-ID rationale without duplicating Identity/FactPack/source truth. Intent changes require a new normal Master revision under existing CAS/idempotency/atomicity rules.

#### Scenario: Change only creative intent
- **WHEN** an editor changes why a section/scene should be handled while payload remains otherwise equal
- **THEN** a new Master revision is created with a new intent hash and the old revision remains unchanged

### Requirement: Professional execution never mutates a Master implicitly

Preparing a CreativeExecutionPackage, dispatching an Agent, receiving result_ready output or accepting a MaterialRevision MUST NOT create/update ContentMasterRevision automatically. The accepted result can affect content only through an explicit new Master save that binds exact accepted refs/render.

#### Scenario: External video edit is accepted
- **WHEN** one external MP4 is accepted as MaterialRevision
- **THEN** the current Video Master remains unchanged until the editor explicitly binds that revision and saves a new Master

### Requirement: Video daily creation is director-first while F6D integrity remains

The product SHALL present Script/Scene/Shot intent, Assets, Voice, Subtitles, Cover, creative intent and Director Package as the primary Video creation experience. Existing Video v1/v2 timeline/render fields, exact ref validation, render-input binding, manual attestation and Candidate v4 behavior SHALL remain compatible and available for historical/advanced workflows.

Creating a Director Package before final render MUST NOT make the Video Master Candidate-ready. Existing final render/readiness gates still govern v4 freeze.

#### Scenario: Prepare external edit before render
- **WHEN** the user has a valid Video script/shot plan but no final MP4
- **THEN** they can prepare a Director Package while Candidate freeze remains blocked until an accepted render is explicitly bound and saved
