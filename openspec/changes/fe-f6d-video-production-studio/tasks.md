## 0. Baseline and apply boundary

- [x] 0.1 Verify F6C 74/74, independent review approval and a clean tracked local-main baseline before F6D business-code apply.
- [x] 0.2 Review all four F6D delta specs against current canonical requirements and obtain explicit apply confirmation under the project OpenSpec rule.
- [x] 0.3 Record current API migration head, backend/frontend tests, FE-P1 bundle sizes, OpenSpec strict and Git status.
- [x] 0.4 Confirm existing revision/ref/check tables can persist v2 without a new migration; stop and amend the specification if they cannot.
- [x] 0.5 Keep F6E/F7 implementation, remote publication, push, deployment, production migration and canonical archive outside this change.

## 1. Canonical video.master.v2 document and adapter

- [x] 1.1 Define stable script-block IDs and bounded text/content structure.
- [x] 1.2 Define stable shot IDs, contiguous order, duration, source placements and bounded framing/transition tokens.
- [x] 1.3 Define stable timeline track/item IDs, allowed track kinds, start/end/trim/volume bounds and canonical order.
- [x] 1.4 Define voice mode and exact audio reference semantics.
- [x] 1.5 Define subtitle cue IDs/text/start/end, ordering and overlap rules.
- [x] 1.6 Define overlay IDs/text/placement and exact music/cover declarations.
- [x] 1.7 Reject unknown fields, non-finite values, excessive counts/durations and infrastructure paths before persistence.
- [x] 1.8 Add `video.master.v2` schema dispatch without changing Video v1 or Text/Graphic adapter behavior.
- [x] 1.9 Make new professional Video drafts use v2; no frontend editor schema becomes a backend contract.
- [x] 1.10 Extend published exact `ContentFormSpec.video_requirements` with bounded typed keys; missing rules impose no constraint, invalid/unknown or legacy/wildcard rules cannot PASS.

## 2. Exact media refs and v1 upgrade

- [x] 2.1 Map every source visual/audio/music/cover/final-render use to an exact role and placement ref.
- [x] 2.2 Validate project visibility, media kind, byte existence/hash and live public-use rights at save.
- [x] 2.3 Allow repeated MaterialRevision use in distinct placements without copying bytes or collapsing refs.
- [x] 2.4 Reject foreign, wrong-kind, revoked, hash-mismatched or missing media atomically.
- [x] 2.5 Implement v1→v2 upgrade preview that identifies provable fields and conversion warnings.
- [x] 2.6 Implement explicit append-only v1→v2 fork with expected payload/context/head CAS and idempotency.
- [x] 2.7 Keep generic save cross-schema protection and old v1/Candidate hashes unchanged.
- [x] 2.8 Validate canonical role/slot/order/placement mapping for every declared use, including repeated revisions, missing/orphan refs and the sole render output.
- [x] 2.9 Permit only the verified `video.master.v1`→`video.master.v2` upgrade pair via preview/commit; ordinary save and other schema crossings remain forbidden.

## 3. Bounded timeline and derived lineage

- [x] 3.1 Validate shot/timeline duration consistency and start/end/trim bounds.
- [x] 3.2 Validate voice/audio track placement and subtitle cue ordering/non-overlap.
- [x] 3.3 Validate overlay placement/text and cover exact image kind.
- [x] 3.4 Build deterministic local preview projection without claiming final-render verification.
- [x] 3.5 Implement explicit long-to-short child revision from exact source Master and concrete validated v2 result, not intent alone.
- [x] 3.6 Implement explicit aspect-ratio child revision from exact source Master and concrete validated v2 result, not intent alone.
- [x] 3.7 Implement shot-regeneration child boundary; unavailable Provider returns no child/media or success receipt.
- [x] 3.8 Enforce source hash/context, expected head and idempotency for all derived operations.
- [x] 3.9 Create `derived_video` source kind and provenance only in the dedicated server operation; reject forged client source/edit-summary and idempotency fingerprint mismatch.

## 4. Provider and render honesty

- [x] 4.1 Expose scoped Video-generation, TTS and ASR capability state with configured/executable/verified fields.
- [x] 4.2 Reject unverified provider-shaped requests with typed unavailable and zero MaterialRevision/Master writes.
- [x] 4.3 Ensure local UI never describes preview, manual render attestation or disconnected Provider as verified output.
- [x] 4.4 Preserve F6A manual input-bound attestation and reject forged renderer origin/version/verification fields.
- [x] 4.5 Carry real Provider execution, accepted-result bytes/license/provenance/rights and response secret-redaction requirements into F7; do not implement or mark them complete in F6D.
- [x] 4.6 Require one exact final video output whose attested input hash covers payload/context/source refs/profile.
- [x] 4.7 Reject stale, wrong-kind, missing-byte or mismatched-hash final video before Candidate freeze.

