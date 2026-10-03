# FE-F8 Production Readiness & Operations Design

## 1. Authentication

Current `development_header` auth is allowed only in development/test.

Production introduces a secure auth adapter boundary using existing User/Role records. Recommended first implementation is standards-based signed JWT verification:
- configured issuer/audience/signing keys or JWKS
- exact subject/email mapping to existing User
- no role claim may silently override durable Studio role unless explicitly configured
- rejected/expired/invalid token exposes no private data
- development header mode refuses to start when `ENV=production`

This does not create organization/tenant/SSO administration UI.

## 2. Secrets

Production startup must distinguish:
- public configuration
- secret references
- secret values

Safe APIs never return plaintext secrets.
Logs/errors/audit metadata never contain secret values or credential-bearing URLs.
Production should prefer environment/secret-provider references; persisted secret overrides must have an explicit migration/disable plan if currently used.

## 3. Storage

Introduce internal `StorageProvider`:
- local filesystem provider for dev/test
- object-storage-compatible provider for production configuration
- put/read/exists/delete-if-unreferenced operations
- content hash verification on every immutable MaterialRevision read
- no raw storage location in safe API

Existing MaterialRevision remains business truth; storage provider is replaceable infrastructure.

## 4. Observability

Every request/worker operation should carry:
- request/correlation ID
- actor
- project/unit when known
- workflow/run/step/attempt
- master/variant/candidate/target when known
- capability key/version
- status/duration/error category

Structured logs are operational telemetry, not a second business state source.

## 5. Health/readiness

Expose safe:
- liveness
- readiness
- DB connectivity
- migration-head compatibility
- worker/queue reachability when required
- configured storage reachability
- critical capability configuration summary without network side effects by default

Readiness must fail for required core infrastructure, not optional unverified providers.

## 6. External capability safety

All external capabilities are untrusted:
- least privilege
- explicit authorization
- credential isolation
- outbound host allowlist/config
- timeout/body size bounds
- side-effect confirmation
- idempotency
- Unknown handling
- audit

No page-load/read-only inventory may trigger a side effect.

## 7. Backup/migration/recovery

Production rehearsal:
- PostgreSQL backup
- restore to isolated DB
- migrate to head
- downgrade only where supported and non-destructive
- migration preflight for incompatible history
- object/material byte integrity sampling
- audit of orphan/missing referenced bytes

No automated destructive rollback of historical content.

## 8. Golden tests

### Identity Golden
Representative fixtures test:
- Brand/Persona voice/boundaries
- Persona differentiation
- long-term viewpoint continuity
- historical snapshot pinning

### Content Golden
Representative fixtures test:
- evidence/fact preservation
- CreativeBrief adherence
- Text/Graphic/Video directional consistency
- Channel Adaptation
- style/format quality

Generative quality checks must record provider/model/version and may require human approval; they are not deterministic unit tests.

## 9. Integration acceptance

Required chain:

`Opportunity
→ ContentProject
→ Identity
→ CreativeBrief/Fact Boundary
→ Content Matrix
→ Text/Graphic/Video Masters
→ ChannelVariant
→ Candidate
→ Approval
→ Delivery Authorization
→ local/verified delivery
→ Receipt
→ PublishedContentRecord/Performance
→ LearningCandidate`

Every link must remain traceable.

## 10. Real Platform

For any Publisher to be `verified`:
`Approved Candidate → Delivery → Read Back / Human Verify`.

If credentials/accounts are absent, code can be complete while capability remains unverified. Release status must explicitly distinguish:
- implementation complete
- provider configured
- real platform verified

## 11. Release/deployment

Provide:
- production configuration template
- migration command/runbook
- API/web/worker startup
- health/readiness checks
- backup/restore runbook
- storage config
- secret config
- reverse proxy/TLS expectations
- rollback/disable capability procedure

No deployment is executed unless separately authorized.
