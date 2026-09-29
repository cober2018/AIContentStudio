## ADDED Requirements

### Requirement: Production identity cannot use development headers
Production mode SHALL reject `X-Studio-User`, default-user, mock and auto-create-user authentication. It SHALL validate a configured signed identity and map it to an existing active Studio User; authorization SHALL use that User's durable role rather than an untrusted role claim. Development/test Header mode MAY remain available only outside production.

#### Scenario: Spoofed header in production
- **WHEN** a request supplies `X-Studio-User: admin@studio.local` without a valid configured production identity
- **THEN** the protected API denies the request without returning private data or creating a User

#### Scenario: Unknown or inactive subject
- **WHEN** a token is otherwise valid but its mapped User is missing or inactive
- **THEN** the request is denied without auto-provisioning or promoting a token role claim

### Requirement: Production startup fails closed on unsafe configuration
Production startup SHALL validate auth, required secrets, schema-head compatibility and required runtime configuration before accepting traffic. It MUST NOT silently create tables, migrate/downgrade a database or mutate approved templates/settings as part of service boot. Development/test bootstrap MAY retain explicit local behavior.

#### Scenario: Header auth mode selected
- **WHEN** production is configured with development-header authentication or a missing signing configuration
- **THEN** service startup fails with a safe reason and does not serve protected routes

#### Scenario: Schema behind application
- **WHEN** the database migration head is incompatible with the application in production mode
- **THEN** readiness fails and startup does not perform an automatic migration

### Requirement: Secrets remain out of safe surfaces
Plaintext credentials, cookies, signed URLs, credential-bearing URLs, secret headers and raw secret values MUST NOT appear in safe API, log, metric, health, audit, worker or capability-verification output. Production enablement SHALL inventory and deliberately remediate any existing plaintext SystemSetting override rather than treating masked display as secure storage.

#### Scenario: Stored override exists
- **WHEN** a production startup encounters a legacy persisted secret override without an approved migration/disable policy
- **THEN** readiness is blocked with a safe reason that does not reveal the value

#### Scenario: Provider raises a credential-bearing exception
- **WHEN** an external adapter error contains a token or signed URL
- **THEN** all returned and persisted diagnostics expose only allowlisted fields and a safe error category

### Requirement: Immutable media uses a replaceable storage boundary
MaterialRevision SHALL retain its business ID, exact content hash and rights while its bytes are accessed through a configured local/object StorageProvider. Candidate, Review and Delivery reads MUST verify actual bytes against the frozen hash and fail closed on missing/corrupt data. Legacy media and all direct read/write paths SHALL be covered before storage cutover; safe APIs MUST NOT disclose internal storage locations.

#### Scenario: Object differs from revision hash
- **WHEN** stored object bytes do not match an approved MaterialRevision hash
- **THEN** Candidate/package media access is blocked without falling back to another path or emitting a false delivery receipt

#### Scenario: Partial storage migration
- **WHEN** some referenced historical media have not been copied and verified in the selected production store
- **THEN** the new storage mode is not declared ready and no silent mixed-root success is reported

### Requirement: Correlation is safe telemetry, not business state
Requests and asynchronous workers SHALL propagate a bounded correlation ID through Workflow, capability, Master/Variant, Candidate and Delivery operations, recording permitted actor/project/unit/run/attempt/version/status/duration metadata. Structured telemetry MUST NOT replace persisted Run, Attempt, Candidate, Review or Receipt truth or log private content by default.

#### Scenario: Trace from request to delivery attempt
- **WHEN** an authorized request starts work that later creates a DeliveryAttempt
- **THEN** safe telemetry can correlate the operations while the attempt's persisted state remains the source of truth

### Requirement: Metrics are bounded and safe
Operational metrics SHALL use route templates or another bounded label set instead of raw dynamic paths or private IDs. Metrics access SHALL be protected or intentionally restricted, and MUST NOT disclose secrets or content bodies.

#### Scenario: Many project IDs requested
- **WHEN** requests address thousands of distinct project IDs under the same route
- **THEN** their metric labels aggregate under a bounded route identity rather than creating one series per raw ID

### Requirement: Liveness and readiness report actual required dependencies
The existing health surface SHALL distinguish liveness from readiness. Readiness SHALL validate required DB/schema, auth/secret, selected storage and configured worker/queue dependencies, and return a non-success HTTP status with a safe reason when a required dependency fails. Optional disconnected providers SHALL remain visible as unavailable without making core readiness fail or triggering network calls on ordinary reads.

