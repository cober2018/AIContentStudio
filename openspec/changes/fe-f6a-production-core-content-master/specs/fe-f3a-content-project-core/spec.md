## MODIFIED Requirements

### Requirement: Aggregated project Versions view

The system SHALL expose a project Versions read model aggregated from actual versioned resources. It MUST NOT introduce a monolithic ProjectVersion persistence table solely for UI presentation. The view SHALL aggregate, when present: CreativeBrief revisions, ProjectFactBoundary revisions, active/archived ContentUnits, relevant Workflow versions, WorkflowRuns with frozen checksums, project MaterialRevisions, workflow-associated Draft/Candidate references, and real IdentitySnapshots linked to project ContentUnits/Runs. It MUST NOT create synthetic snapshots for legacy units. Versions SHALL also aggregate immutable project Candidates, candidate-bound approval decisions, and delivery authorizations/attempts/receipts from real entities, preserving historical versions without fabricating records.

#### Scenario: Historical versions remain visible
- **WHEN** newer Brief, boundary, Workflow or material versions exist
- **THEN** older project-relevant versions remain visible and their IDs/checksums are not rewritten

#### Scenario: IdentitySnapshot version item
- **WHEN** a project unit pins an IdentitySnapshot
- **THEN** Versions returns the snapshot ID/checksum and unit association as an immutable historical item

#### Scenario: Legacy identity version item
- **WHEN** a unit has no snapshot
- **THEN** Versions reports a legacy/unknown identity state without fabricating Brand/Persona/Account/Series revisions

#### Scenario: Candidate and delivery history
- **WHEN** a project has a frozen Candidate, its approval, and a DeliveryTarget with attempts or receipts
- **THEN** Versions returns their real IDs, hashes, status, and unit association without synthesizing a ProjectVersion row

Project Versions SHALL include real ContentMasterRevision rows with unit/modality, revision number, payload/context hashes, exact Identity/Brief/Fact Boundary refs, origin WorkflowRun/output provenance and creation actor/time. It MUST NOT synthesize Masters for legacy Draft-only history.

#### Scenario: Master version history
- **WHEN** a ContentUnit has multiple ContentMaster revisions
- **THEN** Versions returns each immutable revision and its exact context/provenance

#### Scenario: Legacy Draft-only unit
- **WHEN** historical production predates ContentMasterRevision
- **THEN** Versions keeps existing Draft/Candidate history without fabricating Master rows

### Requirement: Derived project Overview

The backend SHALL derive ContentProject overview stage, counts, readiness, risks, pending decisions and next action from persisted state using deterministic rules. The frontend MUST NOT duplicate an independent stage engine. Active FE-F3B production units lacking a usable IdentitySnapshot SHALL produce a typed identity-readiness risk; archived legacy units SHALL not block current readiness. Overview SHALL derive pending Content Approval, Delivery Authorization, and reconciliation decisions from project candidate/review/delivery facts. Unresolved unknown delivery MUST NOT be flattened into ready, approved, or delivered.

#### Scenario: Missing Brief
- **WHEN** a project has no CreativeBrief revision
- **THEN** overview stage is `brief_needed` and next action points to the Brief tab

#### Scenario: Missing Fact Boundary
- **WHEN** a project has a Brief but no frozen project Fact Boundary
- **THEN** overview stage is `evidence_needed`

#### Scenario: Attention state
- **WHEN** active units/runs contain blocked, stale, unknown or failed states
- **THEN** overview returns typed risks and an attention-required stage rather than flattening them into a generic failure

#### Scenario: Waiting human
- **WHEN** no higher-priority blocker exists and an active production run is waiting for human input
- **THEN** overview returns `waiting_human` with a typed pending decision

#### Scenario: Identity not ready
- **WHEN** an active FE-F3B unit lacks a usable identity snapshot
- **THEN** Overview includes an `identity_unready` risk and a deterministic next action

#### Scenario: Empty legacy Persona profile
- **WHEN** a newly bound active unit has a snapshot of a brandless Persona with no authored profile revision
- **THEN** Overview identifies incomplete identity readiness rather than presenting the empty snapshot as a complete identity

#### Scenario: Pending reconciliation
- **WHEN** an active project Candidate has a DeliveryAttempt with unresolved unknown outcome
- **THEN** Overview exposes a typed reconciliation decision ahead of generic ready or approved next actions

Project Overview SHALL derive production attention from the current ContentMaster revision when present, including incomplete_context, stale identity/brief/evidence/channel, blocked Master checks and render-unready state. These remain projections, not a mutable duplicate status table.

#### Scenario: Master context stale
- **WHEN** the current Master references an older Brief or Fact Boundary
- **THEN** Overview exposes a typed production-stale risk and next action back to Production

#### Scenario: Draft-only compatibility
- **WHEN** a unit has no ContentMaster revision
- **THEN** existing FE-F2/F3A/F4 readiness behavior remains valid until the unit adopts the new production core
