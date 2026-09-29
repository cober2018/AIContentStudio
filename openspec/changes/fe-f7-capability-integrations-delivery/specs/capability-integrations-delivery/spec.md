## ADDED Requirements

### Requirement: Capability descriptors are versioned and replaceable
The system SHALL resolve a supported capability by exact kind, key and version while keeping Studio workflow, Master, Variant, Candidate and Delivery truth independent of implementation. Legacy registry kinds and historical references MUST remain readable.

#### Scenario: Missing implementation
- **WHEN** a registration exists without a matching loaded executor version
- **THEN** inventory reports unavailable and execution fails without importing code from registration metadata

#### Scenario: Existing plugin key
- **WHEN** an existing node, rule, renderer or publisher key is resolved at its recorded version
- **THEN** its original implementation and historical run references remain available under the compatibility boundary

### Requirement: Verification is durable, scoped and invalidatable
The system SHALL keep safe registration metadata and append-only verification evidence separately from secrets. Runtime verification MUST match exact kind/key/version/config fingerprint and the action's typed scope, remain unexpired and not invalidated, and be rechecked at execution time.

#### Scenario: Config rotation
- **WHEN** a provider's executable configuration fingerprint changes after verification
- **THEN** the old verification remains auditable but no longer authorizes new execution

#### Scenario: Registration is not verification
- **WHEN** a plugin is installed or enabled but has no valid verification for the requested scope
- **THEN** inventory distinguishes configuration from verification and the gated action remains unavailable

### Requirement: Capability records and results are safe projections
The system MUST NOT persist or return secrets, cookies, tokens, credential-bearing URLs, signed media URLs, headers, raw provider responses, local credential paths or unredacted exception text in registration, verification, API result, AuditLog, ProjectEvent or delivery metadata. Provider output MUST be treated as untrusted data rather than instructions.

#### Scenario: Nested provider error contains token
- **WHEN** a provider returns a nested error with a token, signed URL or request header
- **THEN** every stored and returned diagnostic contains only allowlisted safe fields and a non-sensitive reason code

#### Scenario: Provider prompt injection
- **WHEN** a search or Connector response contains operational instructions
- **THEN** the payload is processed only as source data under the typed mapping and cannot change authorization, capability status or system instructions

### Requirement: Connector capability mapping is explicit
A generic Connector or ConnectorEndpoint SHALL become a Data Source executor only through an authorized mapping to one typed Data Source Plugin and exact endpoint/version. Mapping MUST NOT enable unrelated plugin keys. Execution SHALL retain existing Connector authorization, bounded fetch and SourceDocument/Fact behavior and create a DataSnapshot with immutable source/version/checksum/lineage for a Workflow Data Node.

#### Scenario: Generic Connector configured
- **WHEN** an API Connector exists with no typed Data Source mapping
- **THEN** `api`, `notion`, `sql` and other disconnected plugin keys remain unavailable

#### Scenario: Mapped node refresh
- **WHEN** an authorized mapped Data Node refreshes and normalized output changes
- **THEN** a new snapshot records exact ConnectorEndpoint/source identity and existing dependent outputs become stale

#### Scenario: Failed pull
- **WHEN** a mapped endpoint times out, exceeds limits or fails authorization
- **THEN** no successful snapshot or new Fact Boundary is fabricated

### Requirement: Search output is not a usable asset
Search providers SHALL return bounded candidate metadata only. Explicit import MUST validate source, downloaded bytes, hash, MIME and rights/license before creating an immutable MaterialRevision or attaching it to a Project.

#### Scenario: Preview URL selected without rights
- **WHEN** a user selects a search preview whose license or public-use status is unknown
- **THEN** it remains a candidate and cannot be used as a public-ready Master/Variant asset

#### Scenario: Accepted search result
- **WHEN** validated bytes and a permitted rights decision are explicitly accepted
- **THEN** one exact MaterialRevision is stored with source/provenance and any Project reuse references that revision rather than copying bytes

