## ADDED Requirements

### Requirement: Single-machine production is the final formal deployment
The owner's computer, SQLite, the configured local immutable media library and loopback-only API/Web SHALL be the final production and acceptance deployment, not a temporary stage pending serverization. Existing startup, local identity, credential configuration and required Worker topology SHALL remain unchanged for this documentation correction. PostgreSQL, MinIO, JWT, independent Secret Provider, containers and reverse proxy MUST NOT become prerequisites merely for the production label. The accepted 82/82 evidence SHALL remain valid; original 18 unchecked entries SHALL remain out-of-scope, unverified extension records rather than current production blockers.

Literal `APP_ENV=production` below denotes an existing technical server-extension branch, not the user's formal-use status. Its identity/startup/Secret Provider activation conditions are conditional extension contracts only; they MUST NOT be inferred as requirements to change this computer's current runtime. Paired database/media backup, restored hash integrity, secret masking, traceable errors, exact authorized external calls, no Unknown automatic retry and protection of real data remain mandatory in single-machine production.

#### Scenario: Formal use without server infrastructure
- **WHEN** the owner formally uses the accepted SQLite/local-media/loopback installation without PostgreSQL, MinIO, JWT or an independent Secret Provider
- **THEN** the deployment is classified as single-machine production with its accepted 82/82 scope complete, not blocked or described as temporary due to those absent extensions

#### Scenario: Production terminology is corrected
- **WHEN** the specifications and runbooks are aligned to the final single-machine use plan
- **THEN** runtime APP_ENV, database/schema, material paths, credentials, existing identity behavior and Worker topology remain unchanged, with no new dependencies, migrations, service operations or external acceptance calls

#### Scenario: Authorized outbound operation from loopback application
- **WHEN** an authorized model or WeChat operation is requested from the loopback-only application
- **THEN** the existing credential isolation, capability authorization and outbound safety apply; loopback limits inbound access and does not itself prohibit outbound calls

### Requirement: Production identity cannot use development headers
The optional technical `APP_ENV=production` server-extension mode SHALL reject `X-Studio-User`, default-user, mock and auto-create-user authentication. It SHALL validate a configured signed identity and map it to an existing active Studio User; authorization SHALL use that User's durable role rather than an untrusted role claim. Existing development/test-labeled Header mode MAY remain unchanged for the final loopback-only single-machine production installation; this extension requirement does not force its activation or an identity migration.

The mapping from a configured issuer's stable subject to an existing User MUST be explicitly reviewed and fail closed for unknown or ambiguous subjects. A token email or role claim alone MUST NOT silently bind an account. If the approved mapping requires new durable persistence beyond the current User table, F8 SHALL pause for a separately reviewed specification/migration decision rather than assuming email-only equivalence.

#### Scenario: Spoofed header in production
- **WHEN** a request supplies `X-Studio-User: admin@studio.local` without a valid configured production identity
- **THEN** the protected API denies the request without returning private data or creating a User

#### Scenario: Unknown or inactive subject
- **WHEN** a token is otherwise valid but its mapped User is missing or inactive
- **THEN** the request is denied without auto-provisioning or promoting a token role claim

#### Scenario: Verified token has an unbound subject
- **WHEN** a correctly signed token presents an email matching a Studio User but its issuer/subject has no approved unambiguous binding
- **THEN** production authentication denies the request instead of inferring the User from that email

### Requirement: Production startup fails closed on unsafe configuration
Startup in the optional technical `APP_ENV=production` server-extension mode SHALL validate auth, required secrets, schema-head compatibility and required runtime configuration before accepting traffic. It MUST NOT silently create tables, migrate/downgrade a database or mutate approved templates/settings as part of service boot. The single-machine production deployment SHALL keep existing local runtime/startup behavior; this correction MUST NOT activate the extension flag, run seed/migration or overwrite real data.

#### Scenario: Header auth mode selected
- **WHEN** production is configured with development-header authentication or a missing signing configuration
- **THEN** service startup fails with a safe reason and does not serve protected routes

#### Scenario: Schema behind application
- **WHEN** the database migration head is incompatible with the application in production mode
- **THEN** readiness fails and startup does not perform an automatic migration

### Requirement: Secrets remain out of safe surfaces
Plaintext credentials, cookies, signed URLs, credential-bearing URLs, secret headers and raw secret values MUST NOT appear in safe API, log, metric, health, audit, worker or capability-verification output. The final single-machine production deployment SHALL retain safe local credential configuration and the recorded inventory without silently deleting/migrating overrides. Enabling the optional technical server-extension Secret Provider policy SHALL deliberately remediate applicable overrides rather than treating masked display as secure storage; that cutover is not a prerequisite for current formal use.

#### Scenario: Stored override exists
- **WHEN** an explicitly enabled technical server-extension startup encounters a legacy persisted secret override without an approved migration/disable policy
- **THEN** readiness is blocked with a safe reason that does not reveal the value

