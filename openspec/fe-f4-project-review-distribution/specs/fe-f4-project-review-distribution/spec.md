# fe-f4-project-review-distribution Specification

## Purpose
Define Project-first Review & Distribution as a projection of existing production, candidate, approval and delivery facts while separating Freeze Candidate, Content Approval and Delivery Authorization.

## Requirements

### Requirement: Project-first Review Center
The Review Center SHALL group by ContentProject and ContentUnit and derive state from persisted business facts rather than a second review state table.

#### Scenario: Open Review Center
- **WHEN** the user opens `/review`
- **THEN** projects/units load with truthful Ready/Blocked/Stale/Unknown/Approved projections

### Requirement: Freeze Candidate is separate from Content Approval
The system SHALL freeze an immutable Candidate before approval.

#### Scenario: Freeze
- **WHEN** current content satisfies required freeze gates
- **THEN** immutable project/unit/identity/evidence/workflow/content/media/check/render provenance and Candidate hash are stored without approval or delivery authorization

#### Scenario: Blocked freeze
- **WHEN** required checks are stale/blocking or evidence/media rights are invalid
- **THEN** freeze is rejected with typed reasons

### Requirement: Candidate-bound Content Approval
Approval SHALL bind one exact immutable Candidate hash and MUST NOT rewrite Candidate content.

#### Scenario: Approve
- **WHEN** a reviewer approves a valid Candidate
- **THEN** Review references that Candidate/hash and no DeliveryTarget is created implicitly

### Requirement: Delivery Authorization is separate
DeliveryTarget creation SHALL represent explicit Delivery Authorization for an approved exact Candidate.

#### Scenario: Authorize before approval
- **WHEN** Candidate lacks Content Approval
- **THEN** authorization is rejected

### Requirement: Unknown remains unknown
Unknown remote results SHALL require reconciliation and SHALL NOT be automatically retried.

#### Scenario: Timeout
- **WHEN** publisher result cannot be confirmed
- **THEN** Review projects Unknown/reconciliation-needed with no generic retry

### Requirement: Derived review status
Blocked/Stale/Unknown/Ready/Approved/delivery states SHALL be deterministic projections, not another mutable state source.

### Requirement: Unit review workspace
A selected unit SHALL expose Preview, Changes, Checks and Publish tabs and clearly separate Freeze Candidate, Content Approval, Delivery Authorization and delivery execution.

### Requirement: Project history integration
Candidate/approval/delivery lifecycle SHALL appear in project Activity, Versions and Overview from underlying facts.
