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

Renderer verification SHALL use the existing registration and append-only verification records with exact renderer key/version, modality, payload schema, channel, content form and output MIME. Loaded implementation support and effective runtime fingerprint MUST match; manual Graphic/Video attestation MUST NOT be represented as verified automatic rendering. Explicit administrator verification of a deterministic Text renderer SHALL render an owned current saved Master with current context and exact live refs/rights, record only server-derived render input/output evidence hashes, and leave Master/Candidate unchanged. Read-only inventory SHALL NOT render or probe.

#### Scenario: Renderer scope changes
- **WHEN** the renderer implementation, runtime fingerprint, schema, channel, form or output MIME differs from recorded verification
- **THEN** the previous evidence remains readable but cannot verify the new render action

#### Scenario: Manual final media is not an automatic renderer
- **WHEN** an operator confirms an uploaded Graphic or Video final asset
- **THEN** its manual attestation remains valid under existing content gates but cannot authorize or verify an automatic renderer

#### Scenario: Renderer verification scopes coexist
- **WHEN** the same loaded renderer version is verified for two different supported channel/form scopes
- **THEN** both unchanged scopes remain independently verified until their own expiry, revocation or implementation/profile drift

#### Scenario: Renderer execution or evidence changes
- **WHEN** the actual loaded renderer/adapter callable changes, or referenced evidence or material is revoked before the probe transaction completes
- **THEN** previous capability evidence cannot authorize the changed implementation and the affected probe records no successful verification

#### Scenario: Real media stage scope is explicitly verified
- **WHEN** an administrator confirms the exact input/output hashes of their unexpired real-render stage with current source/context/live rights/runtime/profile
- **THEN** the service appends exact media renderer scope evidence without invoking another render or writing Material/Master; actor mismatch, stale source or tampered bytes creates no successful verification

#### Scenario: Editor executes a verified media renderer
- **WHEN** an authorized editor explicitly requests the exact schema/channel/form/output MIME backed by a current media renderer scope
- **THEN** execution and explicit output acceptance both recheck version/runtime/profile/expiry/revocation and current source gates; an unavailable scope fails without administrator-preview fallback or automatic retry

### Requirement: Capability records and results are safe projections
The system MUST NOT persist or return secrets, cookies, tokens, credential-bearing URLs, signed media URLs, headers, raw provider responses, local credential paths or unredacted exception text in registration, verification, API result, AuditLog, ProjectEvent or delivery metadata. The same prohibition applies to existing `MaterialRevision.prompt_text`, `source_url`, `source_metadata_json`, `metadata_json` and `ConnectorEndpoint.last_pull_error` when they receive external Provider/Connector results: persist only allowlisted safe origin/provenance and bounded reason codes or hashes, never raw prompt/request, signed fetch URL, remote body or exception string. Provider output MUST be treated as untrusted data rather than instructions.

#### Scenario: Nested provider error contains token
- **WHEN** a provider returns a nested error with a token, signed URL or request header
- **THEN** every stored and returned diagnostic contains only allowlisted safe fields and a non-sensitive reason code

#### Scenario: Existing media and connector fields receive sensitive values
- **WHEN** an accepted media result contains a signed fetch URL or credential-bearing prompt, or a Connector pull fails with a secret in its exception
- **THEN** MaterialRevision stores only safe origin and request/input hashes, ConnectorEndpoint stores only a bounded reason code, and no raw sensitive value appears in their fields or API projections

#### Scenario: Provider prompt injection
- **WHEN** a search or Connector response contains operational instructions
- **THEN** the payload is processed only as source data under the typed mapping and cannot change authorization, capability status or system instructions

### Requirement: Connector capability mapping is explicit
A generic Connector or ConnectorEndpoint SHALL become a Data Source executor only through an authorized mapping to one typed Data Source Plugin and exact endpoint/version. Mapping MUST NOT enable unrelated plugin keys. Execution SHALL retain existing Connector authorization, bounded fetch and SourceDocument/Fact behavior and create a DataSnapshot with immutable source/version/checksum/lineage for a Workflow Data Node.

For the existing mutable ConnectorEndpoint, exact endpoint/version means endpoint ID plus the effective configuration and credential-version fingerprint. A changed endpoint configuration or credential version MUST invalidate verification before execution; absent verifiable credential-version identity MUST NOT be treated as a verified mapping. No secret value is stored or exposed as the fingerprint.

