import test from "node:test";
import assert from "node:assert/strict";
import { createVideoDraft, videoDraftFromMaster, videoUpgradeDraftFromPreview, updateAspectRatio, addScriptBlock, updateScriptBlock, addShot, updateShot, reorderShots, removeShot, updateVideoTitle, bindShotSource, addTrack, addTimelineItem, updateTimelineItem, removeTimelineItem, removeTrack, updateTimelineDuration, setVoice, setMusic, setCover, bindFinalRender, addSubtitleCue, updateSubtitleCue, removeSubtitleCue, importSubtitleSrt, addOverlay, removeOverlay } from "../src/product/VideoStudioModel.ts";

test("new Video Studio state has canonical v2 fields without a fabricated render", () => {
  const draft = createVideoDraft();
  assert.equal(draft.payloadSchema, "video.master.v2");
  assert.deepEqual(draft.payload.aspect_ratio, [9, 16]);
  assert.deepEqual(draft.payload.timeline, { duration_ms: 0, tracks: [] });
  assert.deepEqual(draft.payload.voice, { mode: "none" });
  assert.deepEqual(draft.payload.subtitles, { cues: [] });
  assert.equal("render_asset_ref" in draft.payload, false);
  assert.deepEqual(draft.assetRefs, []);
});

test("Video v2 reload preserves exact refs and legacy v1 stays explicit-upgrade only", () => {
  const draft = createVideoDraft();
  const master = { payload_schema: "video.master.v2", payload: draft.payload, assets: [{ material_revision_id: 7, content_hash: "a".repeat(64), role: "cover_image", slot_key: "cover", sort_order: 0, placement: { cover: "main" } }], evidence: [] };
  assert.equal(videoDraftFromMaster(master).assetRefs[0].content_hash, "a".repeat(64));
  assert.throws(() => videoDraftFromMaster({ ...master, payload_schema: "video.master.v1" }), /explicit.*upgrade/i);
});

test("script and shot edits preserve stable IDs/order and invalidate stale final render", () => {
  const start = addScriptBlock(createVideoDraft());
  const blockId = start.payload.script.blocks[0].id;
  const text = updateScriptBlock(start, blockId, "开场");
  assert.equal(text.payload.script.blocks[0].id, blockId);
  const one = addShot(text);
  const two = addShot(one);
  const [first, second] = two.payload.shots;
  assert.notEqual(first.id, second.id);
  assert.deepEqual(reorderShots(two, second.id, 0).payload.shots.map((shot) => [shot.id, shot.order]), [[second.id, 0], [first.id, 1]]);
  const rendered = { ...two, payload: { ...two.payload, render_asset_ref: { material_revision_id: 22 } }, assetRefs: [{ material_revision_id: 22, content_hash: "a".repeat(64), role: "render_output", slot_key: "final", sort_order: 0, placement: { render: "final" } }] };
  assert.equal(updateVideoTitle(rendered, "").payload.render_asset_ref.material_revision_id, 22);
  const edited = updateShot(rendered, first.id, { label: "新镜头", duration_ms: 1200 });
  assert.equal(edited.payload.shots[0].id, first.id);
  assert.equal(edited.payload.timeline.duration_ms, 2200);
  assert.equal("render_asset_ref" in edited.payload, false);
  assert.deepEqual(edited.assetRefs, []);
  assert.deepEqual(removeShot(edited, first.id).payload.shots.map((shot) => shot.order), [0]);
});

