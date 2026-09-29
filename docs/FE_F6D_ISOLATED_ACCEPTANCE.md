# FE-F6D Video Production Studio — isolated acceptance

Date: 2026-09-29. Scope: local F6D change on `main`, before independent implementation review or archive.

## Isolation and provenance

- Dedicated temporary SQLite database: `/tmp/aicontent-f6d-acceptance.vwFhgL/studio.db`; Alembic upgraded only this fixture to `f6a000000001`.
- Dedicated API `127.0.0.1:18262` and Vite `127.0.0.1:15662`; existing user API, production database and remote publishers were not touched. Media storage is **not isolated**: the current backend writes content-addressed test uploads under `apps/api/app/media/material/`. Existing same-hash files are not overwritten; generated files were left in place because another local database may reference them.
- Browser script: `apps/web/scripts/fe-f6d-browser-acceptance.mjs`; it checks the exact isolated URLs, a `/tmp/aicontent-f6d-acceptance.*` database and `F6D_ISOLATED_ACCEPTANCE=yes` before any fixture write.
- Latest successful browser evidence: `/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f6d-browser-evidence-swdwF7/report.json` (local, temporary). Failed intermediate runs are not counted as acceptance.

## Browser gates observed

1. Video v2 typed script, shot, timeline, recorded MP3, subtitle and overlay saved atomically with exact `shot_source`, `timeline_media`, `voice_audio` MaterialRevision refs; page reload preserved the document.
2. Concurrent stale save returned HTTP 409 and the losing tab kept its unsaved title.
3. Bound MP4 was fetched with authorization, MIME/byte limit and SHA-256 checked before local playback. This alone did not create input-bound render proof; changing the Master input removed the old render binding and disabled freeze.
4. Rebinding the exact MP4, saving and explicitly confirming current input produced a new immutable revision. Master checks then enabled Candidate v4 freeze.
5. Review played the frozen MP4. Warning dispositions were entered explicitly before Content Approval, followed by manual local-package authorization and ZIP download.
6. Every MP4 ZIP member, including repeated placement members and final render, matched the exact MaterialRevision SHA-256. Manifest declared schema 4 and `remote_call=false`.
7. Historical Video v1 remained read-only. Preview showed non-inferable fields; explicit confirmation created a v2 child preserving old script and shot ID, while the v1 payload hash stayed unchanged. New v2 revision diff and a concrete aspect-ratio `derived_video` child were visible in history.
8. Public-use revocation of the exact MP4 blocked a previously approved package download. Archiving the isolated project kept history readable but disabled Master save and checks.
9. Video-generation, TTS and ASR remained marked unverified/unexecutable; there was no remote publication or synthetic provider success. Browser page errors: none.

## Fresh local gates

- Backend: `1006 passed, 2 skipped, 5 warnings` from `apps/api/.venv/bin/pytest -q` in `apps/api`.
- Targeted Video/Graphic/Text/F6A/Review regression: `229 passed, 1 warning`.
- Frontend: TypeScript/Vite build PASS; Video model 9/9; FE-P1 route/import graph PASS. `/projects` 224.75 kB raw / 72.89 kB gzip; common Production 276.96 kB raw / 88.24 kB gzip. TipTap remains Text-only lazy.
- OpenSpec: `openspec validate --all --strict` 30/30 PASS.
- Ruff: scoped changed backend files PASS. `git diff --check` PASS.

## 2026-09-29 media-isolated rerun

- Fresh final fixture database: `/tmp/aicontent-f6d-acceptance.kubyUY/studio.db`; API media root: `/tmp/aicontent-f6d-acceptance.kubyUY/media`. The first rerun (`7qLIAl`) exposed a browser assertion using a file_path absent from the public API; after switching the assertion to content hash, the final browser run used a new empty fixture to rule out reuse of prior same-hash bytes. Only these temporary databases received Alembic upgrades; no production migration.
- `AI_STUDIO_MEDIA_ROOT` is an explicit absolute-path override. The browser script now requires the media root to be the `media` sibling of its guarded fixture database, then verifies uploaded MP4 and MP3 bytes under that root against each exact MaterialRevision hash. The previous shared-media run above remains historical evidence, not the isolation claim for this rerun.
- Latest successful report: `/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f6d-browser-evidence-hDIR9b/report.json`. All 11 browser gates passed from a fresh empty media root; no page errors. API and Vite test processes were stopped; temporary fixture and evidence files were retained for inspection.
- Focused backend regression: 55 passed; full backend: 1007 passed, 2 skipped, 5 warnings. TypeScript/Vite and FE-P1 bundle check passed; OpenSpec strict 30/30 passed.

## 2026-09-29 WAV audio regression rerun

- Root cause: upload trusted the declared `audio/wav`, while Video v2 save re-sniffed bytes with no declared type and returned `application/octet-stream` for RIFF/WAVE. The shared sniffer now distinguishes RIFF/WAVE from RIFF/WEBP and unknown RIFF; Video v2 retains its exact byte/hash, project-reference, kind and live-rights gates. The v4 local package names an approved WAV companion `.wav` rather than `.bin`.
- A fresh isolated database `/tmp/aicontent-f6d-acceptance.jx9blb/studio.db` and sibling media directory were used, not the earlier fixture. Browser evidence: `/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f6d-browser-evidence-4RGKn5/report.json`; all 11 gates passed, including recorded WAV → exact Master ref → Candidate v4 → Review/Approval → byte-matched WAV/MP4 local ZIP. Page errors: none. API/Vite test processes were stopped; temporary evidence retained.
- Test-first proof: RIFF/WAVE sniff and Video v2 save both failed before the fix; package integration lacked the `.wav` member before the package mapping fix. Targeted tests then passed. No new table or migration, remote Provider call, publisher call or production write.
- Fresh final gates: backend 1009 passed / 2 skipped / 5 existing warnings; TypeScript/Vite and FE-P1 budget PASS; OpenSpec strict 30/30; scoped Ruff, JS syntax and `git diff --check` PASS.

## Honest limits

- Real external Video/TTS/ASR execution, accepted bytes/license/provenance/rights, response redaction and verified publication are F7, not demonstrated here.
- The initial browser run used ID3 MP3; the later WAV rerun above closes the recorded-audio limitation. External TTS/ASR remains unverified.
- The previous independent F6D SPEC review is on record, but no independent implementation verdict has been obtained this turn: the dedicated ChatGPT browser-control tool required by the existing review skill is unavailable. Local review and passing tests must not be labeled independent approval.
- Source package/ZIP files under `openspec/` remain untouched and untracked. Canonical spec sync, archive, push, deployment and production migration have not occurred.
