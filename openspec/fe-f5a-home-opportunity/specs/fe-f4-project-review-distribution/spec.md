## MODIFIED Requirements

### Requirement: Project-first Review Center

FE-F4 pending-decision summaries MAY be consumed by Home as a read projection. Home MUST NOT create a duplicate review/approval/delivery task state.

#### Scenario: Approval pending on Home
- **WHEN** FE-F4 projects a Content Approval decision
- **THEN** Home may deep-link to it while FE-F4 remains the review-state source

### Requirement: Unknown side effects remain unknown

Home SHALL preserve FE-F4 Unknown/reconciliation semantics.

#### Scenario: Unknown on Home
- **WHEN** delivery result is unknown
- **THEN** Home shows reconciliation required and no automatic delivery retry action
