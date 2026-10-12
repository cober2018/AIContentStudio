## Context

F8 closes operations for this computer's final single-machine production use: SQLite, configured local media and loopback API/Web. The initial audit identified local Header/default-user bootstrap, unhealthy-200/raw errors, dynamic metric labels and direct media consumers. Accepted work closes local health, telemetry, byte integrity and recovery gates; current identity/startup remains within the loopback boundary. Serverization is not the meaning of production or an expected upgrade.

## Goals / Non-Goals

**Goals:** easy existing startup/diagnosis; safe local credentials and observability; exact-hash local media; truthful readiness; paired SQLite/media recovery; traceable product acceptance and honest quality/publication evidence.

**Non-Goals:** adding JWT, independent Secret Provider, PostgreSQL, MinIO, containers, proxy or login merely for a production label; organization/tenant/invite/SSO; new business tables; changing APP_ENV/schema/media/credentials/identity/Worker; running migration/deployment or fabricating verification.

## Decisions

### Final deployment decision (2026-10-04)

The approved 82/82 scope is complete for single-machine production. Original 18 identity/schema, Secret Provider, object-store and new remote/downstream entries are out-of-scope extension records, preserved unchecked/unverified, not blockers. Literal `APP_ENV=production` is a separate technical server-extension mode; keep current runtime settings. Loopback limits inbound callers, not authorized outbound model/WeChat operations. Real-data preservation, paired backup/hash recovery, secret masking, traceable errors and no automatic Unknown retry remain mandatory. Daily operations use existing launchd API/Worker scripts, Web npm entry and logs; see `docs/runbooks/production-readiness.md`.

Decisions 1–2 and external-secret/object-store portions of 3–4 below are conditional extensions only, not requirements to activate for this computer's formal use. Existing extension code does not prove activation or acceptance. This round calibrates documents/specs only; no runtime changes or new acceptance calls.

### Draft authorization correction (2026-10-01, historical extension record)

The original User-column/HS256 proposal predated its required review. Its activation/acceptance entries remain unchecked here and outside the final single-machine scope, regardless of later code commits. This terminology correction does not apply an identity migration or change auth mode. F7's exact recorded draft evidence is retained; local health never replaces separate remote-action evidence.

### 1. Explicit environment and auth mode (conditional server extension)

Production mode requires an approved signed-token identity adapter with issuer/audience/key/JWKS validation, bounded key refresh and mapping to an existing active User row. Studio role comes from that row, not a token role claim or request header; unknown subjects are denied, not auto-created. Development/test mode may retain the existing Header/default-user behavior. Production startup rejects Header mode, missing auth configuration and a test/mock auth fallback before routes are served. Alternative—placing a reverse proxy in front while continuing to trust `X-Studio-User`—leaves a spoofable bypass inside the API.

Before implementation, resolve and review how a verified issuer plus immutable subject maps to an existing User. F8 adds only two nullable identity columns on the existing `User` row, `identity_issuer` and `identity_subject`, protected by a unique pair constraint. A production adapter MUST map the verified `iss + sub` pair to an existing active User; it MUST NOT infer ownership from token email or role alone. This is an additive identity-binding migration, not a new tenant or business object, and downgrade refuses to discard bound identities.

### 2. Startup validates; an operator migrates (conditional server extension)

In production, `lifespan` must not call schema-creating `init_db()` or mutable bootstrap that silently changes approved configuration. Require an explicit migration-head check and documented operator action, with read-only startup validation and safe failure. Dev/test can retain current bootstrap. Alternative—auto-upgrade on service start—can race replicas and make rollback ambiguous.

### 3. Reuse User/Role and define persisted-secret policy

No Organization/Tenant/SSO admin model is introduced. Single-machine production retains private local credentials and safe masking/logging; it does not silently delete/migrate SystemSetting overrides. Only a separately selected server-extension Secret Provider cutover requires external references and deliberate remediation. Logs, health, metrics, exceptions, AuditLog, provider and worker metadata use allowlists in both cases; Settings masking alone does not protect other surfaces.

### 4. StorageProvider under existing revisions (local is final; object-backed is optional extension)

