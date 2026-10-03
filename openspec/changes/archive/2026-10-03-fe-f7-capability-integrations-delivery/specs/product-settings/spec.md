## ADDED Requirements

### Requirement: Capability inventory separates configuration from verification
Product Settings SHALL project existing typed Plugin, Connector, Channel and model truth with bounded CapabilityRegistration/Verification safe metadata. It SHALL distinguish discovered, configured, executable, verified and unavailable for exact kind/key/version/scope and explain missing or invalid verification. A read MUST NOT probe networks or imply an editable action without durable mutation support and caller permission.

#### Scenario: Configured but unverified Publisher
- **WHEN** a Publisher implementation and account configuration exist without valid scoped real-account verification
- **THEN** Settings displays the safe configuration and an unavailable remote action reason, not a verified badge

#### Scenario: Verification expired or config changed
- **WHEN** stored evidence expires or its config fingerprint differs from the active runtime
- **THEN** Settings shows the scope as no longer verified without deleting the historical evidence

### Requirement: Explicit capability actions retain role and redaction gates
Capability probe and verification actions SHALL be separately labeled, authorized and audited; remote side-effect verification SHALL require explicit account/action confirmation. Safe API projections MUST exclude nested provider secrets and credential-bearing errors as well as existing Settings secret fields.

#### Scenario: Viewer clicks verify
- **WHEN** a viewer invokes a capability verification action
- **THEN** authorization rejects it without a provider call or verification record

#### Scenario: Provider returns sensitive diagnostic
- **WHEN** a probe error contains a signed URL or token in a nested response
- **THEN** the Settings response and persisted audit expose only an allowlisted reason code
