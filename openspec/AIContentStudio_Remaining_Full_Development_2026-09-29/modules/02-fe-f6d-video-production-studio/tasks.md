## 0. Baseline and guardrails
- [ ] 0.1 Start after F6C gates pass.
- [ ] 0.2 Re-read current Video shell, Production Core, Material and Channel specs.
- [ ] 0.3 Record fresh backend/frontend/bundle/OpenSpec baseline.
- [ ] 0.4 Target zero new tables/migrations; stop/amend if required.
- [ ] 0.5 No push/deploy/production migration/F6E overlap.

## 1. video.master.v2 contract
- [ ] 1.1 Add exact schema adapter while preserving video v1.
- [ ] 1.2 Define stable script block contract.
- [ ] 1.3 Define stable shot contract/order/duration.
- [ ] 1.4 Define bounded source visual refs/framing/transition fields.
- [ ] 1.5 Define timeline/track/item contract.
- [ ] 1.6 Define voice contract.
- [ ] 1.7 Define subtitle cue contract.
- [ ] 1.8 Define overlay contract.
- [ ] 1.9 Define music/cover refs.
- [ ] 1.10 Enforce payload/count/duration/geometry bounds and canonicalization.
- [ ] 1.11 Reject local/remote infrastructure paths.
- [ ] 1.12 Make new Video edits default to v2.

## 2. Exact media and derived lineage
- [ ] 2.1 Require every embedded media ID in exact MasterAssetRef.
- [ ] 2.2 Enforce MaterialKind image/video/audio compatibility.
- [ ] 2.3 Enforce project visibility/hash/live rights.
- [ ] 2.4 Support repeated asset use with exact placements.
- [ ] 2.5 Preserve provider/source/prompt provenance via MaterialRevision.
- [ ] 2.6 Implement explicit v1→v2 fork.
- [ ] 2.7 Implement long→short child revision service.
- [ ] 2.8 Implement ratio-conversion child revision service.
- [ ] 2.9 Implement shot-regeneration child revision boundary.
- [ ] 2.10 Add lineage/idempotency/context tests.

## 3. Timeline/voice/subtitle logic
- [ ] 3.1 Validate shot/timeline duration consistency.
- [ ] 3.2 Validate trim/start/end bounds.
- [ ] 3.3 Validate audio/voice track placement.
- [ ] 3.4 Validate subtitle ordering/non-overlap/bounds.
- [ ] 3.5 Validate overlays and bounded text/placement.
- [ ] 3.6 Validate cover exact image.
- [ ] 3.7 Add deterministic preview projection.
- [ ] 3.8 Add structure/timeline tests.

## 4. Provider hooks
- [ ] 4.1 Add provider-neutral video generation request boundary.
- [ ] 4.2 Add provider-neutral TTS request boundary.
- [ ] 4.3 Add provider-neutral ASR/subtitle request boundary.
- [ ] 4.4 Add truthful capability unavailable state.
- [ ] 4.5 Materialize accepted output as exact MaterialRevision.
- [ ] 4.6 Never mutate Master automatically on provider completion.
- [ ] 4.7 Explicit user accept + Master save creates revision.
- [ ] 4.8 Add mock/unavailable/provenance tests.
- [ ] 4.9 Leave real provider verification to F7.

## 5. Video checks/diff/render
- [ ] 5.1 Add video_structure.
- [ ] 5.2 Add video_timeline.
- [ ] 5.3 Add video_identity.
- [ ] 5.4 Add exact video_platform checks.
- [ ] 5.5 Preserve evidence/rights/render gates.
- [ ] 5.6 Add structured diff for script/shots/timeline/voice/subtitles/overlays/assets.
- [ ] 5.7 Add v1↔v2 bounded diff.
- [ ] 5.8 Bind final video render to exact inputs.
- [ ] 5.9 Reject stale/wrong-kind/mismatched bytes.
- [ ] 5.10 Package exact final video + declared companion assets.

## 6. Professional Video Studio frontend
- [ ] 6.1 Replace JSON shell with typed Video Studio.
- [ ] 6.2 Add script editor.
- [ ] 6.3 Add shot list/create/delete/reorder.
- [ ] 6.4 Add shot asset/framing/duration editor.
- [ ] 6.5 Add bounded timeline with track/item editing.
- [ ] 6.6 Add voice/TTS panel.
- [ ] 6.7 Add subtitle editor/import/ASR panel.
- [ ] 6.8 Add overlay/music/cover controls.
- [ ] 6.9 Add preview player from current local state/known assets.
- [ ] 6.10 Add provider actions with explicit accept.
- [ ] 6.11 Add revision history/diff/check/readiness.
- [ ] 6.12 Preserve Workflow dirty/save independence.
- [ ] 6.13 Historical/archived read-only.

## 7. Candidate/Review/browser/final gates
- [ ] 7.1 Save/reload v2 script/shots/timeline.
- [ ] 7.2 Verify TTS/ASR/provider output does not auto-save Master.
- [ ] 7.3 Verify rights revocation/stale render.
- [ ] 7.4 Bind exact final MP4 render.
- [ ] 7.5 Freeze Candidate and inspect structured Review.
- [ ] 7.6 Approve and download exact video package.
- [ ] 7.7 Verify Text/Graphic/v1 video regressions.
- [ ] 7.8 Run build/bundle isolation.
- [ ] 7.9 Run backend/OpenSpec/Ruff/diff full gates.
- [ ] 7.10 Complete browser acceptance and independent reviews.
- [ ] 7.11 Record limitations and local implementation commit.
- [ ] 7.12 Do not canonical-sync/archive without explicit authorization.