Create local and object-backed implementations of bounded `put/read/exists/delete-if-unreferenced` over immutable content-addressed keys; preserve `MaterialRevision.id/content_hash` and historical business refs. All byte consumers, including legacy DraftMedia, workflow outputs, project assets, Review/Delivery packages and retention, must go through the selected adapter or an explicitly justified compatibility bridge. Existing MinIO export helper is not proof that material reads are object-backed. Reads used for Candidate/package rehash bytes and fail closed on missing/corrupt objects. Production storage cutover needs a complete referenced-byte copy/verify inventory and a recoverable switch; partial mixed roots cannot be declared ready. Alternative—switch only `materials.read_bytes_checked()`—would leave direct `MEDIA_ROOT` callers broken or bypassing verification.

### 5. Reuse and harden existing ops endpoints

After the separately authorized Creative Orchestration enablement on 2026-10-05,
the formal local deployment pins its approved schema to `aco000000001` through
`f7d000000001 -> f8a000000001 -> aco000000001`. The two nullable User identity
columns now exist as Alembic ancestry but remain null/inert; schema presence does
not enable or accept JWT/production identity. Keep the existing local Header auth,
credentials, media and Worker topology. Do not roll back the live SQLite to match
older wording. The prior `f7d000000001` restore and pre-draft User-schema acceptance
below remain historical evidence, not the current approved schema target.
Readiness under the unchanged local runtime mode uses this head by default; explicit test fixtures may
disable the check only when they are not being used as acceptance evidence.
An unapproved descendant migration in the worktree is not permission to upgrade
the local database. Local compatibility validates the approved revision's
membership in the application's single migration chain and exact database head;
the technical server-extension mode retains exact code/config/database head equality. New local fixtures
must separately retain compatibility coverage for the pre-draft User schema, since the historical initial
migration uses current metadata and can otherwise conceal compatibility gaps.

Keep `/api/v1/health` and `/metrics` compatibility while separating shallow liveness from readiness. Readiness checks DB and schema head, selected storage, configured queue/worker requirement and critical auth/secret config; optional disconnected providers do not fail core readiness. Failed required dependencies return a non-success HTTP status with a safe reason code, not `str(exc)`. Metrics use route templates or a bounded label set, not raw URLs/IDs; access to operational detail is controlled. Existing `x-trace-id` is propagated into worker/Workflow/provider/delivery history as safe correlation, without creating a second business state source. Alternative—add a second uncoordinated health endpoint—would leave old unhealthy-200 consumers and unbounded metrics unchanged.

### 6. External effects retain F7 gates

F8 threat-models outbound hosts, credential isolation, request/response size/time bounds, SSRF, side-effect confirmation, idempotency and Unknown reconciliation across every capability. Read-only UI/Settings inventory triggers no network call. F7's exact Publisher verification remains authoritative; production readiness cannot replace missing real-account verification. Alternative—mark all installed plugins active when infrastructure is healthy—would fabricate capability coverage.

Outbound limits are centralized per capability, not reduced to one timeout: URL import/Connector and model discovery use 10 seconds, text generation retains its existing bounded 120-second budget, image generation retains 25 seconds, Commons retains 15 seconds, official WeChat steps retain 25 seconds, and local CLI operations retain bounded process deadlines/output limits. Safe streaming rejects compressed/oversized responses, expiry is checked before dispatch and after reading, and no uncertain media/publication call is retried. An optional `OUTBOUND_ALLOWED_HOSTS` CSV restricts controllable HTTP targets to exact hostnames/IPs before DNS; invalid/wildcard entries fail closed. An empty list preserves existing per-capability public-DNS/fixed-host/exact trusted-private-endpoint rules, including the explicitly registered CPA LAN endpoint. The fixed locally installed MiniMax CLI owns its own network protocol; do not pretend the HTTP allowlist controls its internal traffic. Its fixed subcommands, isolated environment, bounded process/output and accepted-result gates remain separately audited.

An absolute operation deadline is propagated to the shared pinned network stream: DNS waits, TCP, TLS, each read and each socket send use its remaining budget, including across redirects. A per-read HTTP idle timeout alone is insufficient against trickling response headers. HTTPX/HTTPcore logs are suppressed only inside the outbound ContextVar scope, so signed/query URLs and private request/exception data never enter third-party logs; safe Studio operation metadata remains available. Official WeChat retains its existing fixed-host deadline transport. Synthetic/in-memory NetworkStreams without sockets use their bounded write contract; real HTTP streams are the fixed SyncBackend's socket streams.

