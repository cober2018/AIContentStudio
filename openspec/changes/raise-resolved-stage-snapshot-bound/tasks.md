## 1. Bound

- [x] 1.1 Add `RESOLVED_STAGE_MAX_BYTES = 512 * 1024` in `stage_contracts.py`.
- [x] 1.2 Use it in `stage_resolver.resolve_stage` (all three checks), `stage_invocations` (validation and input snapshot), `stage_master_adoptions` and `stage_domain_adoptions` resolved rereads, `stage_domain_integrations.native_media_resolution`, and `digest()`.

## 2. Verify

- [x] 2.1 On a DB copy: persona 2 new work script with `@3` + methods 4/6/8 previews ready; U72 script / shots / master / prepare preview without `stage_value_too_large`.
- [x] 2.2 Run the API test suite; compare with the known 7 unrelated failures.
- [x] 2.3 Restart the API with `launchctl kickstart` after confirming no running or claimed attempts; repeat one live preview.

## 3. Records

- [x] 3.1 Update findings/progress in `improve-persona-content-methods` and this change's README.
- [x] 3.2 Only if the user asks (confirmed 2026-10-21): turn methods 4/6/8 back on for persona 2.

## Verification record

- 2.1 (DB copy, 2026-10-21): persona 2 new work script with `@3` + methods 4/6/8: 133 KB, ready. U72 script 261 KB ready; shots 228 KB, master 260 KB, prepare 185 KB assemble (blocked only by `upstream_not_succeeded`, the normal waiting state).
- 2.2: 2,789 passed, 28 skipped, 7 failed (the same known failures in migrations, model/plugin routing, topic suggest, ACO schema; none touch stage bounds).
- 2.3: no claimed/in-progress executions or running attempts; API restarted with `launchctl kickstart`. Live: U72 script preview ready. Persona 2 revision 7 (methods 4/6/8 back on beside `@3`); new test work U77 script preview ready, 4 methods, 134 KB.
