# FE-F8 acceptance scope

User-confirmed formal profile: SQLite + configured local media library +
loopback-only API/web. Of the original 100 tasks, 18 remain explicitly deferred
and unchecked: 0.7, 1.1–1.10, 2.4–2.6, 3.3 and 9.5–9.7. They retain their original
requirements for future production/remote acceptance and are NOT verified.
Local completion uses the remaining 82 tasks; safety tasks 6.1–6.3 and reviews
10.8–10.9 are not waived. Commit and lifecycle actions require separate authority.

## 0. Baseline/security review
- [x] 0.1 Start after F7 implementation gates pass. F7 implementation `3f28a51` and canonical/archive `a59d5de` are visible locally; `docs/FE_F7_FINAL_LOCAL_GATES.md` retains the scoped 1660/28 backend, Web/performance and independent-review evidence. Commons remains user-deferred, not live verified; draft-only confirmation is not public publication.
- [x] 0.2 Inventory auth, secrets, storage, worker, logging, migrations and deployment docs. Evidence: `docs/FE_F8_BASELINE_AUDIT.md`; no secret values read or printed.
- [x] 0.3 Threat-model external capabilities and side-effect routes. Evidence: bounded threat table in `docs/FE_F8_BASELINE_AUDIT.md`; F7 Unknown/authorization boundaries preserved.
- [x] 0.4 Record production-readiness gaps without inventing tenant/org/SSO features. Evidence: audit records implementation/configured/verified distinctions and keeps org/tenant/SSO outside scope.
- [x] 0.5 Record full backend/frontend/OpenSpec baseline. Evidence: audit records backend, build/budget, strict, Ruff-scope and diff gates; no production migration claimed.
- [x] 0.6 Audit existing `deps.py` default Header user, `main.lifespan()` bootstrap writes, `/api/v1/health` degraded-200/raw error, raw-path metric labels and all direct `MEDIA_ROOT` readers/writers before implementation. Evidence: current seams and direct readers/writers are listed in `docs/FE_F8_BASELINE_AUDIT.md`.
- [ ] 0.7 Resolve and independently review stable issuer/subject → existing active User mapping before implementation approval. The nullable User-column proposal is a draft awaiting explicit schema authorization; no production migration or activation.

## 1. Production authentication
- [ ] 1.1 Make development-header auth explicitly development/test only.
- [ ] 1.2 Add secure production auth adapter boundary.
- [ ] 1.3 Implement and review signed JWT verification with configured issuer/audience/key/JWKS or an approved equivalent. Existing HS256 code is an unaccepted draft, not a completed security gate.
- [ ] 1.4 Map verified issuer+subject to an existing active User/Role.
- [ ] 1.5 Prevent untrusted token role claims from bypassing durable authorization.
- [ ] 1.6 Add expiry/issuer/audience/signature/unknown-user tests.
- [ ] 1.7 Update Settings auth-mode truth.
- [ ] 1.8 No org/invite/tenant admin UI is implied.
- [ ] 1.9 Production identity maps only to an existing active User; reject Header/default-user/auto-create and untrusted token role claims on every protected route.
- [ ] 1.10 Production startup refuses missing auth/schema configuration and does not run `init_db()`, migration or mutable template/settings seed.

## 2. Secrets/config hardening
- [x] 2.1 Classify public vs secret configuration. Evidence: `runtime_config` classifies API keys, credentials, signed URLs, secret headers and vendor signature fields while allowing non-secret environment-reference names.
- [x] 2.2 Ensure safe projections never expose plaintext. Evidence: settings, capability, provider and material safe-view regressions plus isolated Settings browser checks preserve masked/allowlisted output.
- [x] 2.3 Scrub secrets/credential URLs from logs/errors/audit. Evidence: existing connector/media/provider error regressions and bounded F8 secret-policy diagnostics reject credential-bearing values without echoing them.
- [ ] 2.4 Add production startup validation for required secrets.
- [ ] 2.5 Prefer env/secret-provider references in production.
- [ ] 2.6 Document/implement safe handling of existing persisted secret overrides.
- [x] 2.7 Add secret regression tests. Evidence: existing settings, connector, media, provider and F8 secret-classification regressions pass in the fresh full backend run.
- [x] 2.8 Inventory legacy plaintext SystemSetting overrides and require explicit production remediation without printing values or silently deleting them. Evidence: `docs/FE_F8_SECRET_INVENTORY.md` records 6 rows / 3 secret-bearing rows using boolean-only inspection; local credentials were not changed or printed. Production startup/secret cutover remains a deferred obligation; the local-only commit refuses production readiness without claiming completed production authentication.

