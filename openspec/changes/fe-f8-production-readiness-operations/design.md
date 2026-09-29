## Context

F8 follows F7 acceptance and closes production operations, not missing product features. Today `deps.get_current_user()` accepts `X-Studio-User`, defaults to a local admin email and creates a User on demand. `main.lifespan()` calls `init_db()` and mutates template/settings bootstrap. `health.check_health()` catches DB exceptions into a response body; the health route does not set 503. `/metrics` keys use raw request paths. `MaterialRevision.file_path` is a local relative path under `MEDIA_ROOT`, and several legacy/Project/Delivery services read it directly. `storage_service.py` currently uses MinIO for exports, not for all immutable media. These are concrete seams to close, not proof of production readiness.

## Goals / Non-Goals

**Goals:** fail-closed production identity/startup; safe secrets and observability; stable exact-hash storage reads; truthful readiness; rehearsed recovery; versioned quality acceptance; traceable Opportunity→Learning integration and honest real-platform coverage.

**Non-Goals:** organization/tenant/invite/SSO administration, new business truth tables, silently migrating historic media on startup, executing production migrations/deployment without separate authorization, or marking unavailable external accounts verified.

## Decisions

### 1. Explicit environment and auth mode

Production mode requires an approved signed-token identity adapter with issuer/audience/key/JWKS validation, bounded key refresh and mapping to an existing active User row. Studio role comes from that row, not a token role claim or request header; unknown subjects are denied, not auto-created. Development/test mode may retain the existing Header/default-user behavior. Production startup rejects Header mode, missing auth configuration and a test/mock auth fallback before routes are served. Alternative—placing a reverse proxy in front while continuing to trust `X-Studio-User`—leaves a spoofable bypass inside the API.

### 2. Startup validates; an operator migrates

In production, `lifespan` must not call schema-creating `init_db()` or mutable bootstrap that silently changes approved configuration. Require an explicit migration-head check and documented operator action, with read-only startup validation and safe failure. Dev/test can retain current bootstrap. Alternative—auto-upgrade on service start—can race replicas and make rollback ambiguous.

### 3. Reuse User/Role and define persisted-secret policy

No Organization/Tenant/SSO admin model is introduced. Production secrets resolve from external secret references or approved deployment configuration. Existing SystemSetting rows may contain plaintext overrides; production enablement requires an inventory and deliberate disable/migrate procedure, not just masked API output. Logs, health, metrics, exceptions, AuditLog, provider and worker metadata use allowlists. Alternative—relying on Settings masking—does not protect the other surfaces.

### 4. StorageProvider is infrastructure under existing revisions

Create local and object-backed implementations of bounded `put/read/exists/delete-if-unreferenced` over immutable content-addressed keys; preserve `MaterialRevision.id/content_hash` and historical business refs. All byte consumers, including legacy DraftMedia, workflow outputs, project assets, Review/Delivery packages and retention, must go through the selected adapter or an explicitly justified compatibility bridge. Existing MinIO export helper is not proof that material reads are object-backed. Reads used for Candidate/package rehash bytes and fail closed on missing/corrupt objects. Production storage cutover needs a complete referenced-byte copy/verify inventory and a recoverable switch; partial mixed roots cannot be declared ready. Alternative—switch only `materials.read_bytes_checked()`—would leave direct `MEDIA_ROOT` callers broken or bypassing verification.

### 5. Reuse and harden existing ops endpoints

Keep `/api/v1/health` and `/metrics` compatibility while separating shallow liveness from readiness. Readiness checks DB and schema head, selected storage, configured queue/worker requirement and critical auth/secret config; optional disconnected providers do not fail core readiness. Failed required dependencies return a non-success HTTP status with a safe reason code, not `str(exc)`. Metrics use route templates or a bounded label set, not raw URLs/IDs; access to operational detail is controlled. Existing `x-trace-id` is propagated into worker/Workflow/provider/delivery history as safe correlation, without creating a second business state source. Alternative—add a second uncoordinated health endpoint—would leave old unhealthy-200 consumers and unbounded metrics unchanged.

### 6. External effects retain F7 gates

F8 threat-models outbound hosts, credential isolation, request/response size/time bounds, SSRF, side-effect confirmation, idempotency and Unknown reconciliation across every capability. Read-only UI/Settings inventory triggers no network call. F7's exact Publisher verification remains authoritative; production readiness cannot replace missing real-account verification. Alternative—mark all installed plugins active when infrastructure is healthy—would fabricate capability coverage.

### 7. Recovery rehearses a restored copy, never live rollback

Back up PostgreSQL and referenced media together; restore into an isolated environment, verify migration head and a sample of exact MaterialRevision hashes, query historic Identity/Fact Boundary/Candidate/Approval/Delivery lineage and rehearse capability disable. Downgrade only where its preflight proves no incompatible history; destructive rollback is not an automatic recovery path. No production backup, restore, migration or deployment is executed by this OpenSpec proposal.

### 8. Golden and full-chain acceptance are distinct gates

Versioned Identity Golden fixtures cover Brand/Persona voice, boundaries, differentiation and frozen snapshot continuity. Content Golden fixtures cover facts, Brief, three modalities and channel adaptation. Deterministic checks run automatically; generative quality evidence records provider/model/version, input/output hashes and human reviewer when needed. Full integration exercises Opportunity→Project→Identity→Brief/Fact Boundary→Matrix→all three Masters→Variant→Candidate→Approval→Authorization→local/verified Delivery→Receipt→Performance→Learning; each step's exact lineage is queryable. Real Platform acceptance is scoped to available, separately authorized account/action/form combinations; absent credentials are reported `unverified`, not simulated.

## Risks / Trade-offs

- Production startup behavior becomes stricter → fail early with a safe configuration checklist, preserve dev/test mode, and test negative auth/startup paths.
- Existing direct media paths are numerous → inventory each reader/writer and run mixed old/new revision regressions before switching any production storage mode.
- Historical SystemSetting values may contain plaintext secrets → block production enablement until inventory/remediation is explicitly performed; never print those values in reports.
- Queue/worker availability depends on deployment topology → readiness checks only required configured components and uses bounded probes; optional providers remain independent.
- Golden model output is non-deterministic → version fixtures and record review/provenance; do not score it as a deterministic unit pass.
- No real external account may be available → implementation can be complete locally while per-platform verification remains explicitly incomplete.

## Migration Plan

No new durable business object is planned. Implementation first runs dev/test baseline and security inventory, then introduces auth/storage/observability adapters behind explicit configuration. Validate a production-like isolated environment with PostgreSQL and copied media, rehearsed backup/restore, old/new byte reads and full-chain acceptance before preparing a runbook. A real environment switch requires a separate deployment authorization, an operator-controlled migration/secret cutover and a rollback plan preserving both DB and bytes. If an additive schema change proves necessary, revise the OpenSpec and validate isolated up/down/up before applying it; never perform a destructive migration by default.

## Open Questions

- Which identity issuer and secret provider are approved for an actual deployment? The secure adapter contract can be implemented locally, but no production activation is claimed until configured and verified.
- Which external accounts are available for Real Platform acceptance? Unavailable combinations remain `unverified` in the final capability matrix.

## Source-package preservation audit

The source ten requirements map to: production auth; secrets; storage; correlated operations; health/readiness; untrusted external capabilities; recovery; Identity/Content Golden; full ChannelVariant integration; and real-platform Publisher evidence. F8 adds current-code-specific controls for startup writes, unhealthy-200/raw errors, metric cardinality and direct media callers; none of the source requirements are treated as already implemented by having a spec.