test("shot source picker binds exact project media and recalculates canonical ref order", () => {
  const start = addShot(addShot(createVideoDraft()));
  const [first, second] = start.payload.shots;
  const image = { material_revision_id: 13, content_hash: "a".repeat(64), kind: "image", public_use_allowed: true };
  const video = { material_revision_id: 14, content_hash: "b".repeat(64), kind: "video", public_use_allowed: true };
  const later = bindShotSource(start, second.id, video);
  const both = bindShotSource(later, first.id, image);
  assert.deepEqual(both.assetRefs.map((ref) => [ref.role, ref.slot_key, ref.sort_order]), [["shot_source", first.id, 0], ["shot_source", second.id, 1]]);
  assert.deepEqual(both.assetRefs[0].placement, { shot_id: first.id });
  assert.equal(both.payload.shots[0].source_material_revision_id, 13);
  const reversed = reorderShots(both, second.id, 0);
  assert.deepEqual(reversed.assetRefs.map((ref) => [ref.slot_key, ref.sort_order]), [[second.id, 0], [first.id, 1]]);
  assert.deepEqual(removeShot(both, first.id).assetRefs.map((ref) => [ref.slot_key, ref.sort_order]), [[second.id, 0]]);
  assert.deepEqual(bindShotSource(both, first.id, null).assetRefs.map((ref) => ref.slot_key), [second.id]);
  assert.throws(() => bindShotSource(start, first.id, { ...image, kind: "audio" }), /kind/i);
  assert.throws(() => bindShotSource(start, first.id, { ...image, public_use_allowed: false }), /rights/i);
});

test("bounded timeline places shot and exact audio in canonical order", () => {
  const shotDraft = addShot(createVideoDraft());
  const video = addTrack(shotDraft, "video");
  const audio = addTrack(video, "audio");
  const [videoTrack, audioTrack] = audio.payload.timeline.tracks;
  const clip = addTimelineItem(audio, videoTrack.id, { start_ms: 0, end_ms: 900, shot_id: shotDraft.payload.shots[0].id });
  const media = { material_revision_id: 42, content_hash: "c".repeat(64), kind: "audio", public_use_allowed: true };
  const placed = addTimelineItem(clip, audioTrack.id, { start_ms: 0, end_ms: 1000, asset: media });
  assert.equal(placed.payload.timeline.tracks[1].items[0].material_revision_id, 42);
  assert.deepEqual(placed.assetRefs[0].placement, { track_id: audioTrack.id, item_id: placed.payload.timeline.tracks[1].items[0].id, start_ms: 0, end_ms: 1000 });
  const updated = updateTimelineItem(placed, audioTrack.id, placed.payload.timeline.tracks[1].items[0].id, { start_ms: 100, end_ms: 900 });
  assert.deepEqual(updated.assetRefs[0].placement.start_ms, 100);
  const trimmed = updateTimelineItem(updated, audioTrack.id, updated.payload.timeline.tracks[1].items[0].id, { trim_start_ms: 0, trim_end_ms: 1000, volume: 0.5 });
  assert.equal(trimmed.assetRefs[0].placement.volume, 0.5);
  assert.equal(trimmed.assetRefs[0].placement.trim_end_ms, 1000);
  assert.throws(() => updateTimelineItem(updated, audioTrack.id, updated.payload.timeline.tracks[1].items[0].id, { trim_start_ms: 0, trim_end_ms: 100 }), /trim/i);
  assert.deepEqual(removeTimelineItem(updated, audioTrack.id, updated.payload.timeline.tracks[1].items[0].id).assetRefs, []);
  assert.equal(removeTrack(placed, audioTrack.id).payload.timeline.tracks.length, 1);
  assert.throws(() => addTimelineItem(audio, audioTrack.id, { start_ms: 0, end_ms: 1000 }), /audio.*asset/i);
  assert.throws(() => addTimelineItem(audio, audioTrack.id, { start_ms: 0, end_ms: 1000, asset: { ...media, kind: "image" } }), /kind/i);
  assert.throws(() => updateTimelineDuration(placed, 500), /duration|timing/i);
});

