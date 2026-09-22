## ADDED Requirements

### Requirement: Target authorization is separate from content approval
The system SHALL create one DeliveryTarget per platform/account/action and SHALL bind its authorization to an approved content hash and authorization version.

#### Scenario: Account change requires new target authorization
- **WHEN** an approved candidate is assigned to a different account
- **THEN** the system requires a new target authorization
- **AND** unchanged approved content does not require content reapproval solely because the account changed

#### Scenario: Content change requires both approvals to match
- **WHEN** candidate content changes after target authorization
- **THEN** the old target authorization cannot be used for the new content hash
- **AND** handoff remains blocked until content approval and target authorization reference the same candidate

### Requirement: M1 targets are manual and channel-limited
This change SHALL permit manual handoff targets for WeChat articles and X Threads only, and SHALL NOT authorize a remote draft, publish, schedule, or automatic external retry action.

#### Scenario: WeChat automatic draft is not available to M1
- **WHEN** a user prepares a WeChat M1 target
- **THEN** the available M1 action is complete-package manual handoff
- **AND** the target cannot invoke the remote WeChat draft integration

#### Scenario: Unsupported channel is rejected
- **WHEN** a user attempts to create an M1 target for another platform or X content form
- **THEN** the system rejects the target as outside this change

### Requirement: Handoff packages are complete, deterministic, and public-safe
The system SHALL build a package from the authorized approved manifest containing final public text, actual ordered public media, publishable citations and declarations, a manifest, and manual instructions.

#### Scenario: Package matches approved content
- **WHEN** a package is prepared for an authorized target
- **THEN** its text, media hashes/order, citations, and declarations match the approved content hash
- **AND** stale or unapproved material prevents package-ready status

#### Scenario: Internal evidence is not bundled by default
- **WHEN** a package is generated
- **THEN** raw private FactPack data, private source originals, and media without public rights are excluded

### Requirement: Manual delivery receipts preserve provenance
The system SHALL record manual receipt provenance including target, approved hash, operator, actual action, event time, link or evidence reference, and verification method, and SHALL label it as human-confirmed unless separately platform-verified.

#### Scenario: Human confirms a completed handoff
- **WHEN** the operator submits a valid receipt for a package-ready target
- **THEN** the target records the receipt and human-confirmed provenance
- **AND** the system does not claim automatic or platform-verified publication

#### Scenario: Missing receipt remains visible
- **WHEN** a package has been downloaded but no receipt is provided
- **THEN** the target remains awaiting manual confirmation rather than published

### Requirement: Delivery intents and receipt updates are idempotent
The system SHALL reuse an existing target for the same approved hash, platform, account, action, and authorization version, and SHALL make repeated receipt updates idempotent.

#### Scenario: Duplicate target request does not create duplicate intent
- **WHEN** the same authorized target request is submitted more than once
- **THEN** the system returns the existing target instead of creating another delivery intent

#### Scenario: Unknown human outcome requires reconciliation
- **WHEN** a manual handoff is interrupted or its result is unknown
- **THEN** the system records a reconciliation-needed state
- **AND** it does not claim exactly-once human or platform execution

### Requirement: Targets progress independently
The state of one M1 DeliveryTarget SHALL NOT block or overwrite the state of another target for the same approved content.

#### Scenario: One target fails while another completes
- **WHEN** the X Thread target fails validation or remains pending while the WeChat target receives a valid receipt
- **THEN** the WeChat target may complete independently
- **AND** the X target retains its own actionable state

### Requirement: Minimal feedback is linked to the content flow
The system SHALL allow at least one explicit satisfaction, audience, or correction feedback record to be linked to the delivered target or source topic.

#### Scenario: Operator records post-handoff feedback
- **WHEN** feedback is entered after manual handoff
- **THEN** the system records its source, time, and target or topic relationship
- **AND** it does not automatically change upstream product data

### Requirement: Legacy delivery paths cannot grant M1 state
Existing exports, workflow states, retries, and direct external calls MUST NOT create a new M1 delivered or receipt-confirmed state without a matching approved hash and target authorization.

#### Scenario: Legacy export is not publication proof
- **WHEN** an existing ContentAsset has only an ExportRecord or legacy published flag
- **THEN** the system does not treat it as an M1 receipt or platform-verified publication

#### Scenario: Legacy automatic call cannot bypass the M1 gate
- **WHEN** a workflow resume, retry, or direct handler attempts an external action for new M1 content without a supported automatic action and matching authorization
- **THEN** the external call is blocked
- **AND** the manual package path remains available
