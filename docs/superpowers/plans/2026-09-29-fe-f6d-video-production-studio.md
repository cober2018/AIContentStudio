# FE-F6D Video Production Studio implementation plan

## Goal and boundary

Apply the reviewed `fe-f6d-video-production-studio` change to the local `main` checkout. Video v2 shares the existing Production Core, while Video v1 and historical Candidates remain unchanged. No new durable table/migration is planned. Real external Video/TTS/ASR execution is F7, not F6D. Do not push, deploy, run production migration, or canonical-sync/archive without separate authority.

## Baseline

- F6C 74/74, local `main@34ef5af` before F6D spec corrections.
- F6D independent SPEC review `c2c_4a78`: APPROVE after five contract corrections.
- OpenSpec strict 30/30 and `git diff --check`: PASS at spec gate.
- Active F6D tasks: 0/79 before apply.

## Steps

- [x] /// Isolated browser gate for Video v2 save/reload, v1 explicit fork, stable diff, 409 state retention, archived read-only and exact MP4/check/Candidate/Review/local package. Evidence: `docs/FE_F6D_ISOLATED_ACCEPTANCE.md`; 6.9–6.11 and 7.6–7.9 checked.
- [x] /// Video media/preview slice: exact scoped asset picker, input-bound MP4 selection, bounded authenticated byte/hash preview, honest local-structure preview and disconnected Video/TTS/ASR state. Model 8/8 and frontend build/budget PASS; browser acceptance remains separate.
- [x] /// Model-first timeline/audio/subtitle slice: RED for bounded tracks/items and media placement order, cue overlap, SRT import and render invalidation; typed controls and frontend build/budget PASS. Full backend rerun remains a final gate.
- [x] /// Video shot-source frontend slice: test exact project media selection, rights/kind/hash rejection and reference reordering; add duration/framing/transition/script-binding controls. Model 4/4 and frontend build/budget PASS.
- [x] /// Video frontend slice: RED model tests for canonical v2 draft, stable script/shot IDs, reorder and final-render invalidation; implement the pure Video model and Video-only lazy editor with explicit Master save. Model 3/3, TypeScript/Vite/bundle PASS; full backend gate running separately.
- [x] /// Commit the reviewed F6D spec/plan checkpoint locally, preserving user source packages (`a74a7d5`).
- [x] /// Record current migration head, F6C regression baseline and Video v1 compatibility; mark F6D 0.x only from evidence.
- [ ] /// Build canonical `video.master.v2` document/ref validation and exact published `video_requirements`; run focused contract checks.
- [ ] /// Add Video v2 adapter, save/read dispatch and explicit Video v1→v2 preview/commit; keep ordinary cross-schema save forbidden.
- [x] /// Video upgrade TDD: preview only verified v1 shot IDs/order and stored script plus warnings; RED for missing endpoint and forbidden implicit crossing, then implement dedicated preview. RED for missing commit, incomplete v2 input, warning mismatch, stale head/context and old render inheritance; implement explicit canonical child with source CAS/idempotency. Targeted upgrade 8 passed, full backend 994 passed/2 skipped before the final reverse-schema assertion; strict 30/30, related Ruff/diff PASS. Candidate-history hash and browser upgrade acceptance remain pending.
- [ ] /// Add exact source/render refs, input-bound manual attestation and server-only derived child provenance; verify no fake Provider writes.
- [x] /// Red: add frozen Video v2 Candidate integrity cases for canonical content, exact sole MP4 output/declaration/ref and manual input-hash binding; Green: extend Review frozen verifier without changing v1/Text/Graphic paths; rerun targeted and full backend gates. Package/browser acceptance remains a separate pending gate.
- [x] /// Red: prove shot duration can exceed timeline and a shot-linked item can exceed its shot; Green: reject both in canonical Video v2 parsing while retaining empty draft and existing shot reuse; rerun Video/F6A/F6C focused regressions.
- [x] /// Red: prove an overlay without both coordinates or with blank text can persist; Green: require explicit bounded x/y and visible text, retaining save-time exact image-kind/bytes/rights validation for cover assets.
- [x] /// Red: prove Video v2 readiness omits its script/shot/timeline preview; Green: return only canonical known structure with an explicit local-assembly label and false final-render verification claim.
- [x] /// Red: prove a placed audio/music timeline item without exact MaterialRevision persists; Green: reject it while preserving empty tracks, whole-composition voice/music declarations and bounded non-overlapping subtitle cues. Focused 34 passed, full backend 986 passed/2 skipped, strict 30/30, Ruff/diff PASS.
- [ ] /// Add Video checks/freshness, frozen Candidate integrity, Review diff/preview and byte-exact local package; regress Video v1/Text/Graphic.
- [x] /// Video check TDD: RED for missing structure/timeline and identity/profile behavior; Green by schema dispatch into append-only ContentMasterCheckRun. Empty draft stays incomplete; exact published profile is enforced/freshness-hashed; missing semantic provider and unreviewed visual/audio remain non-PASS. Focused 46 passed, full backend 998 passed/2 skipped, strict 30/30, related Ruff/diff PASS. Source/context freshness remains 5.3.
- [x] /// F6D 5.3: source-ref replacement and Brief update independently yield different new Master render-input hashes; Brief update stales old checks, live rights revocation stales rights/blocks freeze, old Master hash remains frozen. Existing services already satisfy the isolated regression; no production-code change needed. Final gates at checkpoint.
- [x] /// F6D 5.4: RED pure stable-ID diff and project-scoped route cases, GREEN bounded v2 diff service/route. Video/Graphic/Text targeted 83 passed; full backend/strict/lint/diff checkpoint pending. Candidate Review diff remains 5.5.
- [x] /// F6D 5.5: RED frozen Video v2 preview/diff with two independently valid Candidate v4 manifests, GREEN exact structured Review projection and Video document diff reuse; no whole-video similarity. Existing frozen tamper rejection and legacy reads retained; Video/Graphic/Review targeted 68 passed.
- [x] /// F6D 5.6–5.10 backend closure: isolated pinned Identity, Brief, frozen Fact Boundary, published exact profile and byte-verified MP4; draft→manual attested Master→checks→Candidate v4→Review→Approval with warning dispositions→Delivery Authorization→deterministic ZIP. Revocation, byte tamper, candidate tamper and new-Master-old-authorization fail closed; no Draft/remote call. Full backend 1004 passed/2 skipped, legacy/multimodal targeted 255 passed, strict 30/30, related Ruff and diff-check PASS.
- [x] /// F6D 3.5–3.9 trusted derived operations: RED missing endpoint and label-only faux regeneration, GREEN dedicated endpoint for concrete user-edited v2 result, source ID/hash/context/current head CAS, server-only derived_video provenance and request-bound idempotency. Shot regeneration requires a new exact project-visible source revision; Provider request is typed 503 with zero Master/media write. Full backend 1005 passed/2 skipped, strict 30/30, related Ruff/diff PASS.
- [x] /// F6D 4.1/4.2 scoped provider honesty: RED missing project-owned Video-generation/TTS/ASR GET/POST; GREEN configured/executable/verified all false, typed unavailable, no MaterialRevision/Master/reference writes, foreign project access 404. Existing Project Assets router only exposes safe unavailable hooks; F7 alone owns real provider acceptance. Targeted Video/Graphic capability tests 2 passed.
- [x] /// F6D 4.4/4.6/4.7 final-render integrity: exercise forged renderer metadata, wrong-kind render, missing bytes, changed byte hash and live rights at save/freeze; preserve F6A manual input binding to payload/context/source/profile. Reproduce v4 ZIP timestamp nondeterminism with two forced years (RED), write fixed ZIP member metadata (GREEN), verify approved media/content hashes unchanged. Full backend gate running.
- [x] /// Build typed Video-only Studio after backend closure, keep common Production/Text/Graphic bundles isolated; browser and FE-P1 graph gate passed.
- [ ] /// Isolated browser and full local gates passed; independent implementation review is unavailable in this session and remains open. Preserve 4.5 as F7-only scope, then complete reviewed F6D handoff without claiming remote publication.

## Verification rule

Each task is checked only after the corresponding service/UI behavior is observed. If implementation truly needs another durable object or migration, stop before creating it and amend/review the OpenSpec. `unknown`/unverified external capability never becomes success through a local fixture.
