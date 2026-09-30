## Context

F7 follows F6E acceptance. Current `content_harness.registry` resolves `(kind,key,version)` exactly, but its kinds are limited; `data_source_plugins` exposes a typed selector with only `studio.source` executable; `ConnectorEndpoint` already fetches and maps JSON into SourceDocument/Fact. `MaterialRevision` already stores exact bytes/hash, provider fields and rights. `DeliveryTarget` freezes account/action/publisher metadata, and `DeliveryAttempt` keeps prepared → remote call → result/unknown. Product Settings already has allowlisted read projections. These are the truth sources to extend, not replace.

Current WeWrite reports `verified() == False`. Legacy `delivery.allow_unverified_auto_draft` can nevertheless bypass the execution check. F7 closes that bypass for future remote effects while keeping historical targets, attempts and receipts readable. F6C/F6D deferred real provider output acceptance and response redaction here; F6E defines the channel adaptation/Candidate v5 boundary.

## Goals / Non-Goals

**Goals:** exact versioned resolution; safe durable verification; explicitly mapped Connector execution; bounded, accepted provider bytes with live rights; truthful inventory; scoped remote delivery with immutable approved payload and unknown reconciliation.

**Non-Goals:** a second Workflow Engine, generic Asset truth, provider-written Master/Variant, publisher-time adaptation, credential storage in verification rows, invented remote platform support, production deployment, or claiming untested accounts verified.

## Decisions

### 1. Extend registry, do not replace resolvers

Add the North Star kinds to `RegistryKinds` while preserving legacy `node/rule/renderer/publisher/asset_provider/material_search/skill_runtime` keys. A registration's `kind + key + version` and executable implementation must match exactly. Persisted registration does not dynamically import arbitrary code. Runtime availability is derived from registered implementation, safe configuration identity, scoped verification where required, enabled state and policy. Alternative—treat a DB row as executable—would allow false availability and code loading from untrusted metadata.

### 2. Two additive tables, no duplicated business history

`CapabilityRegistration` holds safe descriptor metadata, key/kind/version uniqueness, status, config fingerprint and an optional explicit ConnectorEndpoint link for a data-connector mapping. `CapabilityVerification` is append-only evidence for registration id, typed scope, result, verified-at/by, expiry and invalidation, with a bounded safe evidence projection. Verification is valid only when exact registration version/fingerprint, endpoint identity, actor/account authorization and action scope still match. No secret, cookie, token, credential path, raw URL/query, provider response or prompt body enters either table. Existing Connector config and DeliveryTarget/Attempt remain their respective truth sources. Alternative—new connector or delivery tables—would split authority and history.

Invalidation is a newer verification event or a computed expiry/fingerprint mismatch, not silent deletion or rewriting of older evidence. If a second durable mapping or verification-history object proves necessary, stop for a spec revision rather than inventing one during apply.

### 3. Keep Data Source Plugin the execution gate

A ConnectorEndpoint becomes a particular typed Data Source Plugin executor only after an explicit registration mapping and validation of endpoint, connector status, credential availability and caller/project authority. Workflow Data Node still calls the typed plugin boundary, which creates a bounded immutable DataSnapshot with source/version/checksum and existing stale propagation. Manual Connector pulls continue to write SourceDocument/Fact through their existing path; F7 must not duplicate these objects or silently turn a pull into a Fact Boundary. Generic Connector configuration alone cannot enable `notion`, `api`, `sql` or other plugin keys. Alternative—route any configured Connector through a generic Data Node—would bypass typed availability and provenance.

The first generic REST `api` capability accepts HTTPS GET only. Legacy Connector POST pulls remain compatible, but they are not promoted to typed Data Source execution without a separately specified proof of read-only behavior; HTTP method alone cannot establish this for POST. A successful probe is an actual bounded readback with mapped facts and exact configuration fingerprint, not a registration row or mock result.
The registration version is the selectable connection-profile version, not a claim that the built-in generic REST executor's code has changed. Configuration rotation creates a new registration version and must be re-probed; the prior pinned Data Node source reference does not silently follow it.
For F7 mapped pulls, source deduplication and snapshot currentness hash the canonical mapped Fact fields, including value/unit/as-of, not only the human-readable statement. Legacy direct Connector pulls preserve their prior deduplication semantics. DataSnapshot projects bounded mapped Facts and exact source hash, never arbitrary unmapped response fields.
The F7 typed path alone uses a streaming 1 MB decoded-response cap, a 10-second per-request timeout, no more than 20 pages or 500 mapped rows per page (10,000 total), and bounded request configuration. It validates every redirect target before reading that hop. The legacy Connector path keeps its prior fetch behavior until separately migrated.