test("whole-video voice/music/cover refs and bounded subtitles/overlays invalidate final render", () => {
  const audio = { material_revision_id: 5, content_hash: "a".repeat(64), kind: "audio", public_use_allowed: true };
  const music = { material_revision_id: 6, content_hash: "b".repeat(64), kind: "audio", public_use_allowed: true };
  const image = { material_revision_id: 7, content_hash: "c".repeat(64), kind: "image", public_use_allowed: true };
  const start = updateTimelineDuration(createVideoDraft(), 3000);
  const voiced = setVoice(start, "recorded", audio);
  const backed = setMusic(voiced, music);
  const covered = setCover(backed, image);
  assert.deepEqual(covered.assetRefs.map((ref) => [ref.role, ref.slot_key, ref.sort_order]), [["voice_audio", "voice", 0], ["music_audio", "music", 1], ["cover_image", "cover", 2]]);
  assert.throws(() => setVoice(start, "recorded", { ...audio, kind: "video" }), /kind/i);
  assert.throws(() => setCover(start, { ...image, public_use_allowed: false }), /rights/i);
  const cue = addSubtitleCue(covered, { text: "字幕一", start_ms: 0, end_ms: 1000 });
  const cue2 = addSubtitleCue(cue, { text: "字幕二", start_ms: 1000, end_ms: 2000 });
  assert.throws(() => updateSubtitleCue(cue2, cue2.payload.subtitles.cues[1].id, { start_ms: 500 }), /overlap/i);
  assert.equal(removeSubtitleCue(cue2, cue2.payload.subtitles.cues[0].id).payload.subtitles.cues[0].order, 0);
  const overlay = addOverlay(cue, { text: "提示", start_ms: 0, end_ms: 1000, x: 0.5, y: 0.5 });
  assert.equal(removeOverlay(overlay, overlay.payload.overlays[0].id).payload.overlays.length, 0);
  assert.deepEqual(setVoice(covered, "none", null).assetRefs.map((ref) => ref.role), ["music_audio", "cover_image"]);
});

test("SRT import creates bounded ordered local cues and rejects malformed or overlapping timing", () => {
  const start = updateTimelineDuration(createVideoDraft(), 3000);
  const imported = importSubtitleSrt(start, "1\n00:00:00,000 --> 00:00:01,000\n你好\n\n2\n00:00:01,000 --> 00:00:02,000\n世界");
  assert.deepEqual(imported.payload.subtitles.cues.map((cue) => [cue.order, cue.text, cue.start_ms, cue.end_ms]), [[0, "你好", 0, 1000], [1, "世界", 1000, 2000]]);
  assert.equal("render_asset_ref" in imported.payload, false);
  assert.throws(() => importSubtitleSrt(start, "1\n00:00:00,000 --> 00:00:01,000\nA\n\n2\n00:00:00,900 --> 00:00:02,000\nB"), /overlap/i);
  assert.throws(() => importSubtitleSrt(start, "not an SRT file"), /SRT/i);
});

test("manual final render binds one exact MP4 revision without client-forged attestation", () => {
  const start = addShot(createVideoDraft());
  const video = { material_revision_id: 99, content_hash: "d".repeat(64), kind: "video", public_use_allowed: true };
  const bound = bindFinalRender(start, video);
  assert.deepEqual(bound.payload.render_asset_ref, { material_revision_id: 99 });
  assert.deepEqual(bound.assetRefs[0], { material_revision_id: 99, content_hash: "d".repeat(64), role: "render_output", slot_key: "final", sort_order: 0, placement: { render: "final" } });
  assert.equal("render_attestation" in bound.payload, false);
  assert.equal("render_asset_ref" in updateVideoTitle(bound, "新稿").payload, false);
  assert.deepEqual(bindFinalRender(bound, null).assetRefs, []);
  assert.throws(() => bindFinalRender(start, { ...video, kind: "image" }), /kind/i);
  assert.throws(() => bindFinalRender(start, { ...video, public_use_allowed: false }), /rights/i);
});

test("legacy Video preview retains provable script/shot IDs but requires explicit aspect and timing", () => {
  const draft = videoUpgradeDraftFromPreview({ title: "旧稿", script: "原脚本", shots: [{ id: "old-shot", order: 0 }] });
  assert.deepEqual(draft.payload.script.blocks.map((block) => block.text), ["原脚本"]);
  assert.deepEqual(draft.payload.shots.map((shot) => [shot.id, shot.order]), [["old-shot", 0]]);
  assert.equal("render_asset_ref" in draft.payload, false);
  assert.deepEqual(draft.assetRefs, []);
  assert.deepEqual(updateAspectRatio(draft, 16, 9).payload.aspect_ratio, [16, 9]);
  assert.throws(() => updateAspectRatio(draft, 1920, 1080), /reduced/i);
});