### 7. Recovery rehearses a restored copy, never live rollback

Legacy retention must also preserve project-bound WorkflowRun history, any run referenced by a Candidate/Master/snapshot/output/immutable Attempt, and validated Text/Variant LLMRun provenance receipts. Raw provider payload pruning is not permission to erase trusted structured receipts or their lineage. Old unreferenced legacy runs remain eligible for the existing policy.

For the formal local profile, back up SQLite and the referenced local media
together; restore into an isolated local environment, verify migration head and
a sample of exact MaterialRevision hashes, query historic Identity/Fact
Boundary/Candidate/Approval/Delivery lineage and rehearse capability disable.
PostgreSQL/MinIO backup and restore is non-applicable extension reference, not
an expected upgrade or gate for this final single-machine production. Downgrade only where its preflight proves
no incompatible history; destructive rollback is not an automatic recovery
path. No production backup, restore, migration or deployment is executed by
this OpenSpec proposal.

### 8. Golden and full-chain acceptance are distinct gates

Versioned Identity Golden fixtures cover Brand/Persona voice, boundaries, differentiation and frozen snapshot continuity. Content Golden fixtures cover facts, Brief, three modalities and channel adaptation. Deterministic checks run automatically; generative quality evidence records provider/model/version, input/output hashes and human reviewer when needed. Full integration exercises Opportunity→Project→Identity→Brief/Fact Boundary→Matrix→all three Masters→Variant→Candidate→Approval→Authorization→local/verified Delivery→Receipt→Performance→Learning; each step's exact lineage is queryable. Real Platform acceptance is scoped to available, separately authorized account/action/form combinations; absent credentials are reported `unverified`, not simulated.

The local-package branch may stop at authorized handoff. It reaches PublishedContentRecord/Performance/Learning only after a real publication is separately confirmed by a qualifying `human_confirmed` DeliveryReceipt with `delivered_at` and exact Candidate/Target ownership/hash; `package_ready`, a ZIP download or an unresolved Unknown is insufficient. If no actual publication is attested, record the upstream local chain as passed and the downstream publication/learning branch as not exercised, not fabricated success.

## Risks / Trade-offs

- Literal server-extension startup is stricter → do not enable that branch for a terminology correction; local production retains its existing runtime.
- Existing direct media paths are numerous → inventory each reader/writer and run mixed old/new revision regressions before switching any production storage mode.
- Historical SystemSetting values may contain plaintext secrets → preserve masking, private configuration and safe logging; do not silently migrate/delete personal credentials. Separate Secret Provider cutover is outside local production acceptance.
- Queue/worker availability depends on deployment topology → readiness checks only required configured components and uses bounded probes; optional providers remain independent.
- Golden model output is non-deterministic → version fixtures and record review/provenance; do not score it as a deterministic unit pass.
- No real external account may be available → implementation can be complete locally while per-platform verification remains explicitly incomplete.

## Migration Plan

This terminology correction has no migration plan: no new table/dependency/runtime setting and no database/media/credential/Worker mutation. Preserve the accepted isolated SQLite/media recovery and product evidence. PostgreSQL/MinIO/auth references are outside the final use plan; a later requested environment switch must first receive separate scope, authorization and a DB-plus-bytes recovery plan. Do not run existing startup/migration/seed commands as part of doc validation.

## Open Questions

- No deployment choice remains open for current use: this computer, SQLite, local media and loopback are final.
- Issuer/audience/Secret Provider/object storage are questions only if a later server or identity extension is explicitly requested; they do not block 82/82 acceptance.
- Real account/action evidence and model-quality coverage stay honest independently of deployment; absent evidence remains unverified without inventing success.

## Source-package preservation audit

The source ten requirements map to: production auth; secrets; storage; correlated operations; health/readiness; untrusted external capabilities; recovery; Identity/Content Golden; full ChannelVariant integration; and real-platform Publisher evidence. F8 adds current-code-specific controls for startup writes, unhealthy-200/raw errors, metric cardinality and direct media callers; none of the source requirements are treated as already implemented by having a spec.