`ConnectorEndpoint` has no revision number today. For F7, its exact version identity is the endpoint ID plus a server-derived fingerprint of the effective Connector/Endpoint configuration and credential version, not an invented endpoint revision column. Credential material never enters the fingerprint stored in the database or API; the configured credential-version identity must change on rotation, and an absent/unverifiable version makes the mapped capability unverified. An endpoint edit or credential rotation invalidates prior verification before a new Data Node execution.

Because several API sources may share the same typed plugin, `CapabilityRegistration.key` names a specific configured profile, while a nullable `data_source_plugin_key` on that same row explicitly names the typed plugin. A `data_connector` row requires both `data_source_plugin_key` and `endpoint_id`; other kinds leave them null. Data Node `source_ref` pins `capability:<registration_id>@<registration_version>`; a raw endpoint ID, generic Connector, or a matching string prefix is not a mapping. Only a known loaded built-in executor version may bind this profile, and scope verification remains separate from registration.

### 4. External outputs are untrusted until explicitly accepted

The first staging implementation is a bounded, actor-scoped, 15-minute in-process preview cache, not another durable business object. It retains only verified bounded bytes, source revision hashes and safe canonical provenance; raw prompts/responses/fetch URLs are not copied into a durable result entity. A worker restart/expiry requires an explicit new preview, never implicit provider retry. Explicit acceptance rechecks the exact loaded runtime fingerprint, source live model-use rights, bytes/hash/MIME and an operator-confirmed license/rights decision before atomically writing MaterialRevision and an optional project reference. Accepted revision IDs may be replayed only for the identical acceptance decision. Production deployments must expose staging availability honestly; cross-worker durable staging, if required, is a separate storage contract rather than a new business table.

Search returns bounded metadata only; preview URLs do not confer rights. Generation/TTS/renderer results are staged as untrusted output, with bounded fetch, SSRF/redirect protection, content-length and MIME sniffing, file hash and license/rights decision. Only accepted bytes create an immutable MaterialRevision with exact provider/version/input/prompt-or-request hash, source ref and rights status. Distinguish a stable, credential-free public citation URL from a temporary provider fetch/preview URL: only a positively validated safe citation may enter `MaterialRevision.source_url`; otherwise store a bounded provider/source identifier and one-way URL/input hash, not the fetch URL. Do not copy temporary URLs into metadata, audit, events or API results. Project attachment uses existing exact MaterialRevision reference; Master/Variant changes require a separate explicit revision save. ASR cues/transcripts are bounded suggestions, not Master writes. Disconnected provider attempts produce unavailable/failure/unknown receipts, never generated media. Alternative—trust a provider's URL/MIME/success flag—would allow phantom or unsafe assets.

### 5. Redact at every response and persistence edge

Provider request/response wrappers map only allowlisted result fields into stored metadata or user errors. Redaction covers nested response bodies, exception strings, logs, AuditLog, DeliveryAttempt, ProjectEvent, API projections and verification evidence. Existing persistence fields are part of the same boundary: accepted external `MaterialRevision.prompt_text`, `source_url`, `source_metadata_json` and `metadata_json` MUST NOT retain raw provider prompts/requests, credential-bearing or signed URLs, secret headers, cookies or unredacted response fragments; use safe source identity and request/input hashes instead. A citation URL is persistable only after positive validation that it is a stable public reference, not a media fetch URL or tokenized/expiring link; ambiguous URLs fail closed to an opaque identifier/hash. `ConnectorEndpoint.last_pull_error` MUST contain only a bounded safe reason, not the exception string or remote body. Raw provider IDs may be stored only in a purpose-specific field when safe and authorized; tokens, signed URLs, credential-bearing links, headers, cookies and local paths never cross the safe boundary. Negative probes intentionally supply secret-looking nested payloads through both successful and failed Connector/Provider paths. Settings masking alone is insufficient because `WechatWewritePublisher` currently forwards subprocess output into a failure string.

### 6. Verification is an exact remote-action predicate

For remote Publisher actions the predicate is platform × stable ContentAccount/legacy account binding × content form × action × publisher key/version × config fingerprint × validity interval. The configured account must still be active and authorized. A real verification requires explicit operator confirmation and platform read-back or documented human evidence; it cannot be inferred from registration, a simulated response, local package, provider probe or WeWrite's unverified success metadata. All remote execution, including the legacy `allow_unverified_auto_draft` path, checks this predicate. Historical targets/attempts remain readable, but the opt-in flag cannot open a new remote effect. Local `copy_package`/`manual_handoff` remain available only when their exact content is packageable and authorized. Alternative—boolean `verified()` per plugin—cannot distinguish one account/form/action from another.

