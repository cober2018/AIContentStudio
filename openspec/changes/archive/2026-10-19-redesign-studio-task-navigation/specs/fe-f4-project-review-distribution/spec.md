## ADDED Requirements

### Requirement: Task-oriented review and handoff pages
The Review Center SHALL provide an addressable review queue and separate work verification, issue/approval, account authorization, handoff/receipt and history views while preserving existing project/unit/candidate deep links and immutable Candidate semantics. Search, state filtering and pagination SHALL survive return navigation. Navigation MUST NOT approve, authorize, deliver or reconcile.

#### Scenario: Select and return from a work
- **WHEN** the user opens a work from a filtered review queue and returns
- **THEN** queue filters/page remain and the work is not mutated by viewing any step

#### Scenario: Current blocking issue
- **WHEN** a selected work has blocked, stale or unknown facts
- **THEN** the current issue and next action remain visible while technical manifests and historical details are secondary

#### Scenario: Unknown or failed reads
- **WHEN** queue, candidate, accounts or delivery records cannot be loaded
- **THEN** the page preserves the failure rather than reporting an empty successful state and related unverified actions remain unavailable

### Requirement: Product review account entry without persona dependency
The project review read projection SHALL include the authoritative Unit production domain. Product review SHALL use the existing owned-account catalogue and MUST NOT query accounts under a null or inherited historical persona. Persona content SHALL retain its existing persona-account hierarchy. Frozen target channel/account checks and service authorization boundaries SHALL remain unchanged.

#### Scenario: Independent product work
- **WHEN** a product work has a null persona or retains a historical persona ID
- **THEN** the product account entry uses the owned account catalogue without requiring a persona or replacing the frozen account

### Requirement: Review interaction boundaries
The UI SHALL apply existing role and archive permissions, prevent duplicate pending mutations and preserve user/candidate-scoped in-progress inputs across step changes. Approval SHALL bind exact Candidate ID/hash; selected historical Candidates SHALL remain readable without current-Candidate mutation controls. Unknown SHALL require existing reconciliation; ZIP generation, draft delivery and human receipts MUST NOT be presented as public platform publication.

#### Scenario: Reader or unknown permission
- **WHEN** role permissions cannot be verified or the user has read-only access
- **THEN** all mutation controls are unavailable and historical records remain readable

#### Scenario: Candidate changes during navigation
- **WHEN** a user changes work or candidate before earlier reads complete
- **THEN** previous responses and in-progress inputs do not overwrite the new candidate's view or authorize actions against it

#### Scenario: Separate explicit decisions
- **WHEN** the user approves content
- **THEN** no delivery target is automatically authorized, no package is downloaded and no public publication is claimed