The registration SHALL explicitly store its typed `data_source_plugin_key` and `endpoint_id` while its own key names a selectable connection profile. A Data Node SHALL select the exact registration ID and version through `source_ref`; deriving a plugin mapping from key prefixes or treating the endpoint ID alone as a source reference is forbidden. Multiple endpoint profiles MAY use the same typed plugin without becoming interchangeable.

The first generic REST `api` executor SHALL accept HTTPS GET endpoints only. Existing POST Connector pulls remain legacy-compatible but SHALL NOT be promoted to a typed read-only Data Source capability without a separate read-only contract. A probe SHALL perform an actual bounded mapped readback and append a scoped verification only when at least one mapped Fact exists; a failed or empty readback SHALL invalidate the prior scope verification.
After a verified manual pull or Data Node pull fails, the mapped capability SHALL remain unavailable until a new successful administrator probe; a stale prior verification alone SHALL NOT re-enable execution.

#### Scenario: Generic Connector configured
- **WHEN** an API Connector exists with no typed Data Source mapping
- **THEN** `api`, `notion`, `sql` and other disconnected plugin keys remain unavailable

#### Scenario: Mapped node refresh
- **WHEN** an authorized mapped Data Node refreshes and normalized output changes
- **THEN** a new snapshot records exact ConnectorEndpoint/source identity and existing dependent outputs become stale

#### Scenario: POST endpoint is not a read-only Data Source
- **WHEN** an administrator tries to register a generic POST endpoint as the first typed `api` Data Source
- **THEN** registration is unavailable and no verification is created

#### Scenario: Failed pull
- **WHEN** a mapped endpoint times out, exceeds limits or fails authorization
- **THEN** no successful snapshot or new Fact Boundary is fabricated

#### Scenario: Compressed or indefinitely trickling external response
- **WHEN** a typed Connector or Commons response uses non-identity compression, or a typed Connector exceeds its cumulative read deadline
- **THEN** the bounded reader refuses compressed content before iteration or aborts the overrun, with no successful snapshot/media; typed requests force identity negotiation and old direct Connector reads retain their legacy boundary

### Requirement: Search output is not a usable asset
Search providers SHALL return bounded candidate metadata only. Explicit import MUST validate source, downloaded bytes, hash, MIME and rights/license before creating an immutable MaterialRevision or attaching it to a Project.

The source's stable public citation URL and the provider's temporary fetch/preview URL are distinct. Only a positively validated credential-free public citation URL MAY be stored in `MaterialRevision.source_url`; when its safety is ambiguous, store a bounded source identifier and one-way URL/input hash instead. A signed, tokenized or expiring fetch/preview URL MUST NOT enter MaterialRevision metadata, AuditLog, ProjectEvent or API projections.

#### Scenario: Public citation and signed media fetch are distinct
- **WHEN** one accepted search result has a safe stable public citation URL and a signed temporary URL used to fetch its bytes
- **THEN** the exact accepted MaterialRevision may retain the validated citation and safe source identifier, while the temporary URL appears in no stored or returned metadata

#### Scenario: No provably safe citation URL
- **WHEN** a provider supplies only an ambiguous or expiring URL with valid licensed bytes
- **THEN** acceptance may retain a bounded source identifier and one-way URL/input hash but MUST NOT persist that raw URL or present it as a public citation

#### Scenario: Preview URL selected without rights
- **WHEN** a user selects a search preview whose license or public-use status is unknown
- **THEN** it remains a candidate and cannot be used as a public-ready Master/Variant asset

#### Scenario: Accepted search result
- **WHEN** validated bytes and a permitted rights decision are explicitly accepted
- **THEN** one exact MaterialRevision is stored with source/provenance and any Project reuse references that revision rather than copying bytes

### Requirement: Generated media and renderer output require exact acceptance
Image, video, TTS and renderer providers SHALL return bounded untrusted results. Only explicitly accepted, byte-verified output with exact provider/version, input/request hash, MIME, license and rights status SHALL become MaterialRevision. A Master or Variant SHALL change only through its own explicit revision save. No provider success flag, remote URL or preview alone SHALL count as generated media.