### 7. Preserve delivery state machine and approved bytes

Remote Publisher consumes the frozen approved Candidate/package and DeliveryTarget authorization; no rewriting, truncation, asset generation or silent channel adaptation occurs after approval. New v5 path uses its approved Variant content; v1–v4 historical reads remain schema-dispatched. Side-effect attempts persist a prepared idempotency key before the remote call; uncertain result remains unknown/reconciliation-needed and cannot auto-retry. Verification expiry/revocation prevents new execution but does not rewrite historical attempts. Alternative—retry on timeout or fallback to another publisher—risks duplicate publication.

The current WeWrite adapter reads legacy `render.payload` and cannot consume a v5 manifest directly. A v5 WeChat article may enter that remote adapter only through a deterministic, byte-exact projection of its frozen approved article, title, digest and cover into the publisher's input contract; the projection is validated before an attempt is prepared. The frozen v5 article schema has no separate digest field, so this first scope uses the exact frozen title as digest; it MUST NOT invent or summarize one after approval. Missing or incompatible fields fail closed, with no v4/v3 fallback and no publisher-side formatting or media generation. Actual WeWrite/account verification still requires real scoped evidence; a local package or mock CLI result never suffices.

Inspection of the installed WeWrite CLI found global account configuration and a Markdown converter that removes/normalizes body content and appends a declaration. It therefore has no proven account-bound immutable upload contract. Its runtime remains unavailable for new remote effects, including verification API registration, regardless of operator-supplied version labels. A pure v5 projection and synthetic provider tests do not enable this CLI. An account-bound no-rewrite adapter must be implemented and reviewed before this scope becomes executable; local/manual packages remain usable.

### 8. Settings is a safe projection

Show discovered/configured/executable/verified/unavailable with typed reason and exact safe scope/last verification. Read-only inventory does no probing or network calls. Explicit probe/verify endpoints require the existing role gate and a separate confirmation for side effects; return bounded safe metadata. Keep the six existing Settings sections and Channel/Data Source registries as their truth sources.

The initial operator surface reuses Data Sources and Channels. An administrator explicitly saves a typed API connection version and probes its bounded GET; Production selects the exact resulting profile reference. Publisher human readback records only a SHA-256 evidence reference, exact owned ContentAccount/channel/form/action/publisher version and server-derived runtime fingerprint, with a maximum 24-hour validity. Evidence text is hashed locally, never uploaded. Recording/revoking evidence itself performs no remote publication. Synthetic operator/browser fixtures prove persistence and gates only, never real-account acceptance.

## Risks / Trade-offs

- Existing legacy opt-in automatic draft becomes unavailable without scoped real verification → show a specific migration reason, preserve history and manual package path.
- Config or credential rotation invalidates prior verification → compare fingerprints and account/action scope at execution, not only on Settings read.
- Provider downloads/response errors may contain secrets or unsafe URLs → bounded fetch plus allowlisted serialization and negative leakage checks.
- Verification may require real account credentials that are not available in local development → leave scope explicitly unverified; never mark F7 real-platform acceptance complete from mocks.
- A provider may report success with no usable bytes or license → keep result staged/unavailable; no MaterialRevision or project attachment.

## Migration Plan

After F6E gates, add only the two planned tables in an additive, reversible migration; validate SQLite and PostgreSQL-compatible DDL in isolated databases, including upgrade/down/upgrade and verification-history downgrade preflight. Do not backfill `verified=true` from existing registry/Connector/WeWrite configuration. Legacy rows remain readable; remote execution becomes fail-closed until a separately authorized real verification is recorded. Production migration and release remain separately authorized.

## Open Questions

- Which real providers/accounts will be available for isolated F7 verification? Absence changes only verified coverage, never permits fake success.
- Does a selected Provider's license permit public/model/commercial reuse? Unknown remains unknown and blocks public-ready use.

## Source-package preservation audit

The original ten requirements map to the standard clauses as follows: replaceable registration → descriptor requirement; durable verification and unverified availability → verification requirement; Connector mapping → Connector requirement; external media → search/generated-media requirements; ASR/transforms → suggestion requirement; Settings truth → Settings delta and safe inventory; approved Publisher → publisher-content requirement and FE-F4 delta; unknown outcome → unknown requirement; real platform acceptance → scoped verification and real-acceptance requirements. No source requirement is treated as implemented merely by this spec.
