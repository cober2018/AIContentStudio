# FE-F7 isolated browser revalidation — 2026-09-30

## Scope and baseline

Local `main@b940547`; no business-code changes in this batch. Re-run the existing approved Settings/Production/local Delivery browser paths against fresh isolated databases. External supplier/account verification, final F7 security review and F8 prerequisites are separate gates.

Seven scripts passed **52 gates**, with zero page errors. This closes task 10.8 for implemented local UI flows, not real remote delivery. Tasks 10.2/10.3/10.5/10.6 remain pending; F7 is not ARCHIVE_READY and F8 is not applied.

## Results and evidence

All report paths below are under `/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/`. Temporary reports/screenshots are inspectable evidence, not durable application dependencies.

| Script in `apps/web/scripts/` | Gates | Evidence type | Artifact directory |
| --- | ---: | --- | --- |
| `fe-f7-media-browser-acceptance.mjs` | 4 | Real decoded PNG / real backend; fixture image Provider | `aicontent-f7-media-browser-6JE4j7` |
| `fe-f7-search-browser-acceptance.mjs` | 7 | Fixture search/download; exact rights/reference/shared consumption in real backend | `aicontent-f7-search-browser-wweM5F` |
| `fe-f7-graphic-render-browser-acceptance.mjs` | 13 | Actual explicitly configured local Chromium PNG; exact scope, explicit acceptance and manual attestation | `aicontent-f7-graphic-browser-B2hAgy` |
| `fe-f7-asr-browser-acceptance.mjs` | 4 | Actual WAV bytes / fixture transcription; explicit local accept/save provenance | `aicontent-f7-asr-browser-XRH3Ry` |
| `fe-f7-renderer-browser-acceptance.mjs` | 6 | Actual local deterministic Text v1/v2 rendering and Settings inventory | `aicontent-f7-renderer-browser-1vgVz6` |
| `fe-f7-reconciliation-ui-acceptance.mjs` | 5 | Browser route fixture only; no real backend reconciliation transaction | Console report; no artifact directory |
| `fe-f6e-browser-acceptance.mjs` | 13 | Actual backend v5 freeze/approval/authorization/local ZIP across five forms; no remote call | `aicontent-f6e-browser-evidence-U2zewo` |

Settings coverage in this batch is renderer inventory and safe Provider configuration guidance; typed Connector/operator and viewer UI coverage is retained in the earlier Batch A evidence, not claimed as freshly rerun. The five reconciliation UI gates cover empty-evidence disablement, cancelled confirmation causing zero writes, exact latest Attempt plus only local evidence hash, no execution and zero page errors. Backend reconciliation correctness remains the separately recorded regression suite, not this route fixture.

The five actual package forms are WeChat article, X thread, X single, Xiaohongshu image note and Douyin spoken script. ZIPs come from approved frozen v5 content and exact image bytes. The script also checks delayed-response isolation, independent local Master/Workflow edits, unknown reconciliation, source revision staleness, revoked rights and archived read-only behavior. Douyin remains script/estimated SRT, not a finished video or published content.

## Isolation and initial failure

- Media/renderer environment: `/tmp/aicontent-f7-media.yuVlaT/studio.db`, matching `media/`; API `127.0.0.1:15670`, UI `127.0.0.1:15671`. Guarded `apps/api/tests/fe_f7_media_acceptance_server.py` installs explicit fixture image/search/ASR implementations; it does not verify real suppliers.
- Delivery regression environment: `/tmp/aicontent-f6e-acceptance.wbUwCW/studio.db`, matching `media/`; API `127.0.0.1:18263`, UI `127.0.0.1:15663`. Real `app.main:app`, explicitly `LLM_PROVIDER=mock`, queue/object-storage disabled, fresh `seed_v1_channel_profiles` (14 profiles).
- Both fresh SQLite databases actually migrated to `f7b000000001`; this is upgrade coverage, not fresh downgrade/PostgreSQL coverage. No default/deployed database was modified.
- First Graphic run failed before renderer invocation: fixture `admin@studio.local` had auto-created `editor` role and no published exact `xiaohongshu/image_note` profile. Evidence retained in `aicontent-f7-graphic-browser-NyYFmt`. Only that exact temporary database was prepared with an administrator and a published image profile, then the entire 13-gate script passed. No product permission/profile validation was weakened. Existing Text renderer script has the same administrator prerequisite.
- Chromium, Node, Playwright and font paths were explicitly supplied to the local renderer. Real runtime fingerprinting, PNG rendering, scope verification, editor execution and revoke ran; these are not external model results. Settings' older manual Graphic/Video descriptors are not proof the separate new Graphic renderer is absent.

## Reproduction / retained boundaries

Use the existing guarded scripts, Python `.venv`, Node/Playwright/Chrome and ffmpeg/unzip. Start with new matching temporary DB/media directories and free fixed loopback ports, migrate the isolated DB, prepare the script's administrator and published profile prerequisites, then run the media scripts sequentially (Graphic temporarily changes the fixture role). Run the F6E package script against a separate fresh seeded environment. All four servers started by this batch were stopped after acceptance; databases/reports are retained for inspection.

No business code, new tests, dependency, migration file, canonical sync or archive was introduced. No paid model request, real Commons success, account upload, push, deployment or production migration. Existing WeWrite account binding/immutable upload remains unresolved; an official account-bound replacement requires a separate implementation decision and any real platform effect separate authorization.

Full backend/build results in earlier acceptance records were **not rerun or re-labelled as this batch's results**. This documentation-only batch runs OpenSpec all-strict and diff-check, with narrow evidence review; it does not close task 10.7/10.9 or establish final F7/F8 acceptance.

Final batch gates: `openspec validate --all --strict` **30/30 PASS**, `git diff --check` PASS. CLI apply progress reads **95/105**, ten remaining. Read-only independent evidence review **APPROVE**: six report files independently inspected (47 gates, zero page errors), plus the main agent's actually executed five-gate reconciliation console report. Reviewer did not rerun scripts or independently verify the no-file reconciliation execution; approval concerns evidence wording and local task 10.8 only, not the whole F7 security/provider/delivery gate.

Skills used: using-superpowers, openspec-apply-change, writing-plans, executing-plans, systematic-debugging, requesting-code-review, verification-before-completion.