Source model-use authorization and optional Project active/ownership authorization SHALL be serialized through controlled Provider dispatch/result, not merely checked after sending source bytes. Source and parent Material locks SHALL use deterministic ordering; database authorization locks SHALL be released before publishing a temporary cache stage. Explicit acceptance retains its separate live rights checks.

#### Scenario: Source revoked before controlled dispatch
- **WHEN** a source revocation wins the authorization lock before a derived media request dispatches
- **THEN** no source bytes are sent to the Provider and no preview or derived revision is created; acceptance-time rejection alone is insufficient

#### Scenario: Explicitly configured one-shot image adapter
- **WHEN** an authorized user explicitly requests generation with the existing openai image settings and exact loaded adapter
- **THEN** one bounded HTTPS request uses the exact configured model/size, with no redirect/retry/fallback; only one base64 PNG can enter preview, source-image edits and unsafe/unsupported configuration fail before a call, config/credential drift invalidates acceptance, and neither settings save nor preview creates verification or durable media

#### Scenario: Provider reports success without bytes
- **WHEN** a provider returns a success status but media cannot be fetched, decoded, hashed or licensed
- **THEN** no MaterialRevision, project attachment, Master update or render attestation is created

#### Scenario: Different render input
- **WHEN** the Master payload/context/asset-set hash differs from the renderer's recorded input hash
- **THEN** the result cannot attest the current Master or make its Candidate freeze-ready

#### Scenario: Staged renderer result becomes stale
- **WHEN** the source Master head/context, selected canvas, profile or exact loaded renderer runtime changes before explicit acceptance
- **THEN** acceptance fails without writing a MaterialRevision or project reference; safe historical preview metadata does not authorize a new Master or render attestation

#### Scenario: Renderer result is explicitly accepted
- **WHEN** one installed exact media renderer returns decodable bytes for the server-derived input hash and selected canvas and the user explicitly confirms license/rights
- **THEN** only the exact library revision and project reference are saved with safe input/runtime/base provenance; Master save and final render binding remain separate explicit operations

#### Scenario: Derived renderer output cannot escalate source rights
- **WHEN** a renderer consumes a source lacking model/commercial-use rights or requiring CC BY attribution
- **THEN** the explicit output decision cannot grant unsupported rights or remove the source license/complete attribution; acceptance rechecks the live restrictions before commit

#### Scenario: Renderer source budget is exceeded
- **WHEN** the unique referenced source files exceed the bounded 30 MB input budget or escape the media storage root
- **THEN** the probe rejects them before reading their bytes or calling the renderer; repeated layers share one verified source byte set

#### Scenario: Explicit local Graphic rendering runtime
- **WHEN** an administrator probes an installed local Graphic renderer with explicitly configured browser, execution dependencies and font bytes
- **THEN** it renders only the selected canonical canvas and verified inline source bytes with network access blocked, fingerprints its actual execution inputs, and returns a real PNG; absent configuration, unsupported font coverage or unsupported document semantics fail rather than silently substituting a font, placeholder or external resource

#### Scenario: Graphic Studio explicitly accepts and binds a render
- **WHEN** an administrator renders a current saved Graphic canvas and explicitly accepts its bytes and rights in Production
- **THEN** accepting saves only the library revision and Project reference, a separate explicit action binds the exact server-visible accepted revision to local canvas state, and only explicit Master save creates a new immutable revision; dirty, historical, archived or unauthorized state cannot execute the preview/accept/bind controls, and no action silently verifies a capability

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

The existing WeWrite publisher's legacy render input MUST NOT be applied directly to a v5 manifest. A v5 WeChat article requires a deterministic pre-attempt projection from its frozen approved title/body/digest/cover bytes into the publisher input; missing or incompatible frozen content MUST fail before a remote attempt, without v3/v4 fallback or post-approval rewriting.

#### Scenario: Publisher wants shorter title
- **WHEN** frozen approved content exceeds a remote platform limit
- **THEN** delivery fails with an actionable validation reason and no modified remote payload is sent

#### Scenario: V5 article presented to legacy WeWrite input
- **WHEN** a verified WeChat account authorizes an approved v5 article for auto-draft
- **THEN** the publisher receives only a validated deterministic projection of the frozen article and exact cover bytes, or no attempt is prepared if that projection cannot be formed

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