#### Scenario: Provider raises a credential-bearing exception
- **WHEN** an external adapter error contains a token or signed URL
- **THEN** all returned and persisted diagnostics expose only allowlisted fields and a safe error category

#### Scenario: Legacy worker or audit payload contains private data
- **WHEN** a Workflow worker raises an arbitrary exception or stored audit telemetry contains unknown/private fields
- **THEN** the worker returns/logs only a fixed category and the audit read rebuilds bounded allowlisted metadata rather than echoing the stored object

#### Scenario: Persisted signed storage URL or signing secret
- **WHEN** a persisted override contains a nonempty signing-secret/header field or an AWS/GCS/OSS/Azure signed URL, including vendor-prefixed credential or signature query names
- **THEN** the technical server-extension secret policy rejects it with a fixed safe reason, while reference names/public configuration remain usable and safe local projections never disclose values

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

#### Scenario: Legacy telemetry has the wrong value type
- **WHEN** stored telemetry contains a JWT-shaped trace, text in a numeric entity ID, or a boolean entity ID
- **THEN** the field-specific metadata projection drops those values while preserving valid bounded trace, actor and integer identifiers

### Requirement: Metrics are bounded and safe
Operational metrics SHALL use route templates or another bounded label set instead of raw dynamic paths or private IDs. Metrics access SHALL be protected or intentionally restricted, and MUST NOT disclose secrets or content bodies.

#### Scenario: Many project IDs requested
- **WHEN** requests address thousands of distinct project IDs under the same route
- **THEN** their metric labels aggregate under a bounded route identity rather than creating one series per raw ID

#### Scenario: Arbitrary HTTP methods requested
- **WHEN** requests contain methods outside the supported finite HTTP method set
- **THEN** metrics aggregate them under one `OTHER` label, including unmatched paths

### Requirement: Liveness and readiness report actual required dependencies
The existing health surface SHALL distinguish liveness from readiness. Readiness SHALL validate required DB/schema, selected local storage and configured worker/queue dependencies, with auth/secret checks appropriate to the actual unchanged runtime branch; it SHALL return a non-success status and safe reason on required failure. Missing server-extension components alone MUST NOT classify the accepted single-machine production deployment as unready. Optional disconnected providers SHALL remain visible as unavailable without making core readiness fail or triggering network calls on ordinary reads.

#### Scenario: Database unavailable
- **WHEN** the database cannot be reached
- **THEN** readiness returns a non-success status and a safe DB reason code, not raw exception text or an HTTP 200 degraded body

#### Scenario: Local approved schema with a pending draft
- **WHEN** the formal loopback-only local database is at approved `aco000000001` after separately authorized enablement while unrelated descendant work remains unapproved
- **THEN** readiness verifies that exact approved database head and its application migration ancestry instead of skipping the check or requiring the unapproved migration
- **AND** missing, multiple or different database heads fail with a safe schema reason; only the separately selected technical server-extension profile requires exact code/config/database head equality

#### Scenario: Nullable identity ancestry does not activate authentication
- **WHEN** the approved local `aco000000001` ancestry includes `f8a000000001` and User issuer/subject columns remain null/inert
- **THEN** readiness and recovery use the approved aco target without claiming JWT/production identity enabled or verified, preserve historical f7d acceptance, and never downgrade the formal SQLite to reconcile outdated documentation

#### Scenario: Optional Provider disconnected
- **WHEN** a non-required external provider has no credentials
- **THEN** core readiness can remain ready while that Provider's capability status remains unverified/unavailable

#### Scenario: Selected local storage is missing
- **WHEN** the configured local store cannot be accessed, even outside production mode
- **THEN** readiness returns a non-success status and a fixed storage reason without creating a directory or silently selecting a different provider

#### Scenario: Queue reachable without a worker
- **WHEN** a required queue is reachable but its bounded worker probe has no valid pong response
- **THEN** readiness remains failed; broker connectivity alone is not worker availability

### Requirement: External capabilities remain untrusted in production
Every external capability SHALL enforce existing authorization, bounded outbound host/redirect/body/time policies, credential isolation, audit, side-effect confirmation, idempotency and Unknown reconciliation. Read-only inventory, Home, Settings and health views MUST NOT trigger provider pull, probe or publication.

#### Scenario: Read Settings
- **WHEN** a viewer opens capability inventory
- **THEN** no external call or side-effect attempt is initiated

#### Scenario: Read legacy Settings
- **WHEN** an administrator reads the retained legacy settings inventory
- **THEN** dsh reachability remains explicitly `not_probed` and no HTTP request is made; the UI does not label this as offline or verified

