## ADDED Requirements

### Requirement: A real account belongs to exactly one content persona
The system SHALL preserve one Persona to many ContentAccounts and SHALL prohibit a real platform account from being bound to multiple Personas through either shared references or duplicate local account records. Stable platform identity SHALL be distinct from names, content profiles and operator authorization.

#### Scenario: Duplicate real account
- **WHEN** another account attempts to bind the same platform identity
- **THEN** the binding fails atomically with a safe conflict and does not reveal the existing owner; archiving the original account does not release its historical identity

#### Scenario: Two accounts under one persona
- **WHEN** an authorized operator binds two distinct real accounts to the same active Persona
- **THEN** both remain independently selectable with their own connection, verification and history

### Requirement: Credentials and verification are account scoped
The system MUST resolve publisher.wechat.official@1 credentials, tokens and effective runtime by exact owned ContentAccount and platform identity. It MUST NOT use a global current account, another account token or old WeWrite verification. Secrets SHALL remain outside profiles, manifests, API projections and audit records; registration alone SHALL NOT prove account ownership.

#### Scenario: Account A rotates credentials
- **WHEN** A changes credential/configuration version
- **THEN** A's old tokens and scope cannot authorize new delivery while unchanged B remains independent

#### Scenario: Unbound historical account
- **WHEN** an old account lacks a proven platform binding
- **THEN** history and local delivery remain available under existing rules but remote creation is unavailable with no inferred identity

### Requirement: Official channel representation is approved before dispatch
The system SHALL freeze a versioned deterministic official article render in Candidate before Approval, including exact text, safe HTML template, renderer/hash and exact asset slots. Publisher MUST NOT convert Markdown, rewrite, truncate, add declarations or generate media after Approval. Only account-specific remote identifiers for exact frozen resource slots MAY be substituted using validated mappings.

#### Scenario: Historical candidate lacks official render
- **WHEN** a v5 or older candidate lacks the approved official render contract
- **THEN** new official remote delivery is rejected without mutation or fallback and requires a newly frozen approved candidate; legacy reads/local packages remain unchanged

#### Scenario: Asset needs transformation
- **WHEN** the platform cannot accept the approved exact asset bytes
- **THEN** delivery stops without resizing/transcoding and the user must prepare and approve a new revision

#### Scenario: Inline image placement is exact
- **WHEN** a new article contains explicit image blocks
- **THEN** each block has one exact inline material slot bound by stable block ID, order and revision/hash, frozen before Approval; missing, duplicated or orphan mappings are rejected, old text-only canonical hashes remain unchanged, and dispatch may replace only its frozen resource placeholder

### Requirement: Draft creation preserves existing delivery semantics
The system SHALL use existing DeliveryTarget, DeliveryAttempt and DeliveryReceipt for official draft creation. An authorized prepared Attempt SHALL precede any external action. Scoped verification/current candidate/live rights SHALL be rechecked; ambiguous side effects SHALL remain unknown and MUST NOT auto-retry or switch publishers.

#### Scenario: Create times out
- **WHEN** a draft-create request has an ambiguous result
- **THEN** the original Attempt remains reconciliation-needed and no new create is issued automatically

#### Scenario: Partial upload succeeds
- **WHEN** one asset uploads but a later step fails
- **THEN** safe step evidence remains in the existing Attempt, no successful draft is fabricated, and local rollback does not claim the remote upload was undone

#### Scenario: Failed step retains bounded diagnostics
- **WHEN** a claimed official step raises a transport error
- **THEN** the existing Attempt retains an allowlisted fixed transport code and a strictly boolean dispatch hint; optional phase/reason use fixed allowlists, HTTP status is a strict integer from 100 through 599, and response type is only json/text/html/missing/other; persistence filters these fields again, excluding raw headers, exceptions, URLs, tokens, provider messages and bodies; invalid optional values are omitted, unrecognized codes become a fixed unknown code, historical Attempts are not backfilled, and the evidence neither relaxes response validation nor downgrades unknown state or permits automatic retry

#### Scenario: Authorization changes after preparation
- **WHEN** account archival, runtime rotation or verification revocation wins the authorization lock after Attempt preparation or after one upload
- **THEN** the next external step is refused with no dispatch; already dispatched work is not claimed canceled and its evidence remains available

#### Scenario: Concurrent execution or crashed in-flight step
- **WHEN** another request observes the same target already prepared, in flight or unknown
- **THEN** it cannot acquire a second dispatch claim or automatically reclaim and resend the ambiguous step; target state and step authorization are serialized with database locks and CAS

### Requirement: Official HTTP behavior matches the proven WeWrite wire contract

The account-bound publisher SHALL use the proven WeWrite HTTP request semantics for the supported WeChat draft flow: token GET, `media` multipart uploads using the frozen filename/MIME, UTF-8 JSON `draft/add` with the WeWrite article fields, and exact non-empty response `media_id` confirmation. It MUST keep AIContentStudio account scoping, frozen-content, claim/CAS, secret-redaction, no-public-publish and no-automatic-retry controls; it MUST NOT import WeWrite's global credential cache, CLI fallback or public-publish behavior.

#### Scenario: WeWrite-compatible cover upload

- **WHEN** an authorized attempt uploads the frozen cover
- **THEN** the request uses `material/add_material` with a `media` multipart part whose filename and MIME match the frozen asset, and only a valid response `media_id` is recorded as the cover mapping

#### Scenario: Original filename is frozen and remains exact

