## ADDED Requirements

### Requirement: Accepted external execution files use MaterialRevision truth

Binary/file outputs from CreativeExecution SHALL become reusable media only after explicit acceptance creates an immutable MaterialRevision with exact hash, MIME/kind, rights/license decision, `source_kind=external_execution`, and external-execution/package provenance. `external_execution` is an additive source kind; existing source kinds and rows remain unchanged. Staged outputs are not library revisions. When the output was derived from materialized MaterialRevision inputs, its public/model/commercial rights MUST NOT exceed the rights supported by every exact input, and inherited attribution/license obligations MUST remain present. Live revocation or unprovable rights block escalation; the output may be stored only with the narrower false/unknown rights state.

#### Scenario: Accept an externally refined image
- **WHEN** the user accepts exact staged PNG bytes from one execution
- **THEN** one immutable MaterialRevision is created and may be referenced by Projects/Masters through existing reference contracts

#### Scenario: Derived material retains source rights boundary
- **WHEN** an external execution derives a new file from an input MaterialRevision that is not public-use allowed
- **THEN** the accepted external revision cannot be marked public-use allowed or lose the input's required attribution/license obligation

### Requirement: External project files default to non-public material semantics

A professional project file that can be materialized as a regular file MAY be stored as Material/MaterialRevision with a bounded project-file/other kind and public/model/commercial rights not inferred. An arbitrary local path alone MUST NOT satisfy MaterialRevision or Candidate media readiness.

#### Scenario: Agent reports only a local project path
- **WHEN** no project-file bytes are submitted through the bounded execution workspace
- **THEN** the path remains optional execution metadata and is not treated as an immutable reusable asset
