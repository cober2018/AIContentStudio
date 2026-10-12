## Why

F6B–F7 provide the product lifecycle. F8 makes it operable, auditable and recoverable for the owner's final single-machine production environment: this computer, SQLite, the configured local media library and loopback-only API/Web. This is the actual production deployment, not a temporary stage awaiting servers. Keep the existing startup, credentials, identity behavior and configured asynchronous Worker; do not claim unavailable external accounts or model quality were verified.

## What Changes

- Retain the current loopback-only identity/startup behavior. JWT/issuer-subject mapping and stricter startup under literal technical `APP_ENV=production` are out-of-scope extensions, not prerequisites for this computer's formal use.
- Preserve the real database, media, credentials and configured Worker topology; perform no migrations or runtime/configuration changes for terminology alignment.
- Harden secret handling and redact provider/runtime errors, logs, metrics, health and audit projections. Independent Secret Provider cutover is optional extension work; safe local credential use remains required.
- Introduce an infrastructure-only StorageProvider for immutable MaterialRevision bytes, inventory all direct `MEDIA_ROOT` readers/writers, and verify exact hashes without changing business IDs or duplicating Asset truth.
- Extend the existing `/api/v1/health`, `/metrics` and request trace implementation into distinct liveness/readiness, bounded route-templated metrics and request→worker→workflow→delivery correlation. Required core dependencies fail readiness; optional unverified providers do not.
- Add SQLite plus referenced-media backup/restore rehearsal, byte integrity checks, recovery and capability-disable runbooks; PostgreSQL/MinIO/server guidance is non-applicable extension reference, not an expected upgrade. Do not perform destructive rollback of history.
- Define versioned Identity/Content Golden and full Opportunity→Learning integration acceptance, with real-platform verification only for explicitly authorized accounts that have actual read-back or human evidence.
- Keep organization, invite, tenant and enterprise SSO administration outside F8; do not treat implementation-complete, configured and externally verified as synonyms.

The formal F8 production and acceptance profile is the owner's final
single-machine deployment: SQLite, the configured local immutable media library,
and loopback-only API/Web. Maintain easy startup, diagnosis, backup and recovery.
PostgreSQL, MinIO, JWT, independent Secret Provider, containers, reverse proxy and
multi-host deployment are not prerequisites or planned upgrades. The code's
literal `APP_ENV=production` has separate server-extension checks; do not set it,
install components or invent configuration merely for the production name.
Loopback restricts inbound access, not authorized outbound model/WeChat API calls.

The original checklist's server authentication/schema activation
(0.7, 1.1–1.10), production secret-provider cutover (2.4–2.6), and a new real
remote publication/downstream acceptance (9.5–9.7), and production object-storage
implementation (3.3) are outside the final single-machine production scope.
These 18 extension records remain unchecked and unverified; they are neither
removed nor counted as passed or current production gaps. Formal acceptance has 82
tasks; the previous 83-count incorrectly included excluded MinIO implementation.
Outbound safety, credential separation, independent reviews and final
evidence remain formal production gates; accepted 82/82 evidence is preserved.
Existing draft-only evidence is not public publication evidence, and contract
tests are not model-quality review. This correction authorizes documentation
and active-spec alignment only, not commit, canonical sync/archive, deployment,
formal migration or fresh generation/publication acceptance.

## Capabilities

### New Capabilities

- `production-readiness-operations`: single-machine production secrets, local storage, observability, health/recovery and honest Golden/integration evidence; conditional server-auth and real-platform extension records remain preserved.

### Modified Capabilities

- `product-settings`: Team/Advanced sections must reflect the actual active auth/runtime mode and safe readiness state without pretending production org/SSO management exists.

## Impact

The accepted implementation already covers local operations/storage/recovery and safety. This correction changes only proposal/design/tasks/deltas, status/matrix, README and existing runbooks. It changes no code, database, material root, identity behavior, credentials, Worker, dependency or migration. Any later runtime/server extension requires separate scope and authorization; no push, deployment, remote publication, canonical sync or archive is authorized here.
