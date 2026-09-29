## 0. Baseline/security review
- [ ] 0.1 Start after F7 implementation gates pass.
- [ ] 0.2 Inventory auth, secrets, storage, worker, logging, migrations and deployment docs.
- [ ] 0.3 Threat-model external capabilities and side-effect routes.
- [ ] 0.4 Record production-readiness gaps without inventing tenant/org/SSO features.
- [ ] 0.5 Record full backend/frontend/OpenSpec baseline.
- [ ] 0.6 Audit existing `deps.py` default Header user, `main.lifespan()` bootstrap writes, `/api/v1/health` degraded-200/raw error, raw-path metric labels and all direct `MEDIA_ROOT` readers/writers before implementation.

## 1. Production authentication
- [ ] 1.1 Make development-header auth explicitly development/test only.
- [ ] 1.2 Add secure production auth adapter boundary.
- [ ] 1.3 Implement signed JWT verification with configured issuer/audience/key/JWKS or equivalent approved secure mechanism.
- [ ] 1.4 Map authenticated identity to existing User/Role.
- [ ] 1.5 Prevent untrusted token role claims from bypassing durable authorization.
- [ ] 1.6 Add expiry/issuer/audience/signature/unknown-user tests.
- [ ] 1.7 Update Settings auth-mode truth.
- [ ] 1.8 No org/invite/tenant admin UI is implied.
- [ ] 1.9 Production identity maps only to an existing active User; reject Header/default-user/auto-create and untrusted token role claims on every protected route.
- [ ] 1.10 Production startup refuses missing auth/schema configuration and does not run `init_db()`, migration or mutable template/settings seed.

## 2. Secrets/config hardening
- [ ] 2.1 Classify public vs secret configuration.
- [ ] 2.2 Ensure safe projections never expose plaintext.
- [ ] 2.3 Scrub secrets/credential URLs from logs/errors/audit.
- [ ] 2.4 Add production startup validation for required secrets.
- [ ] 2.5 Prefer env/secret-provider references in production.
- [ ] 2.6 Document/implement safe handling of existing persisted secret overrides.
- [ ] 2.7 Add secret regression tests.
- [ ] 2.8 Inventory legacy plaintext SystemSetting overrides and require explicit production remediation without printing values or silently deleting them.

## 3. Storage provider
- [ ] 3.1 Define internal StorageProvider contract.
- [ ] 3.2 Implement local provider preserving current dev/test behavior.
- [ ] 3.3 Implement production object-storage-compatible provider/config.
- [ ] 3.4 Preserve MaterialRevision hash/business IDs.
- [ ] 3.5 Verify bytes/hash on reads used by Candidate/package.
- [ ] 3.6 Prevent safe API path disclosure.
- [ ] 3.7 Add missing/corrupt/orphan byte diagnostics.
- [ ] 3.8 Add storage integration tests.
- [ ] 3.9 Route all Material, legacy DraftMedia, workflow/project output, Review/Delivery package and retention byte access through the selected provider or a documented compatibility bridge.
- [ ] 3.10 Rehearse complete referenced-byte copy/hash verification before production storage cutover; reject partial mixed-root readiness and preserve a recoverable rollback path.

## 4. Observability/correlation
- [ ] 4.1 Add request/correlation IDs.
- [ ] 4.2 Propagate into worker/Workflow/external capability execution.
- [ ] 4.3 Attach actor/project/unit/run/master/variant/candidate/target IDs where available.
- [ ] 4.4 Attach capability key/version and duration/status.
- [ ] 4.5 Define safe error categories.
- [ ] 4.6 Ensure no secret/raw private content leaks by default.
- [ ] 4.7 Add audit query/debug support.
- [ ] 4.8 Add observability tests.
- [ ] 4.9 Replace raw dynamic request paths in metric labels with bounded route templates and verify private IDs/secret-like paths cannot expand series or leak.