#### Scenario: Legacy fetch redirects or exceeds its bound
- **WHEN** a legacy import/Connector response exceeds its byte/time budget or redirects to a different origin
- **THEN** reading aborts in flight and a credentialed request is not forwarded to that origin; redirects remain bounded and validated

#### Scenario: Query-bearing fetch changes origin
- **WHEN** a redirect changes origin and the original URL, current hop or destination contains query parameters
- **THEN** the fetch rejects the redirect before sending to the new origin rather than attempting to guess which query parameters carry credentials

#### Scenario: Remote side effect times out
- **WHEN** a Publisher request has an ambiguous outcome
- **THEN** it remains unknown/reconciliation-needed and no automatic retry or alternate Publisher is invoked

#### Scenario: Generation needs a longer bounded budget
- **WHEN** a text or image generation operation uses the centralized outbound policy
- **THEN** it retains a capability-appropriate finite generation budget rather than inheriting the short discovery/import timeout, with bounded request/response bodies and no automatic retry

#### Scenario: Operator restricts outbound hosts
- **WHEN** the optional exact-host allowlist is configured and a controllable HTTP target is absent, or the list contains a wildcard/invalid entry
- **THEN** the operation is rejected before DNS or credential transmission, without weakening its existing public-address, TLS or trusted-private-endpoint checks

#### Scenario: Remote response trickles headers or body
- **WHEN** a response continuously trickles bytes below the per-read idle timeout
- **THEN** one absolute operation deadline bounds DNS, TCP, TLS and every socket read/write across redirects; already-dispatched generation remains Unknown on expiry

#### Scenario: Signed query URL is fetched
- **WHEN** an import or download URL includes query credentials, including on an allowed redirect
- **THEN** third-party HTTP client/transport logs are suppressed within that outbound operation and cannot emit the URL, header, body or raw exception; safe operation metadata remains available

### Requirement: Recovery preserves exact historical truth
For final single-machine production, backup/restore rehearsals SHALL use SQLite and its same-snapshot referenced immutable local media set, verify schema compatibility and bytes, and preserve frozen Identity/Evidence/Master/Variant/Candidate/Approval/Delivery lineage. PostgreSQL/MinIO is non-applicable extension reference, not a planned upgrade or formal-use gate. Migration or real-data replacement requires separate authorization; downgrade MUST require a preflight and MUST NOT delete incompatible history to make rollback appear successful.

#### Scenario: Restore missing approved media
- **WHEN** a restored database references approved media absent from the restored byte store
- **THEN** the rehearsal fails with an explicit integrity finding rather than declaring recovery successful

#### Scenario: SQLite integrity fails
- **WHEN** either the source or restored SQLite integrity result is not `ok`
- **THEN** the rehearsal returns a nonzero exit status and cannot be recorded as recovery PASS

#### Scenario: Backup integrity inspects its source
- **WHEN** the rehearsal opens the source for backup or integrity inspection
- **THEN** it uses a read-only SQLite URI and never opens that source in writable mode

#### Scenario: Source database filename contains URI delimiters
- **WHEN** a source path contains question marks or fragment delimiters
- **THEN** the rehearsal encodes the exact filesystem path and backs up that database read-only, not another truncated path

#### Scenario: Shared storage key has conflicting revisions
- **WHEN** multiple references to one key require different content hashes
- **THEN** each reference is validated before copy deduplication, the mismatch returns a nonzero status and cutover readiness remains false

#### Scenario: Incompatible downgrade
- **WHEN** a downgrade would discard required later-version history
- **THEN** the downgrade is refused and the operator uses a non-destructive recovery path

#### Scenario: Retention encounters frozen production lineage
- **WHEN** an expired WorkflowRun is project-bound or referenced by an immutable attempt or production artifact, or an LLMRun holds a validated Text/Variant receipt
- **THEN** retention preserves that historical lineage and structured receipt; it may prune raw provider payloads without breaking exact historical validation

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

The local branch MAY complete at authorized package/handoff; it SHALL enter PublishedContentRecord and subsequent Performance/Learning only after real publication is separately attested by a qualifying `human_confirmed` DeliveryReceipt with `delivered_at`, exact Candidate/Target/hash and owner validation. An unresolved Unknown, package-ready target or ZIP download MUST NOT be counted as published or as downstream learning acceptance.

#### Scenario: Complete local chain
- **WHEN** all three modality Masters and a channel Variant are produced in an isolated environment
- **THEN** the approved Candidate and local DeliveryTarget retain exact frozen lineage through handoff; without a separate qualifying human-confirmed publication Receipt, the published-history and learning branch remains not exercised

#### Scenario: Real publication confirmed after manual handoff
- **WHEN** an owner separately confirms actual publication with a qualifying `human_confirmed` Receipt, `delivered_at` and matching frozen Candidate/Target/hash
- **THEN** PublishedContentRecord and subsequent Performance/Learning may be exercised with that exact provenance rather than a fabricated publication time or remote success

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
