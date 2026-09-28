## MODIFIED Requirements

### Requirement: Pending work uses existing state semantics

Home MAY additionally surface LearningCandidate validation when a candidate is `ready_for_review`. Learning remains the authoritative source and Home MUST NOT create a duplicate learning task/state. Operational production/review risks retain higher precedence than learning validation.

#### Scenario: Learning validation pending
- **WHEN** an owned LearningCandidate is ready_for_review
- **THEN** Home shows a pending decision linking to `/learning` without changing candidate status