## 3. Storage provider
- [x] 3.1 Define internal StorageProvider contract. Evidence: `apps/api/app/services/material_storage.py` exposes bounded `put/read/exists/size/delete_if_unreferenced` operations with safe content-addressed keys.
- [x] 3.2 Implement local provider preserving current dev/test behavior. Evidence: local provider uses the configured media root, immutable atomic writes, private generation namespace and legacy absolute-read bridge only outside production.
- [ ] 3.3 Implement production object-storage-compatible provider/config. Deferred under the confirmed SQLite/local-media-only profile. The unaccepted MinIO implementation remains in the working tree, excluded from this local commit; it is not delivered or verified by local-provider tests.
- [x] 3.4 Preserve MaterialRevision hash/business IDs. Evidence: storage changes operate on `file_path`/bytes only; `MaterialRevision.id`, `content_hash` and business references remain database truth.
- [x] 3.5 Verify bytes/hash on reads used by Candidate/package. Evidence: delivery, v4/v5 package and renderer paths use `materials.read_bytes_checked`; targeted material/package/delivery/renderer regression passed.
- [x] 3.6 Prevent safe API path disclosure. Evidence: material/revision serializers expose IDs, hashes, rights and MIME only; raw endpoints return bytes and the admin diagnostics projection omits storage paths/keys.
- [x] 3.7 Add missing/corrupt/orphan byte diagnostics. Evidence: admin-only `GET /api/v1/materials/storage-diagnostics` checks bounded MaterialRevision bytes through the selected provider and reports safe issue codes plus unresolved orphan candidates.
- [x] 3.8 Add storage integration tests. Evidence: existing Material Library, media renderer, ASR suggestion, F7 media and acceptance storage regressions plus the isolated cutover rehearsal all exercise selected-provider writes/reads and hash rejection; no new permanent test code was added under the local-only policy.
- [x] 3.9 Route all Material, legacy DraftMedia, workflow/project output, Review/Delivery package and retention byte access through the selected provider or a documented compatibility bridge. Evidence: `docs/FE_F8_STORAGE_CUTOVER_AUDIT.md` inventories each consumer; legacy absolute reads remain a bounded development/test bridge only.
- [x] 3.10 Rehearse complete referenced-byte copy/hash verification before production storage cutover; reject partial mixed-root readiness and preserve a recoverable rollback path. Evidence: `apps/api/scripts/rehearse_storage_cutover.py` copied and verified 5/5 referenced keys in an isolated new root; no production root or database was changed.