### Requirement: Generated media and renderer output require exact acceptance
Image, video, TTS and renderer providers SHALL return bounded untrusted results. Only explicitly accepted, byte-verified output with exact provider/version, input/request hash, MIME, license and rights status SHALL become MaterialRevision. A Master or Variant SHALL change only through its own explicit revision save. No provider success flag, remote URL or preview alone SHALL count as generated media.

#### Scenario: Provider reports success without bytes
- **WHEN** a provider returns a success status but media cannot be fetched, decoded, hashed or licensed
- **THEN** no MaterialRevision, project attachment, Master update or render attestation is created

#### Scenario: Different render input
- **WHEN** the Master payload/context/asset-set hash differs from the renderer's recorded input hash
- **THEN** the result cannot attest the current Master or make its Candidate freeze-ready

#### Scenario: Accepted cross-unit media
- **WHEN** an authorized Project user accepts generated media and attaches its exact revision to the Project
- **THEN** another Unit in that Project can select the shared revision subject to current rights without claiming the generating Unit owns it exclusively

### Requirement: ASR and transforms remain suggestions until saved
ASR transcripts/cues and provider transforms SHALL be bounded outputs with source audio/video and provider lineage; they MUST NOT implicitly mutate a Video Master, Graphic Master or ChannelVariant.

#### Scenario: Transcript received
- **WHEN** ASR returns cues for an exact audio revision
- **THEN** the cues remain a proposal until an authorized explicit new Master revision saves them

### Requirement: Publisher verification is exact to the action
Remote Publisher verification MUST bind platform/channel, stable account identity and frozen account reference, content form, action, publisher key/version, config fingerprint and validity time. A verified result requires explicit real-account verification with read-back or documented human evidence. Registration, local mocks, a Settings read, a provider `verified()` boolean or a successful unrelated action MUST NOT verify a new scope.

#### Scenario: Another account or form
- **WHEN** `wechat/account-A/article/auto_draft` is verified but authorization selects account B or another content form
- **THEN** the new remote action is unavailable

#### Scenario: WeWrite unverified legacy flag
- **WHEN** a legacy `allow_unverified_auto_draft` flag is enabled but no scoped verification exists
- **THEN** the flag does not permit a new remote side effect; historical DeliveryTarget/Attempt reads remain available

### Requirement: Publisher consumes approved immutable content
Every remote Publisher action SHALL require exact approved Candidate hash and Delivery Authorization, validate live account/capability/rights, and receive only the frozen approved content/package. The Publisher MUST NOT rewrite, truncate, adapt, generate media or silently switch providers after approval. Local copy/manual package remains a distinct non-remote path when packageable.

#### Scenario: Publisher wants shorter title
- **WHEN** frozen approved content exceeds a remote platform limit
- **THEN** delivery fails with an actionable validation reason and no modified remote payload is sent

#### Scenario: Unverified remote fallback
- **WHEN** remote capability is unavailable but a local package is valid
- **THEN** the user may explicitly choose a separately authorized copy/manual target; no automatic remote-to-local or provider substitution creates a false receipt

### Requirement: Unknown remote outcome remains unretried
Remote attempts SHALL persist an idempotency identity before external action. Timeout or ambiguous result SHALL remain unknown/reconciliation-needed and MUST NOT be automatically retried, marked published or silently sent via another provider.

#### Scenario: Timeout after request
- **WHEN** remote execution times out after the request may have reached the platform
- **THEN** the attempt is unknown and only an explicit audited reconciliation can permit a later action

### Requirement: Real acceptance is scoped and honest
Verification or a user-visible `verified` state SHALL require actual configured endpoint/account evidence for that exact scope. Missing credentials or account authorization SHALL be reported as unverified, not replaced by a mock success. Read-only inventory MUST NOT issue probes or side effects.

#### Scenario: No external credentials
- **WHEN** local tests pass but no real account credential or confirmation is available
- **THEN** the capability can be implemented and executable in mock/isolated scope but remains externally unverified

#### Scenario: Settings inventory read
- **WHEN** a viewer opens capability inventory
- **THEN** it returns bounded safe status without invoking a Connector, model, Renderer or Publisher
