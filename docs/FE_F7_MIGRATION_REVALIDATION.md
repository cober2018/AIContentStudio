# FE-F7 latest migration revalidation — 2026-09-30

## Scope and baseline

Actual baseline: local `main@c828672`, latest Alembic head `f7b000000001`. This is verification of existing migrations, not new implementation, production migration, deployment or F8 apply. Prior PostgreSQL evidence ended at `f7a000000001`; it did not prove the later renderer-scope migration.

## Isolation and evidence

Created only the temporary container `aics-f7b-gate-20260930` from existing `postgres:16-alpine`, with auto-remove, a generated loopback port (`127.0.0.1:32771`) and a disposable database `aics_f7b_gate`. PostgreSQL reports **16.15**. No existing container/database was used or altered. The temporary container was stopped and auto-removed after readback; its synthetic database is intentionally disposable. The gate source remains at `/tmp/aics-f7-readiness-Etf53d/postgres_gate.py`.

Actual application Alembic `upgrade head` succeeded from a fresh database. A separate guarded Python gate invoked the real Alembic commands against only that exact local test target and asserted database state, not compiled DDL.

## Passed PostgreSQL gates

1. `f7b000000001 → f6e000000001 → head`: actual downgrade/upgrade succeeds on empty capability tables. Final columns, named checks, indexes and foreign keys equal the initial latest-head schema.
2. With one synthetic prior `publisher_action` verification, `f7b → f7a` preserves every verification field. Upgrade back to head preserves that row and schema.
3. With retained prior verification, the `f7a → f6e` downgrade raises `retained CapabilityVerification history`. Transaction rollback preserves the version and all verification rows.
4. With a synthetic `renderer_output` row added at latest head, `f7b → f7a` raises `retained renderer verification`. Version, both rows and all capability constraints remain unchanged.

Final head: `f7b000000001`. Capability schema SHA-256: `c9045fe501f6462dcb76ea0a8fc73ec629ebed77399256aeaa8b4ae25d4013d6`.

Synthetic rows prove migration preservation/refusal, **not real publisher or renderer verification**. This run does not cover cross-worker provider configuration, PostgreSQL concurrent source revocation, publisher effects, application-role privileges or backup/restore.

## Public search attempt — not accepted

The actual installed Wikimedia provider was invoked with an explicit bounded image search. The request failed before HTTP dispatch because current DNS resolves `commons.wikimedia.org` to **198.18.0.41**, which Python classifies as non-global. `pinned_transport` correctly returned `UnsafeUrlError`. No fake search results, download, MaterialRevision, Project attachment or verification were produced. No DNS/SSRF/proxy policy was weakened. F7 task10.2 stays open.

## Remaining gates

Fresh existing SQLite migration regressions: `tests/test_migrations.py` plus `tests/test_f7_renderer_migration.py`, **7 passed /5 existing warnings,1.24s**. First invocation referenced a nonexistent renderer test file and ran no tests; corrected to the actual migration test path before collecting this result. OpenSpec all-strict **30/30** and `git diff --check` pass. No full backend/frontend/browser rerun is claimed for this documentation-only batch; previous results remain dated separately.

Independent read-only evidence review: **APPROVE**, restricted to gate assertions and documentation fidelity. Reviewer did not independently execute the database/network commands; main-agent tool results provide execution evidence. This is not full F7 implementation review.

F7 remains **95/105**. Real supplier/account evidence, account-bound immutable publisher implementation, full stage review and final acceptance remain incomplete. These new PostgreSQL results improve the migration evidence only; they do not close task10.7 or permit F8 to start. Public network access and the separately requested publisher design choice are still unresolved.
