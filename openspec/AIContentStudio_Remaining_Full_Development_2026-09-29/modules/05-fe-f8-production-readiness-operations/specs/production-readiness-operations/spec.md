## ADDED Requirements

### Requirement: Development-header auth is development-only
Production mode SHALL reject development-header authentication and use a secure authenticated identity mapped to existing User/Role authorization.

### Requirement: Secrets never escape safe surfaces
Plaintext credentials, tokens, cookies, credential-bearing URLs and raw secret values MUST NOT appear in safe APIs, logs, errors or capability verification metadata.

### Requirement: Storage is replaceable infrastructure
MaterialRevision business identity SHALL remain stable while immutable bytes are read/written through a replaceable storage provider with exact hash verification.

### Requirement: Operations are correlated without becoming business truth
Requests, workers and external capabilities SHALL emit structured correlation/audit metadata linking project/run/master/variant/candidate/target where available. Logs MUST NOT replace persisted business state.

### Requirement: Production health/readiness is explicit
The system SHALL expose safe liveness/readiness checks for required infrastructure and fail readiness when core DB/migration/storage/runtime dependencies are invalid.

### Requirement: External capabilities are treated as untrusted
External calls SHALL use least privilege, bounds, authorization, idempotency, audit and side-effect gates. Read-only views MUST NOT trigger network side effects.

### Requirement: Recovery preserves history
Backup/restore/migration procedures SHALL preserve historical content/evidence/identity/approval records and never fabricate rollback data.

### Requirement: Identity and Content Golden suites are first-class acceptance
The project SHALL maintain versioned Golden fixtures for identity behavior and content/evidence/channel quality in addition to unit tests.

### Requirement: Integration acceptance crosses ChannelVariant
The production integration test SHALL cover Opportunity through ChannelVariant/Candidate/Delivery/Receipt/Learning rather than stopping at Master.

### Requirement: Publisher verification requires real platform evidence
A remote Publisher capability MUST NOT be marked verified without actual delivery plus read-back or explicit human verification appropriate to the platform.
