## MODIFIED Requirements

### Requirement: Project-first Review Center
The Review Center SHALL group authorized ContentProjects and ContentUnits and derive state from persisted production, Candidate, Review, DeliveryTarget, DeliveryAttempt, and Receipt facts rather than a second review state table. Legacy Topic-first `/review-publish` SHALL remain available without substituting its queue for project review.

#### Scenario: Open Review Center
- **WHEN** the user opens `/review`
- **THEN** projects/units load with truthful Ready/Blocked/Stale/Unknown/Approved projections

#### Scenario: Legacy review remains separate
- **WHEN** the user opens `/review-publish`
- **THEN** existing Topic-based review remains readable and project candidates are not leaked through that legacy queue

FE-F4 pending-decision summaries MAY be consumed by Home as a read projection. Home MUST NOT create a duplicate review/approval/delivery task state.

#### Scenario: Approval pending on Home
- **WHEN** FE-F4 projects a Content Approval decision
- **THEN** Home may deep-link to it while FE-F4 remains the review-state source

### Requirement: Unknown remains unknown
Unknown remote results SHALL require reconciliation and SHALL NOT be automatically retried or silently converted to delivered. A further attempt is allowed only after an explicit, audited not-delivered reconciliation under the existing DeliveryAttempt rules.

#### Scenario: Timeout
- **WHEN** publisher result cannot be confirmed
- **THEN** Review projects Unknown/reconciliation-needed with no generic retry

#### Scenario: Reconcile without duplicate side effect
- **WHEN** an operator records a delivered or not-delivered reconciliation for an unknown attempt
- **THEN** the attempt/target history records that outcome without making a second remote call during reconciliation

Home SHALL preserve FE-F4 Unknown/reconciliation semantics.

#### Scenario: Unknown on Home
- **WHEN** delivery result is unknown
- **THEN** Home shows reconciliation required and no automatic delivery retry action