## 4. Observability/correlation
- [x] 4.1 Add request/correlation IDs. Existing trace middleware assigns a bounded per-request ID, returns `x-trace-id` and includes the same ID in the safe structured request log; existing observability regression passed. Propagation to workers and downstream execution remains 4.2–4.4.
- [x] 4.2 Propagate into worker/Workflow/external capability execution. Evidence: bounded ContextVar correlation is persisted into queued generation/workflow JSON context and restored by worker scopes; project events carry the request trace.
- [x] 4.3 Attach actor/project/unit/run/master/variant/candidate/target IDs where available. Evidence: existing ProjectEvent actor/project/entity/payload fields remain the business projection; worker telemetry adds bounded job/run/unit/endpoint context without copying private content.
- [x] 4.4 Attach capability key/version and duration/status. Evidence: bounded operation telemetry records operation, status, duration and optional capability identity fields; worker generation/workflow/connector operations emit it without provider payloads.
- [x] 4.5 Define safe error categories. Evidence: `safe_error_category()` maps timeout/database/validation/external-capability/internal failures to fixed categories and never serializes exception text.
- [x] 4.6 Ensure no secret/raw private content leaks by default. Evidence: correlation allowlist, bounded values, structured operation logging and the audit debug projection exclude bodies, raw errors and credentials.
- [x] 4.7 Add audit query/debug support. Evidence: admin-only bounded `GET /api/v1/ops/audit` supports event/entity filters and returns metadata/telemetry only, never raw `detail_json`.
- [x] 4.8 Add observability tests. Evidence: existing observability and worker-queue regressions pass; a temporary isolated smoke probe verified request-header trace equals persisted ProjectEvent trace; no permanent test fixture or external call was added.
- [x] 4.9 Replace raw dynamic request paths in metric labels with bounded route templates and verify private IDs/secret-like paths cannot expand series or leak. Evidence: route templates exclude private IDs, unknown HTTP methods collapse to `OTHER`, and `/metrics` self-noise is excluded. Production metrics is admin-only; the approved local profile uses loopback restriction and development Header identity, not production authentication.

## 5. Health/readiness/runtime
- [x] 5.1 Split the existing `/api/v1/health` behavior into truthful liveness and readiness without adding a conflicting second status source. Evidence: `/api/v1/health/live` is liveness, `/api/v1/health/ready` is the explicit readiness endpoint, and `/api/v1/health` remains a compatibility alias.
- [x] 5.2 Make required-dependency readiness failures return non-success HTTP status and safe reason codes, never HTTP 200 degraded with raw exception text. Evidence: readiness maps failed checks to HTTP 503 and bounded reason codes.
- [x] 5.3 Check DB connectivity and migration-head compatibility. Production requires exact configured/code/database head equality. Local development defaults to the approved `f7d000000001` and requires one database head and a single code ancestry containing it; an unapproved descendant is not silently accepted as the database head. Wrong/multi/empty heads fail; old User schema without draft identity columns passed actual startup/ORM/browser. Identity approval remains 0.7/1.x.
- [x] 5.4 Check required storage configuration/reachability. Evidence: the selected local provider is probed in all environments; a missing local root returns `storage_unavailable`/503 without creating it or falling back.
- [x] 5.5 Check worker/queue when required by configured runtime. Evidence: queue connectivity and a bounded valid `{"ok":"pong"}` worker probe are separate; no-worker, live-worker and stopped-worker topology probes fail/ready truthfully, and the ping has an overall timeout.
- [x] 5.6 Report optional capabilities without network side effects. Readiness projects the optional LLM provider from in-process settings with `not_probed`/`unavailable` status; it neither calls the provider nor makes optional availability part of the core ready predicate. Required storage/queue probes remain separate 5.4/5.5.
- [x] 5.7 Add startup/readiness failure tests. Evidence: existing health, migration and settings regressions plus temporary isolated probes recorded in `docs/FE_F8_HEALTH_FAILURE_ACCEPTANCE.md`; no permanent test code was added under the local-only policy.
- [x] 5.8 Add safe operational status UI/docs. Evidence: Advanced Settings exposes only bounded required checks after explicit refresh, hides controls from viewers and documents that readiness is not external-capability acceptance.
- [x] 5.9 Prove optional unverified providers do not fail core readiness or get probed on a read, while a configured required queue/worker failure does. Evidence: zero-call optional-provider probe and required worker failure topology diagnostics, plus isolated browser request-count checks.

