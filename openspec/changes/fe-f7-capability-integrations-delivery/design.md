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

### 4. External outputs are untrusted until explicitly accepted

Search returns bounded metadata only; preview URLs do not confer rights. Generation/TTS/renderer results are staged as untrusted output, with bounded fetch, SSRF/redirect protection, content-length and MIME sniffing, file hash and license/rights decision. Only accepted bytes create an immutable MaterialRevision with exact provider/version/input/prompt-or-request hash, source ref and rights status. Project attachment uses existing exact MaterialRevision reference; Master/Variant changes require a separate explicit revision save. ASR cues/transcripts are bounded suggestions, not Master writes. Disconnected provider attempts produce unavailable/failure/unknown receipts, never generated media. Alternative—trust a provider's URL/MIME/success flag—would allow phantom or unsafe assets.

### 5. Redact at every response and persistence edge

Provider request/response wrappers map only allowlisted result fields into stored metadata or user errors. Redaction covers nested response bodies, exception strings, logs, AuditLog, DeliveryAttempt, ProjectEvent, API projections and verification evidence. Raw provider IDs may be stored only in a purpose-specific field when safe and authorized; tokens, signed URLs, credential-bearing links, headers, cookies and local paths never cross the safe boundary. Negative probes intentionally supply secret-looking nested payloads. Settings masking alone is insufficient because `WechatWewritePublisher` currently forwards subprocess output into a failure string.

### 6. Verification is an exact remote-action predicate

For remote Publisher actions the predicate is platform × stable ContentAccount/legacy account binding × content form × action × publisher key/version × config fingerprint × validity interval. The configured account must still be active and authorized. A real verification requires explicit operator confirmation and platform read-back or documented human evidence; it cannot be inferred from registration, a simulated response, local package, provider probe or WeWrite's unverified success metadata. All remote execution, including the legacy `allow_unverified_auto_draft` path, checks this predicate. Historical targets/attempts remain readable, but the opt-in flag cannot open a new remote effect. Local `copy_package`/`manual_handoff` remain available only when their exact content is packageable and authorized. Alternative—boolean `verified()` per plugin—cannot distinguish one account/form/action from another.

### 7. Preserve delivery state machine and approved bytes

Remote Publisher consumes the frozen approved Candidate/package and DeliveryTarget authorization; no rewriting, truncation, asset generation or silent channel adaptation occurs after approval. New v5 path uses its approved Variant content; v1–v4 historical reads remain schema-dispatched. Side-effect attempts persist a prepared idempotency key before the remote call; uncertain result remains unknown/reconciliation-needed and cannot auto-retry. Verification expiry/revocation prevents new execution but does not rewrite historical attempts. Alternative—retry on timeout or fallback to another publisher—risks duplicate publication.

### 8. Settings is a safe projection

Show discovered/configured/executable/verified/unavailable with typed reason and exact safe scope/last verification. Read-only inventory does no probing or network calls. Explicit probe/verify endpoints require the existing role gate and a separate confirmation for side effects; return bounded safe metadata. Keep the six existing Settings sections and Channel/Data Source registries as their truth sources.

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