## 5. Video checks, diff, Review and package

- [x] 5.1 Add append-only Video v2 structure and timeline checks in ContentMasterCheckRun.
- [x] 5.2 Add coverage-honest Video identity and exact published video-profile checks; missing semantic provider is not PASS.
- [x] 5.3 Make profile/source/context changes invalidate current check and render-input hashes.
- [x] 5.4 Add stable-ID Master diff for script, shots, timeline, voice, cues, overlays, media and context.
- [x] 5.5 Project Review reads Video v2 from frozen Candidate v4 manifest and never invents whole-video text similarity.
- [x] 5.6 Preserve exact Candidate integrity/current Master/live-rights gates across freeze, approval and authorization.
- [x] 5.7 Build deterministic local package with approved MP4 bytes/hash, manifest and declared companions.
- [x] 5.8 Prove v2 package failure never falls back to Draft/v1 or performs remote publishing.
- [x] 5.9 Preserve v1/video and Text/Graphic Candidate/Review/package behavior.
- [x] 5.10 Extend frozen Candidate integrity dispatch to canonical Video v2 content, one exact video render-output ref/declaration/hash/MIME and ready input-bound render before Review/package.

## 6. Professional Video Studio

- [x] 6.1 Replace the normal-user Video JSON shell with typed v2 editor state and explicit local dirty/save.
- [x] 6.2 Add bounded script editor and stable shot create/delete/reorder controls.
- [x] 6.3 Add shot source asset, duration, framing and transition controls.
- [x] 6.4 Add bounded timeline tracks/items editor with timing validation feedback.
- [x] 6.5 Add voice/recorded-audio, validated subtitle cue editor/import, overlay, music and cover panels.
- [x] 6.6 Add project-visible exact media picker with kind/hash/rights/source context.
- [x] 6.7 Add truthful local preview and disconnected Video/TTS/ASR capability states.
- [x] 6.8 Add exact final-render binding and explicit manual input-bound confirmation UX.
- [x] 6.9 Add check/currentness/readiness, immutable history, v1 upgrade preview and structured diff UX.
- [x] 6.10 Keep Workflow dirty/save independent from Video Master dirty/save; archived/history views read-only.
- [x] 6.11 Preserve 409 conflict and unsaved local state when a concurrent revision wins.
- [x] 6.12 Keep Video editor/runtime in Video-only lazy closure; assert common Production/Text/Graphic do not import it.

## 7. Regression and isolated acceptance

- [x] 7.1 Regress v2 canonical IDs/hash, invalid document and atomic exact-ref failures.
- [x] 7.2 Regress v1 explicit fork, stale context/head conflicts, idempotent concrete derived revisions and unavailable Provider no-write.
- [x] 7.3 Regress unverified Provider no-write, forged renderer and stale/wrong-kind final media.
- [x] 7.4 Regress Video check freshness, frozen Candidate/Review diff and byte-exact local package.
- [x] 7.5 Regress Text v2, Graphic v2, Video v1 and historical Candidate reads without backfill.
- [x] 7.6 In isolated browser, save/reload script, shots, timeline, voice/subtitles/overlays and exact media refs.
- [x] 7.7 In isolated browser, verify v1 fork, derived child history, archived read-only and 409 stale save.
- [x] 7.8 In isolated browser, bind exact final MP4, run checks, freeze Candidate, Review, approve and download byte-matched local package.
- [x] 7.9 In isolated browser, verify rights revocation, stale render, disconnected Provider and no remote publication.
- [x] 7.10 Measure Video/common Production initial JS and enforce FE-P1/Tiptap/Graphic isolation gates.
- [x] 7.11 Regress malformed/unpublished Video profile, duplicate/missing media slots, forged derivation, forbidden upgrade pair and tampered frozen Video v2 render/content; prove no legacy fallback.

## 8. Final gates and handoff

- [x] 8.1 Run full backend suite and targeted Video/legacy regressions; record actual pass/skip/warning counts.
- [x] 8.2 Run TypeScript/Vite, frontend model checks and FE-P1 bundle/import-graph gate.
- [x] 8.3 Run `openspec validate --all --strict`, relevant lint and `git diff --check`.
- [x] 8.4 Independently review SPEC preservation, backend/rights/render and frontend/Review/package/browser evidence.
- [x] 8.5 Update README, progress/findings and acceptance report with exact limitations and verification provenance.
- [x] 8.6 Commit only owned F6D files locally; preserve user source packages and do not push, deploy, run production migration or canonical-sync/archive without separate authorization.
