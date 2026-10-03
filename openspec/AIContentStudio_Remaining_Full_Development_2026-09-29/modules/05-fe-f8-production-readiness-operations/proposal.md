## Why

After professional Text/Graphic/Video, ChannelVariant and replaceable capabilities are implemented, AIContentStudio still needs production-safe operational behavior. North Star requires observable provenance, untrusted external capability boundaries, deterministic/Golden/Integration/Real Platform tests and truthful verification. Current product-settings explicitly exposes development-header authentication limitations.

F8 hardens the system for a production deployment without inventing organization/invite/SSO/multi-tenant product features that are not defined by the canonical product contract.

## What Changes

- Add a production-safe authentication mode using existing User/Role authorization semantics; development-header auth remains development-only.
- Harden secrets/config behavior and production startup checks.
- Add request/run/content lineage correlation and structured observability.
- Add health/readiness endpoints and worker/runtime checks.
- Add storage-provider boundary for local/object-backed immutable material bytes without changing business refs.
- Add external capability audit/security controls and explicit side-effect confirmation.
- Add PostgreSQL migration/backup/restore/recovery rehearsal.
- Add Identity Golden, Content Golden, Integration and Real Platform acceptance suites.
- Add final end-to-end release checklist across Opportunity→Learning.
- Keep capability verification truthful when external credentials/accounts are unavailable.

## Non-goals

- Organization management.
- Invite flows.
- Tenant administration.
- Mandatory enterprise SSO UI.
- Replacing existing business authorization objects.
- Claiming real-platform verification without actual account read-back/human verification.