## 5. Health/readiness/runtime
- [ ] 5.1 Split the existing `/api/v1/health` behavior into truthful liveness and readiness without adding a conflicting second status source.
- [ ] 5.2 Make required-dependency readiness failures return non-success HTTP status and safe reason codes, never HTTP 200 degraded with raw exception text.
- [ ] 5.3 Check DB connectivity and migration-head compatibility.
- [ ] 5.4 Check required storage configuration/reachability.
- [ ] 5.5 Check worker/queue when required by configured runtime.
- [ ] 5.6 Report optional capabilities without network side effects.
- [ ] 5.7 Add startup/readiness failure tests.
- [ ] 5.8 Add safe operational status UI/docs.
- [ ] 5.9 Prove optional unverified providers do not fail core readiness or get probed on a read, while a configured required queue/worker failure does.

## 6. External capability security
- [ ] 6.1 Centralize outbound timeout/body-size bounds.
- [ ] 6.2 Add configurable outbound host restrictions where feasible.
- [ ] 6.3 Verify least-privilege credentials per capability.
- [ ] 6.4 Preserve explicit side-effect authorization.
- [ ] 6.5 Preserve idempotency and Unknown semantics.
- [ ] 6.6 Ensure read-only inventory performs no probe/pull.
- [ ] 6.7 Add audit records for verify/probe/delivery actions.
- [ ] 6.8 Add security regressions.

## 7. Migration/backup/recovery
- [ ] 7.1 Document PostgreSQL backup/restore.
- [ ] 7.2 Automate isolated backup→restore rehearsal.
- [ ] 7.3 Run restored DB migrations to head.
- [ ] 7.4 Validate downgrade preflights without deleting incompatible history.
- [ ] 7.5 Sample MaterialRevision byte integrity after restore.
- [ ] 7.6 Detect missing referenced bytes/orphans.
- [ ] 7.7 Document capability disable/rollback procedure.
- [ ] 7.8 Add recovery acceptance record.

## 8. Golden suites
- [ ] 8.1 Create versioned Identity Golden fixtures.
- [ ] 8.2 Cover Brand/Persona differentiation and boundaries.
- [ ] 8.3 Cover historical snapshot pinning/long-term viewpoint continuity.
- [ ] 8.4 Create versioned Content Golden fixtures.
- [ ] 8.5 Cover fact preservation and Brief adherence.
- [ ] 8.6 Cover Text/Graphic/Video directional consistency.
- [ ] 8.7 Cover Channel Adaptation.
- [ ] 8.8 Record provider/model/version and human review for non-deterministic quality.
- [ ] 8.9 Keep Golden changes explicitly reviewed/versioned.

## 9. Full integration and real-platform verification
- [ ] 9.1 Build isolated Opportunity→Project→Identity→Brief/Boundary setup.
- [ ] 9.2 Exercise Matrix→Text/Graphic/Video Masters.
- [ ] 9.3 Exercise ChannelVariants and Candidates.
- [ ] 9.4 Exercise Approval/Authorization/local delivery.
- [ ] 9.5 Exercise configured verified remote Publisher only with explicit authorization.
- [ ] 9.6 Read back or human-verify remote result.
- [ ] 9.7 Materialize Receipt/PublishedContentRecord/Performance/LearningCandidate.
- [ ] 9.8 Confirm Unknown/failed delivery never becomes published.
- [ ] 9.9 Confirm complete lineage queryability.
- [ ] 9.10 Produce verified/unverified capability matrix.

## 10. Deployment/runbook/final gates
- [ ] 10.1 Add production configuration template.
- [ ] 10.2 Add API/web/worker startup runbook.
- [ ] 10.3 Add migration/backup/storage/secret runbook.
- [ ] 10.4 Add reverse-proxy/TLS/auth expectations.
- [ ] 10.5 Run full backend suite.
- [ ] 10.6 Run full frontend build/bundle/browser suites.
- [ ] 10.7 Run all OpenSpec strict/lint/diff gates.
- [ ] 10.8 Independent security/operations review.
- [ ] 10.9 Independent end-to-end product architecture review.
- [ ] 10.10 Record implementation-complete vs provider-configured vs real-platform-verified statuses.
- [ ] 10.11 Record local final commit and overall ROADMAP_IMPLEMENTED state.
- [ ] 10.12 Do not deploy/push/canonical-archive without explicit authorization.
