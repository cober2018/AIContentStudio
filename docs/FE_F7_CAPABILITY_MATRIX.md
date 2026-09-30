# FE-F7 capability implementation and evidence matrix

## Scope and interpretation

Implementation input baseline: local `main@707fc34`, F7 92/105 before this audit; this batch closes the 10.4/10.10 record obligations for 94/105. This is a repository/acceptance matrix, not a claim about live deployment or every database's configuration. No credential values, stored endpoint addresses, verification evidence text or account identifiers were inspected or printed.

`Implemented` means a real loaded code path exists. `Externally unverified` means no qualifying real-platform evidence was established by this audit. Fixture scope and externally verified scope must never be conflated. The PRD remains the product goal; local manual packages do not replace remote draft-box requirements.

## Matrix

| Capability | Actual implementation | Established evidence | Missing / safe behavior |
|---|---|---|---|
| Internal Studio Data Source | Existing typed plugin and snapshots | Backend/project regression | Does not connect arbitrary external plugins |
| Typed API Connector | Explicit exact registration/Endpoint mapping, bounded GET, probe and snapshots | Prior configured isolated endpoint acceptance; scoped persistence regressions | Real source-specific credentials/configuration/evidence still needed; generic Connector is not Notion/SQL |
| Wikimedia material search | `search.wikimedia.commons@1`, bounded metadata/download and explicit rights acceptance | Real decoded fixture bytes, exact revision, cross-Unit browser consumption | Actual Commons read/import remains unverified; fresh read-only search attempt again stopped with UnsafeUrlError, no DNS/private-address bypass |
| Native OpenAI image | `image.openai@1`, exact existing KEY_IMAGE config and one bounded POST | 28 native HTTP transport regressions plus real PNG stage/database acceptance | Explicit supported configuration and separately authorized paid request needed; no source-image edit or fallback |
| Legacy WeWrite image | `asset_provider.wewrite_image@1` retained | Honest unavailable boundary | Mutable global config/internal retry cannot attest exact runtime; no typed execution promotion |
| Video generation | Typed protocol / accepted-byte contract only | MP4 decode, rights/provenance fixture regressions | No production video_provider implementation loaded by media bootstrap; unavailable |
| TTS | Typed protocol / exact audio acceptance only | WAV byte/MIME/hash fixture regressions | No production tts_provider implementation loaded by media bootstrap; unavailable |
| ASR | Bounded suggestion/receipt, explicit Video local acceptance and save provenance | Fixture provider/backend/Video browser checks | No production asr_provider implementation loaded by media bootstrap; actual transcription unverified |
| Text render | Production modality deterministic render and scoped verification path | Actual deterministic render/check/Candidate/local package regressions | Must check exact scope/runtime/current context per action; not remote publication |
| Graphic render | `graphic.chromium@1`, explicitly configured browser/font, real PNG and exact scoped verification | Real Chromium PNG and isolated scope/editor/browser acceptance | Local evidence is not external model verification; unsupported fonts/styles fail rather than substitute |
| Video final render | Existing manual exact asset attestation | Video v2/exact refs/render-input/hash/approval/package regressions | No installed automatic final Video renderer; cannot claim generated final video |
| Local delivery | `publisher.copy@1` / explicit manual handoff, v1–v5 dispatch | Frozen Candidate→Approval→Authorization→ZIP and browser acceptance | ZIP/package-ready does not establish publication |
| WeChat remote draft | Legacy `publisher.wechat.wewrite@1` preserved; frozen v5 projection is implemented | Projection/no-fallback and invalidation/unknown/reconciliation regression | Runtime fingerprint intentionally unavailable: CLI global account and converter cannot prove account-bound immutable content; not executable or verified |
| X/Douyin/Xiaohongshu remote effects | No verified installed Publisher scope | Fail-closed regressions | Controlled Variant/local package support is not remote publishing support |

Loaded-provider evidence was obtained with explicit media/publisher bootstrap and descriptor-only registry reads: search=[Commons], image=[legacy WeWrite, native OpenAI], video/TTS/ASR=[], media renderer=[Graphic Chromium], publisher=[copy, legacy WeWrite]. This is not a scan of all node/Production adapter registries or a runtime probe.

## Database / deployment distinction

A read-only inspection of the **existing default local file** `apps/api/content_studio.db` found Alembic version `d4audit00004` and no capability_registration / capability_verification tables. No schema, settings or data were changed. This is a sampled local file, not proof of the effective DATABASE_URL of a running process or production. The application must not be described as ready against this file solely because isolated F7 migrations/tests passed. Selecting/migrating a deployment database is a separately authorized operational step; first identify the actual process/database.

## Acceptance debt / next decision

This batch additionally closes the existing bounded-reader defects, not new integration scope: 11 RED→GREEN compression/header/slow/empty/redirect regressions, 84 targeted tests, full backend 1446 passed /2 skipped /8 existing warnings (85.77s), TypeScript/Vite/FE-P1, OpenSpec strict30/30, scoped Ruff/diff, independent plan and implementation/matrix reviews APPROVE. The reviewers inspected sources but did not re-run commands. No new frontend/browser acceptance, migration or dependency is claimed.

- F7 8.3/8.5 remote implementation is still incomplete despite the safe projection; no safe WeWrite runtime has been established.
- F7 10.2/10.3/10.5/10.6 actual external/account acceptance is not satisfied by fixtures. Credentials, chosen providers and exact account/action authority are required.
- F7 10.4/10.10: missing implementations/configuration/evidence are explicitly listed above. This matrix does not close 10.11 ARCHIVE_READY or F8 0.1.
- Existing CLI cannot meet the current no-rewrite/account-binding contract. An account-bound upload replacement needs an explicit implementation decision; real platform requests and draft creation remain separately authorized. Do not enable the old bypass or label a replacement HTTP adapter as a proven WeWrite scope.
- F8 production auth/stable subject binding, storage, health, recovery/Golden/end-to-end/runbook work remains unapplied; completing this audit is not completing F8.

No push, deploy, production migration, canonical sync or archive. A fresh read-only Commons search was attempted and refused by existing URL safety validation; no successful external read, paid model request, account effect or provider verification resulted. Validation was not disabled.
