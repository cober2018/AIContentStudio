## Why

F6B–F7 can provide the product lifecycle, but current startup still accepts spoofable `X-Studio-User` identity, uses local media paths, and exposes a single health probe whose degraded body may contain raw exception text. F8 makes a completed implementation operable and auditable in a production configuration without claiming that unavailable third-party accounts were verified.

## What Changes

- **BREAKING for production mode:** refuse development-header/default-user authentication; require a configured, validated production identity mapped to the existing durable User/Role authorization model. Development/test behavior remains explicitly limited to those modes.
- Separate production startup validation and explicit migrations from development bootstrap that currently creates tables and seeds mutable data. Do not run destructive migrations on startup.
- Harden secret handling and redact provider/runtime errors, logs, metrics, health and audit projections; define treatment of existing persisted secret overrides before production enablement.
- Introduce an infrastructure-only StorageProvider for immutable MaterialRevision bytes, inventory all direct `MEDIA_ROOT` readers/writers, and verify exact hashes without changing business IDs or duplicating Asset truth.
- Extend the existing `/api/v1/health`, `/metrics` and request trace implementation into distinct liveness/readiness, bounded route-templated metrics and request→worker→workflow→delivery correlation. Required core dependencies fail readiness; optional unverified providers do not.
- Add local SQLite backup→restore→migration rehearsal, byte integrity checks, recovery and capability-disable runbooks; keep PostgreSQL/MinIO rollout guidance as a future profile and do not perform destructive rollback of history.
- Define versioned Identity/Content Golden and full Opportunity→Learning integration acceptance, with real-platform verification only for explicitly authorized accounts that have actual read-back or human evidence.
- Keep organization, invite, tenant and enterprise SSO administration outside F8; do not treat implementation-complete, configured and externally verified as synonyms.

The formal F8 acceptance profile is the single-operator local deployment:
SQLite, the configured local immutable media library, and loopback-only API/web
access. PostgreSQL, MinIO and multi-host deployment remain future profiles and
are not gates for this local acceptance.

The user also confirmed that production authentication/schema activation
(0.7, 1.1–1.10), production secret-provider cutover (2.4–2.6), and a new real
remote publication/downstream acceptance (9.5–9.7), and production object-storage
implementation (3.3) are deferred. These 18
obligations remain recorded, unchecked and unverified; they are not silently
removed or considered passed. The local acceptance set therefore has 82
tasks; the previous 83-count incorrectly included excluded MinIO implementation.
Outbound safety, credential separation, independent reviews and final
evidence remain local gates. Existing draft-only evidence is not public
publication evidence. This scope decision does not authorize commit,
canonical sync, archive, deployment or formal database migration.

## Capabilities

### New Capabilities

- `production-readiness-operations`: production auth, secrets, storage, observability, health/recovery and Golden/integration/real-platform acceptance.

### Modified Capabilities

- `product-settings`: Team/Advanced sections must reflect the actual active auth/runtime mode and safe readiness state without pretending production org/SSO management exists.

## Impact

Targets `deps.py`, `config.py`, `main.py`, `observability.py`, health router, media/storage readers, worker propagation, existing User/Role and SystemSetting paths, deployment scripts and acceptance fixtures. No new persistent business object is planned; any unplanned durable schema requirement pauses apply for specification revision. F8 business apply follows F7 gates. This proposal authorizes no push, deployment, production migration, credential transmission, remote publication, canonical sync or archive.