## 6. External capability security
- [x] 6.1 Centralize outbound timeout/body-size bounds. Local evidence: capability-specific policies, absolute TCP/TLS/read/send deadlines, bounded DNS/redirects and streaming byte limits; slow-header/body loopback probes, 186 existing targeted regressions and final security re-review APPROVE. See `docs/FE_F8_EXTERNAL_CAPABILITY_SECURITY_AUDIT.md`.
- [x] 6.2 Add configurable outbound host restrictions where feasible. Local evidence: optional exact-host restrictions reject before DNS/credential dispatch without weakening per-capability SSRF/redirect rules; security re-review APPROVE. MiniMax CLI internal HTTP is explicitly outside this helper's control.
- [x] 6.3 Verify least-privilege credentials per capability. Local evidence: exact provider/endpoint/account credentials, no cross-origin credential forwarding, and MiniMax subprocess environment allowlist; security re-review APPROVE for local credential separation. Vendor-side grants and production Secret Provider remain unverified/deferred, not inferred from these probes.
- [x] 6.4 Preserve explicit side-effect authorization. Evidence: DeliveryTarget/CapabilityVerification validate exact channel, content form, action, account and publisher scope before a side effect; read-only inventory paths do not dispatch providers. See `docs/FE_F8_EXTERNAL_CAPABILITY_SECURITY_AUDIT.md`.
- [x] 6.5 Preserve idempotency and Unknown semantics. Evidence: DeliveryAttempt/Receipt idempotency keys, bounded publisher results, Unknown/reconciliation and no-auto-retry regressions remain enforced. See `docs/FE_F8_EXTERNAL_CAPABILITY_SECURITY_AUDIT.md`.
- [x] 6.6 Ensure read-only inventory performs no probe/pull. Evidence: Settings, Home, health and capability inventory only project stored state; probe/pull are explicit administrator write routes. See `docs/FE_F8_EXTERNAL_CAPABILITY_SECURITY_AUDIT.md`.
- [x] 6.7 Add audit records for verify/probe/delivery actions. Evidence: CapabilityVerification, AuditLog, ProjectEvent and bounded `/api/v1/ops/audit` retain safe action metadata without raw provider errors, content or secrets. See `docs/FE_F8_EXTERNAL_CAPABILITY_SECURITY_AUDIT.md`.
- [x] 6.8 Add security regressions. Evidence: existing Delivery, Capability, Connector, Media, Settings, Health and Observability regression suites cover fail-closed side effects, redaction, Unknown, no-auto-retry and no-probe inventory behavior; no permanent test code was added under the local-only policy. See `docs/FE_F8_EXTERNAL_CAPABILITY_SECURITY_AUDIT.md`.

## 7. Migration/backup/recovery
- [x] 7.1 Document SQLite/local-media backup/restore for the formal local profile; record PostgreSQL/MinIO as a future deployment profile. Evidence: `docs/runbooks/backup-restore.md` now makes the local profile authoritative and labels the other profiles future-only.
- [x] 7.2 Automate isolated backup→restore rehearsal. Evidence: SQLite online backup and integrity both open the source read-only, refuse an existing destination, and return nonzero on failed integrity. Source/restored integrity were `ok`; WAL backup size equality is not a required correctness condition.
- [x] 7.3 Run restored DB migrations to head. Evidence: an isolated restore was targeted to the approved `f7d000000001` head and read back at that head with `PRAGMA integrity_check=ok`; unapproved `f8a000000001` was not applied.
- [x] 7.4 Validate downgrade preflights without deleting incompatible history. Evidence: current local preflight found 1 retained `provider_generation_task` and 1 bound platform identity; it returned `downgrade_allowed=false` and did not execute downgrade or delete history. Existing f7c/f7d migration guards remain fail-closed.
- [x] 7.5 Sample MaterialRevision byte integrity after restore. Evidence: the current local library's six referenced MaterialRevision byte hashes matched (`matched=6, missing=0, mismatch=0`) and the isolated restored DB remained intact.
- [x] 7.6 Detect missing referenced bytes/orphans. Evidence: bounded admin storage diagnostics read all 6 current MaterialRevision rows and unresolved orphan candidates; isolated local run returned `issue_count=0`, `orphan_candidate_count=0`, `truncated=false`.
- [x] 7.7 Document capability disable/rollback procedure. Evidence: `docs/runbooks/backup-restore.md` documents local capability disable, restore-source selection and non-destructive rollback order.
- [x] 7.8 Add recovery acceptance record. Evidence: recovery DB + copied media started together at approved f7d/no-draft User schema; Project 4's five packages matched every original uncompressed ZIP entry byte. The record does not claim a formal DB cutover.