#### Scenario: Database unavailable
- **WHEN** the database cannot be reached
- **THEN** readiness returns a non-success status and a safe DB reason code, not raw exception text or an HTTP 200 degraded body

#### Scenario: Optional Provider disconnected
- **WHEN** a non-required external provider has no credentials
- **THEN** core readiness can remain ready while that Provider's capability status remains unverified/unavailable

### Requirement: External capabilities remain untrusted in production
Every external capability SHALL enforce existing authorization, bounded outbound host/redirect/body/time policies, credential isolation, audit, side-effect confirmation, idempotency and Unknown reconciliation. Read-only inventory, Home, Settings and health views MUST NOT trigger provider pull, probe or publication.

#### Scenario: Read Settings
- **WHEN** a viewer opens capability inventory
- **THEN** no external call or side-effect attempt is initiated

#### Scenario: Remote side effect times out
- **WHEN** a Publisher request has an ambiguous outcome
- **THEN** it remains unknown/reconciliation-needed and no automatic retry or alternate Publisher is invoked

### Requirement: Recovery preserves exact historical truth
Backup/restore and migration rehearsals SHALL use an isolated PostgreSQL restore plus the referenced immutable media set, verify schema compatibility and sampled bytes, and preserve frozen Identity/Evidence/Master/Variant/Candidate/Approval/Delivery lineage. Downgrade MUST require a preflight and MUST NOT delete incompatible historical records to make rollback appear successful.

#### Scenario: Restore missing approved media
- **WHEN** a restored database references approved media absent from the restored byte store
- **THEN** the rehearsal fails with an explicit integrity finding rather than declaring recovery successful

#### Scenario: Incompatible downgrade
- **WHEN** a downgrade would discard required later-version history
- **THEN** the downgrade is refused and the operator uses a non-destructive recovery path

### Requirement: Identity and Content Golden evidence is versioned
The project SHALL maintain versioned Identity Golden and Content Golden fixtures covering voice/boundaries, Persona differentiation, historical snapshot pinning, fact/Brief adherence, Text/Graphic/Video direction and channel adaptation. Deterministic checks SHALL remain separate from non-deterministic model-quality review; any such review SHALL record provider/model/version, exact input/output identity and human decision where required.

#### Scenario: Historical identity changes
- **WHEN** a Persona's current voice changes after an older ContentUnit/Run was created
- **THEN** the Golden evaluation checks that the older frozen IdentitySnapshot remains the historical basis

#### Scenario: Model quality is reviewed
- **WHEN** a generative output is judged for voice or style quality
- **THEN** the record identifies model/runtime and reviewer rather than reporting a deterministic unit-test pass

### Requirement: Full integration acceptance crosses ChannelVariant
An isolated integration acceptance SHALL exercise Opportunity → Project → Identity → CreativeBrief/Fact Boundary → Matrix → Text/Graphic/Video Masters → ChannelVariant → Candidate → Content Approval → Delivery Authorization → local or verified delivery → Receipt → Performance/Learning. Each transition's ownership, exact revision/checksum, rights and runtime provenance SHALL be queryable. A local package or attempt status MUST NOT stand in for a published receipt.

#### Scenario: Complete local chain
- **WHEN** all three modality Masters and a channel Variant are produced in an isolated environment
- **THEN** the approved Candidate and local DeliveryTarget retain exact frozen lineage through the downstream feedback/Learning path without claiming remote publication

#### Scenario: Unknown delivery
- **WHEN** a remote attempt is unknown or failed
- **THEN** PublishedContentRecord and Learning do not treat it as confirmed publication

### Requirement: Real Platform verification is exact and honest
A remote Publisher scope SHALL be marked verified only after separately authorized real-account execution plus platform read-back or documented human verification for that exact platform/account/form/action/version. Implementation complete, provider configured and Real Platform verified SHALL be reported independently; unavailable credentials MUST remain unverified.

#### Scenario: No real account supplied
- **WHEN** mock and isolated integration suites pass but no real account is authorized
- **THEN** code status may be complete while that remote capability is still reported unverified

#### Scenario: Verified account A does not imply account B
- **WHEN** one account's draft action is verified
- **THEN** another account/form/action remains unverified until its own evidence is recorded
