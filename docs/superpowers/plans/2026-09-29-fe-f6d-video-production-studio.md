# FE-F6D Video Production Studio implementation plan

## Goal and boundary

Apply the reviewed `fe-f6d-video-production-studio` change to the local `main` checkout. Video v2 shares the existing Production Core, while Video v1 and historical Candidates remain unchanged. No new durable table/migration is planned. Real external Video/TTS/ASR execution is F7, not F6D. Do not push, deploy, run production migration, or canonical-sync/archive without separate authority.

## Baseline

- F6C 74/74, local `main@34ef5af` before F6D spec corrections.
- F6D independent SPEC review `c2c_4a78`: APPROVE after five contract corrections.
- OpenSpec strict 30/30 and `git diff --check`: PASS at spec gate.
- Active F6D tasks: 0/79 before apply.

## Steps

- [x] /// Commit the reviewed F6D spec/plan checkpoint locally, preserving user source packages (`a74a7d5`).
- [x] /// Record current migration head, F6C regression baseline and Video v1 compatibility; mark F6D 0.x only from evidence.
- [ ] /// Build canonical `video.master.v2` document/ref validation and exact published `video_requirements`; run focused contract checks.
- [ ] /// Add Video v2 adapter, save/read dispatch and explicit Video v1→v2 preview/commit; keep ordinary cross-schema save forbidden.
- [ ] /// Add exact source/render refs, input-bound manual attestation and server-only derived child provenance; verify no fake Provider writes.
- [x] /// Red: add frozen Video v2 Candidate integrity cases for canonical content, exact sole MP4 output/declaration/ref and manual input-hash binding; Green: extend Review frozen verifier without changing v1/Text/Graphic paths; rerun targeted and full backend gates. Package/browser acceptance remains a separate pending gate.
- [x] /// Red: prove shot duration can exceed timeline and a shot-linked item can exceed its shot; Green: reject both in canonical Video v2 parsing while retaining empty draft and existing shot reuse; rerun Video/F6A/F6C focused regressions.
- [ ] /// Add Video checks/freshness, frozen Candidate integrity, Review diff/preview and byte-exact local package; regress Video v1/Text/Graphic.
- [ ] /// Build typed Video-only Studio after backend closure, keep common Production/Text/Graphic bundles isolated.
- [ ] /// Run isolated browser Video flow, full backend/frontend/FE-P1/OpenSpec/lint/diff gates and independent reviews; close only proven tasks and commit locally.

## Verification rule

Each task is checked only after the corresponding service/UI behavior is observed. If implementation truly needs another durable object or migration, stop before creating it and amend/review the OpenSpec. `unknown`/unverified external capability never becomes success through a local fixture.
