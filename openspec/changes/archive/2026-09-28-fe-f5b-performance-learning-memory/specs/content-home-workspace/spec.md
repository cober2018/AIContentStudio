## MODIFIED Requirements

### Requirement: Pending work uses existing state semantics

Home SHALL derive “待我处理” from existing typed facts including waiting_human/waiting_input, pending Content Approval, pending Delivery Authorization, unresolved unknown reconciliation, identity_unready, blocked, and stale. Its decision ordering MUST be unknown/reconciliation > blocker > stale > waiting human > approval pending > delivery authorization pending > identity readiness, with stable entity IDs breaking ties. Duplicate cards for the same code and entity reference SHALL be collapsed. Unknown and stale MUST NOT be flattened into success.

#### Scenario: Show human action
- **WHEN** an owned project has a workflow or unit waiting for human input
- **THEN** Home shows a pending card linking to the existing production action and labels it as human input

#### Scenario: Show review and delivery decisions
- **WHEN** an owned project has a current candidate awaiting approval, authorization, or unknown reconciliation
- **THEN** Home shows the corresponding decision card linking to `/review` and does not claim approval or delivery completion

#### Scenario: Show identity and production risks
- **WHEN** an active unit has `identity_unready`, blocked, or stale state
- **THEN** Home shows distinct risk cards and links to the existing project/matrix or production resolution path

#### Scenario: Decision precedence and deduplication
- **WHEN** the same entity yields multiple pending facts, including an unresolved unknown delivery result
- **THEN** Home orders unknown first and shows at most one card per stable code and entity reference without hiding distinct issues

Home MAY additionally surface LearningCandidate validation when a candidate is `ready_for_review`. Learning remains the authoritative source and Home MUST NOT create a duplicate learning task/state. Operational production/review risks retain higher precedence than learning validation.

#### Scenario: Learning validation pending
- **WHEN** an owned LearningCandidate is ready_for_review
- **THEN** Home shows a pending decision linking to `/learning` without changing candidate status