- **WHEN** a new official Candidate is frozen
- **THEN** renderer version 2 freezes each slot's original `MaterialRevision.metadata_json.filename` and exact MIME into the render/Candidate hash; missing or unsafe names cannot be replaced by a generated technical name, changed live names/MIME refuse remote dispatch, and historical renderer version 1 candidates remain readable but cannot receive after-approval enrichment or new official remote effects

#### Scenario: WeWrite-compatible body image upload

- **WHEN** an authorized attempt uploads a frozen inline image
- **THEN** the request uses `media/uploadimg` with the exact `media` multipart bytes and filename/MIME, and only a valid response `url` is used to substitute the corresponding frozen slot

#### Scenario: Draft success requires media_id

- **WHEN** `draft/add` returns HTTP success and JSON `errcode` zero
- **THEN** the attempt is confirmed only if the response also contains a valid non-empty `media_id`; an empty/missing/ambiguous response remains unknown and cannot trigger a second create

#### Scenario: Official text/plain contains strict JSON

- **WHEN** a supported fixed official endpoint returns HTTP 200 with `application/json` or `text/plain`, optionally with charset parameters
- **THEN** both MIME types use the same bounded strict JSON parser and operation-specific contract checks; duplicate keys, non-finite constants, non-object payloads, invalid or nonzero errcode, and missing or invalid required identifiers remain rejected; HTML, missing or other MIME, compressed responses, non-200 status and exceeded budgets/deadlines remain rejected, and compatibility never grants another dispatch or changes historical Unknown attempts

#### Scenario: UTF-8 article payload

- **WHEN** the product creates a draft
- **THEN** it sends UTF-8 JSON with `application/json; charset=utf-8`, preserves Chinese characters without ASCII escaping, includes `title`, `author`, `digest`, `content`, `show_cover_pic: 0`, and the exact frozen `thumb_media_id`, and does not rewrite the approved HTML

### Requirement: Readback is distinct from public publication
The system SHALL preserve a known remote draft identifier. A successful official `draft/add` response with an exact `media_id` MAY confirm draft creation without a second readback, matching the approved WeWrite API contract; bounded matching readback remains an explicit optional verification path. Ambiguous side effects still require reconciliation and MUST NOT auto-retry. Draft creation SHALL NOT imply published content or automatically create PublishedContentRecord. Any allowed normalization SHALL be versioned and backed by official evidence.

#### Scenario: Draft readback mismatch
- **WHEN** remote text or asset mapping differs from the approved frozen contract
- **THEN** the result remains reconciliation-needed with safe diagnostics and cannot be accepted by silently rewriting the approved content

#### Scenario: Human confirms official draft delivery
- **WHEN** a human confirms delivery of publisher.wechat.official@1 auto_draft through a Receipt or reconciliation
- **THEN** the existing Receipt records that draft delivery only and does not automatically create a PublishedContentRecord or assert a public publication time; legacy manual-publication receipt behavior remains unchanged

### Requirement: Real account actions require separate authority
The system MUST NOT perform token retrieval, upload, draft creation or account readback merely by saving settings, rendering inventory or running default tests. Real actions SHALL require explicit exact account/action authority and credentials; fixtures SHALL NOT create real verified status.

#### Scenario: Read-only settings
- **WHEN** a viewer opens account or capability inventory
- **THEN** no secret is read, token obtained or external request performed and the view distinguishes configured from verified

### Requirement: Official endpoint contracts are evidence backed
Implementation SHALL obtain current official API documentation for token, media upload, draft create and readback before enabling the new adapter. Missing evidence or unsupported account permissions MUST remain unavailable, not guessed from unofficial examples.

#### Scenario: Official documentation unavailable
- **WHEN** exact endpoint parameters, limits or permissions cannot be confirmed
- **THEN** real remote dispatch and verified/executable claims remain blocked; explicitly authorized local account binding, adapter implementation and isolated tests may proceed without guessing a production contract

#### Scenario: Local acceptance with unresolved remote limits
- **WHEN** local adapter tests pass but official body-size limits remain contradictory
- **THEN** the system retains the unresolved-contract reason, refuses general real remote requests except the explicitly authorized bounded experiment below and does not turn fixture success into account verification or full F7 acceptance

### Requirement: An explicitly authorized short-draft experiment does not enable the general contract
The system MAY execute an explicitly approved short-draft experiment for the user's designated account while the general body-limit contract remains unresolved. It MUST bind authority to exact owned account/AppID, approved Candidate ID/hash, DeliveryTarget, one Attempt, action and short-lived experiment scope. General contract readiness MUST remain false; the experiment MUST NOT use test monkeypatches, legacy CLI fallback, global enable flags or fabricated platform verification. All existing ownership, approval, live rights, TLS, secret masking, CAS and Unknown gates SHALL remain mandatory. No new durable business object or migration is authorized.

#### Scenario: Final HTML size rather than character count
- **WHEN** a short-draft experiment is prepared and its approved media placeholders are replaced
- **THEN** preparation verifies a bounded final URL-expanded UTF-8 body estimate and create verifies actual final HTML content is strictly below 2048 bytes; excess refuses dispatch without truncating or changing approved content, and any completed upload evidence is retained

#### Scenario: Unscoped or reused experimental authority
- **WHEN** another account, Candidate/hash, target, Attempt or action attempts to use the experimental authority, or its authority has expired
- **THEN** the action is refused before dispatch; an ambiguous create cannot be automatically retried under experimental authority

#### Scenario: Short-draft readback succeeds
- **WHEN** the exact experimental draft is created and matching readback is confirmed
- **THEN** only bounded experimental evidence is recorded for that exact account/content; no general verified status, public publication record or long-form contract readiness is inferred, and F7/F8 obligations remain outstanding