## 8. Golden suites
- [x] 8.1 Create versioned Identity Golden fixtures. Evidence: `apps/api/evals/goldens/identity.v1.json` and version manifest.
- [x] 8.2 Cover Brand/Persona differentiation and boundaries. Evidence: identity fixture includes two differentiated Personas, Brand boundaries, per-Persona boundaries and forbidden auto-mutation shortcuts.
- [x] 8.3 Cover historical snapshot pinning/long-term viewpoint continuity. Evidence: consumed Identity v1; old Unit 9/Run 1 retained snapshot 9/checksum after Persona revision, while new Unit selected snapshot 12. See Golden README for fixture hash and isolated DB.
- [x] 8.4 Create versioned Content Golden fixtures. Evidence: `apps/api/evals/goldens/content.v1.json` references the existing 30-case `golden_topics.json` without copying its facts.
- [x] 8.5 Cover fact preservation and Brief adherence. Evidence: consumed G001/G003/G006/G009, real freeze_pack + exact citation/evidence/checksum/as_of + Brief fields survived v4; unsupported number produced blocker/409. Semantic review remained unavailable/warning, not a quality PASS.
- [x] 8.6 Cover Text/Graphic/Video directional consistency. Evidence: consumed each required_state against Text6/Graphic8/Video19; local real 4-second H.264 + exact shots/manual attestation reached v4 approval/ZIP with matching render bytes. Douyin script/estimated SRT remains distinct from finished video.
- [x] 8.7 Cover Channel Adaptation. Evidence: consumed Content v1's five exact source-schema/form/Variant-schema/artifact-kind mappings against restored frozen candidates; current browser covered prompt-only, stale, revoked, Unknown and archived negative paths without remote calls.
- [x] 8.8 Record provider/model/version and human review for non-deterministic quality. Evidence: `manifest.v1.json` records the required provider/model/input-output/reviewer fields and explicitly records this local deterministic run as `not_exercised` for real-model quality review.
- [x] 8.9 Keep Golden changes explicitly reviewed/versioned. Evidence: manifest has fixture/change versions, review scope, change log and external-platform status; no historical fixture is overwritten.

## 9. Full integration and real-platform verification
- [x] 9.1 Build isolated Opportunity→Project→Identity→Brief/Boundary setup. Evidence: actual Opportunity4 assessment/qualified/explicit idempotent conversion→Project4; new project remained evidence_needed before explicit Boundary. See local full-chain record.
- [x] 9.2 Exercise Matrix→Text/Graphic/Video Masters. Evidence: one Project4, Text Unit6/Master6, Graphic Unit7/Master8, Video Unit8/Master9; browser Matrix read zero writes and explicit selection only. Video9 is a script; final video separately covered by Golden19.
- [x] 9.3 Exercise ChannelVariants and Candidates. Evidence: same project's five exact v5 series reached Candidate6/7/8/9/10 with currentness/order-response/stale protections; existing suites preserve v3/v4.
- [x] 9.4 Exercise Approval/Authorization/local delivery. Evidence: browser approved/authorized/downloaded all five local packages; restored DB/media re-export matched all original entry bytes. No remote call or publication claim.
- [ ] 9.5 Exercise configured verified remote Publisher only with explicit authorization.
- [ ] 9.6 Read back or human-verify remote result.
- [ ] 9.7 Materialize PublishedContentRecord/Performance/LearningCandidate only after an actual publication has a qualifying `human_confirmed` DeliveryReceipt with `delivered_at` and exact Candidate/Target/hash; an authorized local package or ZIP download alone stops before this branch. Record absent publication evidence as not exercised, not success.
- [x] 9.8 Confirm Unknown/failed delivery never becomes published. Evidence: delivery router Unknown/timeout/no-auto-retry and published-history negative regressions passed; local package does not create downstream published/learning rows.
- [x] 9.9 Confirm complete lineage queryability. Evidence: project read models, frozen v4/v5 manifests, DeliveryTarget/Receipt, ProjectEvent and bounded admin audit projection retain the exact project/unit/master/variant/candidate/target/check/telemetry chain.
- [x] 9.10 Produce verified/unverified capability matrix. Evidence: `docs/FE_F8_LOCAL_CAPABILITY_MATRIX.md` separates implemented, locally verified, configured and real-remote-not-exercised statuses.

