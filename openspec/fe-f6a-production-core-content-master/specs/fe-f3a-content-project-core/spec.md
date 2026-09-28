## MODIFIED Requirements

### Requirement: Aggregated project Versions view

Project Versions SHALL include real ContentMasterRevision rows with unit/modality, revision number, payload/context hashes, exact Identity/Brief/Fact Boundary refs, origin WorkflowRun/output provenance and creation actor/time. It MUST NOT synthesize Masters for legacy Draft-only history.

#### Scenario: Master version history
- **WHEN** a ContentUnit has multiple ContentMaster revisions
- **THEN** Versions returns each immutable revision and its exact context/provenance

#### Scenario: Legacy Draft-only unit
- **WHEN** historical production predates ContentMasterRevision
- **THEN** Versions keeps existing Draft/Candidate history without fabricating Master rows

### Requirement: Derived project Overview

Project Overview SHALL derive production attention from the current ContentMaster revision when present, including incomplete_context, stale identity/brief/evidence/channel, blocked Master checks and render-unready state. These remain projections, not a mutable duplicate status table.

#### Scenario: Master context stale
- **WHEN** the current Master references an older Brief or Fact Boundary
- **THEN** Overview exposes a typed production-stale risk and next action back to Production

#### Scenario: Draft-only compatibility
- **WHEN** a unit has no ContentMaster revision
- **THEN** existing FE-F2/F3A/F4 readiness behavior remains valid until the unit adopts the new production core
