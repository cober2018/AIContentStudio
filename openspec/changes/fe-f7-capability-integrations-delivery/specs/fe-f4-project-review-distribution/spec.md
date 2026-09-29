## ADDED Requirements

### Requirement: Remote execution requires current scoped capability verification
New and legacy remote Delivery actions SHALL validate a current exact Publisher verification for platform, account, content form, action, version, config and time at execution, in addition to existing approved Candidate, DeliveryTarget, account, rights and idempotency gates. `allow_unverified_auto_draft` MUST NOT bypass the verification gate. Historical target/attempt/receipt reads SHALL remain intact; local copy/manual flow SHALL remain separately available when packageable.

#### Scenario: Legacy bypass flag present
- **WHEN** the legacy flag is enabled but the account/action has no valid scoped verification
- **THEN** no new remote attempt is sent and the user sees a safe unverified reason while old history remains readable

#### Scenario: Verification revoked after target authorization
- **WHEN** target authorization captured a valid capability but verification is revoked before execution
- **THEN** execution fails before preparing/sending a remote attempt without rewriting the frozen target history

### Requirement: Publisher preserves approved channel content and unknown state
Publisher SHALL consume the exact approved v3/v4/v5 schema-dispatched package and MUST NOT modify content or perform channel adaptation after approval. An ambiguous remote outcome SHALL remain unknown/reconciliation-needed without retry or fallback, preserving current Review/Home precedence.

#### Scenario: Remote formatting mismatch
- **WHEN** the selected remote platform rejects an approved title, media set or form
- **THEN** the Publisher records a safe failure and requires a new content revision/Candidate/approval instead of trimming or replacing content

#### Scenario: Timeout followed by another available Publisher
- **WHEN** an attempt is unknown and another Publisher is registered
- **THEN** no automatic switch or second remote effect occurs before explicit reconciliation