## 10. Deployment/runbook/final gates
- [x] 10.1 Add production configuration template. Evidence: `docs/runbooks/production.env.example` contains placeholders only and explicitly remains future deployment reference.
- [x] 10.2 Add API/web/worker startup runbook. Evidence: `docs/runbooks/production-readiness.md` defines readiness-first startup and local profile separation.
- [x] 10.3 Add migration/backup/storage/secret runbook. Evidence: production runbook links the existing backup/recovery and secret inventory rules and requires copy/hash rehearsal before storage cutover.
- [x] 10.4 Add reverse-proxy/TLS/auth expectations. Evidence: production runbook requires trusted proxy/TLS, JWT subject mapping, admin-only ops surfaces and development Header auth isolation.
- [x] 10.5 Run full backend suite. Final approved commit-snapshot evidence on 2026-10-04, cwd `apps/api`: `PYTHONPATH=. APP_ENV=test LLM_PROVIDER=mock DATABASE_URL=sqlite:////private/tmp/aics-f7-close-Ro2XB0/worker-test.sqlite .venv/bin/python -m pytest -q --tb=short` → 1660 passed, 28 skipped, 8 warnings in 85.99 seconds, exit 0. The incorrect repo-root run's 32 path failures and first projection's 3 import failures are not counted as PASS.
- [x] 10.6 Run full frontend build/bundle/browser suites. Fresh TypeScript/Vite/FE-P1 PASS, 13 current product browser gates plus 7 F8 runtime-status gates/no page errors, and post-fix legacy/new Settings no-probe checks. Evidence paths are in the local full-chain record; historical runs were not used as substitutes.
- [x] 10.7 Run all OpenSpec strict/lint/diff gates. Evidence: OpenSpec strict 34/34, full app/recovery-script Ruff PASS and `git diff --check` PASS after the final fixes on 2026-10-04.
- [x] 10.8 Independent security/operations review. Prior overall review plus final targeted re-review closed the absolute-deadline and query-log blockers; Harvey returned local-scope APPROVE on 2026-10-04. Reviewers inspected code, not independently reran the reported full suite/browser gates; production/remote scope remains deferred.
- [x] 10.9 Independent end-to-end product architecture review. Prior overall review plus final targeted re-review closed special-path SQLite backup and conflicting-reference hash blockers; Copernicus returned 10.9 APPROVE on 2026-10-04, retaining the approved lineage/product portions. See `docs/FE_F8_LOCAL_FINAL_STATUS.md`.
- [x] 10.10 Record implementation-complete vs provider-configured vs real-platform-verified statuses. Evidence: `docs/FE_F8_LOCAL_CAPABILITY_MATRIX.md` and `docs/FE_F8_LOCAL_FINAL_STATUS.md` keep those states separate.
- [x] 10.11 Record local final commit and overall ROADMAP_IMPLEMENTED state. Authorized local implementation commit `ade4ce04870b854d262cdbc55250233cb293f54e` is on main; `docs/FE_F8_LOCAL_FINAL_STATUS.md` records ROADMAP_IMPLEMENTED_LOCAL=true for the approved SQLite/local-media/loopback profile and ROADMAP_IMPLEMENTED_PRODUCTION=false. Local tasks 82/82; original tasks 82/100 with 18 deferred obligations preserved unchecked.
- [x] 10.12 Do not deploy/push/canonical-archive without explicit authorization. The user separately authorized the above local main commit; no push, deployment, formal migration, canonical synchronization or archive was performed. Lifecycle actions remain subject to separate authority.
