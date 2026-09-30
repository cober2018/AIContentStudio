# FE-F7 Batch A — local implementation acceptance

## Independent-review corrections (latest authoritative status)

Independent scoped re-review: **APPROVE**, all four original safety blockers closed. Approval is limited to safety closure, not real Publisher functionality. Latest OpenSpec all-strict 30/30 and diff-check passed; scoped Ruff passed except the unchanged historical SystemConstant TRY004 noted below. Isolated API/Vite and PostgreSQL processes have been stopped; temporary browser/database/media evidence retained.

The first review found four blockers: credential-bearing cross-origin redirects; mutable legacy pull status restoring failed verification; unbound CLI account; CLI rewriting approved content. Cross-origin/downgrade now fails before the redirected request; failed mapped pulls append scoped invalidation events. Installed WeWrite is explicitly unavailable for new remote effects because neither account binding nor immutable upload is proven. Administrator confirmation cannot enable it. Tasks 8.3/8.5 are reopened: **F7 56/105**, not 58/105. Local packages remain available.

Post-correction targeted backend: 92 passed; latest full backend **1230 passed / 2 skipped / 8 warnings, 64.48s**. New frontend/FE-P1 build passed (CapabilitySettings 6.07 / 2.95 kB). New isolated browser report `/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-browser-evidence-hyydf2`: four gates, zero page errors; Publisher gate now verifies UI unavailable and API rejection with no remote publishing, replacing the earlier synthetic successful-recording browser scenario below. Independent re-review is being rerun; earlier counts are historical, not final current gates.

## Scope and baseline

Local `main@be4f0a9` plus uncommitted F7 work. First batch covers durable capability registration/verification, exact API connection profiles, bounded Data Node execution, safe Settings operator UI, and verified-scope enforcement for immutable v5 WeChat delivery. F7 remains 58/105; provider acceptance and full-stage final review are not complete. F8 has not started.

No push, deploy, production migration, real remote publisher execution or canonical sync/archive occurred.

## Actual commands and results

- Backend: `cd apps/api` → `.venv/bin/pytest -q`: **1228 passed, 2 skipped, 8 warnings, 67.01s**.
- Frontend: `cd apps/web` → `npm run build`: TypeScript/Vite and FE-P1 gates passed. `/projects` initial JS 224.75 kB raw / 72.90 kB gzip; Settings 230.12 / 75.07; common Production 279.10 / 88.85. CapabilitySettings loads in an independent 5.86 / 2.83 kB lazy chunk.
- SQLite: backend suite executes fresh migration plus F7 up/down/up and retained-verification downgrade refusal.
- PostgreSQL: ephemeral PostgreSQL 16 container, isolated database `aics_f7_gate`, actual Alembic upgrade head → downgrade f6e000000001 → upgrade head passed. Readback: `f7a000000001` and 13 capability constraints. Container stopped and auto-removed; no production database touched.
- `openspec validate --all --strict`: 30 passed, 0 failed.
- `git diff --check`: passed.
- Scoped Ruff: one pre-existing TRY004 at SystemConstant's unchanged exception line (`content_harness/nodes/__init__.py:115`). All other scoped checks passed; rerun with TRY004 ignored passed. This is not an unconditional clean Ruff result.

## Isolated browser evidence

Script: `apps/web/scripts/fe-f7-capability-browser-acceptance.mjs`.

Guarded isolated API `127.0.0.1:18270`, frontend `127.0.0.1:15670`, temporary SQLite/media directories. Four gates passed, zero page errors:

1. Settings saves a typed API profile, performs a real bounded public HTTPS GET against httpbin, persists mapped SourceDocument/Fact and verification across reload.
2. Production selects the exact verified profile version, saves workflow override, and runs a real Data Node that persists DataSnapshot/source lineage.
3. Synthetic operator evidence records exact account/form/action scope; refresh and explicit revoke preserve append-only history. **No remote publishing was called.**
4. Viewer reads safe inventory but has no administrator verification actions or access to another identity's publisher scope.

Report/screenshots: `/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-browser-evidence-9cYvcr`. Temporary paths are evidence locations, not durable product dependencies.

## Important negative coverage

- Unverified/revoked/drifted/expired capability cannot create a new remote attempt.
- v5 WeChat projection uses exact approved frozen title/body and live public-use PNG/JPEG bytes; no Draft fallback, rewriting, truncation or generated media.
- Unknown publisher result is not automatically retried; duplicate requests do not repeat the side effect.
- Typed Data Source stops streaming above decoded body limit, bounds pagination and total mapped rows, and saves only mapped Fact snapshots.
- Pull/probe failure uses safe reason codes and actor audit; old verification stays historical but non-executable until explicit successful probe.
- Settings selects only safe endpoint metadata columns; no secret config reads and no inventory network calls.

## Still pending

Independent batch review; provider search/import and image/video/TTS/ASR/render acceptance; real account/platform evidence when separately authorized; final F7 capability matrix and full-stage gates; F8. Synthetic CLI/operator tests do not verify any real publisher account.
