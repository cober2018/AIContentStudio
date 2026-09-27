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

### Requirement: Append-only project activity

The system SHALL maintain an append-only product event stream per ContentProject. Events SHALL use stable event codes, entity references and structured payloads. Large content bodies, material bytes, secrets and mutable display text MUST NOT be the event contract. Project Candidate freeze, Content Approval, changes requests, Delivery Authorization, execution outcome, reconciliation, and receipt SHALL emit stable ProjectEvent codes in the same transaction as the corresponding local state change. External side-effect attempts SHALL retain their existing prepare/commit boundary and MUST NOT be claimed succeeded before a confirmed result.

#### Scenario: Business mutation records event
- **WHEN** project, Brief, Source, boundary, ContentUnit, Workflow, DataSnapshot or project-asset state changes through an FE-F3A/FE-F2 project flow
- **THEN** the same transaction records the corresponding ProjectEvent unless the underlying operation is idempotently returning an already-recorded association

#### Scenario: Activity survives display copy changes
- **WHEN** frontend wording changes
- **THEN** historical activity is still renderable from stable `event_type` and structured payload fields

#### Scenario: AuditLog remains separate
- **WHEN** an operation already has a security/operations AuditLog requirement
- **THEN** FE-F3A does not remove that AuditLog merely because a ProjectEvent also exists

#### Scenario: Failed mutation has no event
- **WHEN** a project mutation rolls back
- **THEN** its ProjectEvent also rolls back and the activity timeline does not claim a change that did not commit

#### Scenario: Review and delivery events
- **WHEN** a candidate is frozen, approved, authorized, or reconciled through a project-scoped action
- **THEN** Activity records the corresponding stable event and entity reference exactly once with the committed local change

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
