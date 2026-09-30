# FE-F7 configured native image path

## Scope and design

Implements task 5.8 using existing `KEY_IMAGE`, `image_provider`, and private stage/accept. No new table, migration, secret store, automatic capability verification, or provider fallback.

Flow: explicit image settings → explicit generation → frozen configuration / public DNS / pinned TCP address → one HTTPS POST → bounded PNG preview → human license/rights confirmation → exact MaterialRevision and optional project reference.

Paths: `apps/api/app/services/openai_image_provider.py`, existing `content_harness/providers.py`, `routers/materials.py`, `system_settings.py`, `product_settings.py`; regression tests in `apps/api/tests/test_f7_openai_image_provider.py`.

## Configuration and execution

Use the existing administrator AI image settings: explicitly select `openai`, an exact supported model, size, HTTPS endpoint ending `/v1`, and image API key. There is no model/key/endpoint fallback. Native settings do not touch WeWrite's global file. Settings/inventory reads and configuration saves do not call a vendor.

Supported controlled models: `gpt-image-1`, `gpt-image-1-mini`, `gpt-image-1.5`, `dall-e-2`, `dall-e-3`. Sizes must belong to the selected model's allowlist; other/newer models and source-image editing are unavailable, not silently substituted. Request uses `n=1`, PNG/base64 output according to the [official Images API contract](https://developers.openai.com/api/reference/resources/images/methods/generate).

The adapter uses installed HTTPX/HTTPCore, zero retries, no environment proxy, no redirect, 25-second HTTP timeout and cumulative read deadline; outer provider wall-clock/capacity protection remains unchanged. TCP connects to a checked public IP while TLS verifies the original hostname. The narrow internal HTTPCore backend hook is exercised by a regression and must be rechecked on dependency upgrades. JSON is capped at 8 MiB and decoded PNG at 5 MiB. Non-identity compression is refused before body reads; actual Pillow validation remains in shared staging.

Only a process-keyed combined implementation/configuration/credential fingerprint is recorded; no independent credential digest, raw response/error, provider prompt rewrite, or secret is copied into durable media provenance. Missing configuration is unavailable; uncertain response/timeout is unknown and never retried. Config changes during generation discard output; rotation makes old preview acceptance fail closed.

## Evidence and limitations

- Initial RED: missing adapter, 19 failures. Native settings and selection failures were separately reproduced before fixes. Compression regression reproduced a successful compressed output before the guard was added.
- Latest targeted adapter/guidance/shared acceptance: 52 passed, 1 existing warning.
- Final post-fix full backend: 1435 passed / 2 skipped / 8 existing warnings, 85.22 seconds. Earlier 1432 was pre-compression-fix and is not the final gate.
- TypeScript/Vite and FE-P1 budgets passed; `/projects` 224.84/72.94 kB raw/gzip, common Production 280.20/89.13 kB. No frontend editor code changes or new browser acceptance are claimed.
- OpenSpec strict 30/30; scoped Ruff and diff check passed. Independent plan review APPROVE; implementation review found compression risk, then narrow post-fix re-review APPROVE. Reviewer inspected code/tests but did not re-run commands.

Tests use HTTP transport fixtures plus real decoded PNG and database acceptance, not paid credentials or vendor calls. This proves the configured adapter code path, not real-provider task 10.3 or completed F7. Existing generated preview UI is reused; no new automatic Master binding/render attestation.

## TODO

Real image/account/provider validation requires separately supplied credentials and explicit effect authority. Video/TTS/ASR actual provider implementations and Publisher closure remain separate F7 work. No push, deploy, production migration, canonical synchronization, or archive was performed.

Re-run: `cd apps/api && .venv/bin/python -m pytest -q tests/test_f7_openai_image_provider.py tests/test_f7_provider_guidance.py tests/test_f7_media_acceptance.py`.
