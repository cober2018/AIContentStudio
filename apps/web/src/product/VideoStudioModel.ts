export type VideoScriptBlock = { id: string; order: number; text: string };
export type VideoShot = { id: string; order: number; label: string; duration_ms: number; purpose?: string; script_block_id?: string; source_material_revision_id?: number; framing?: "wide" | "medium" | "close" | "custom"; transition?: "cut" | "fade" | "dissolve" };
export type VideoTimelineItem = { id: string; order: number; start_ms: number; end_ms: number; shot_id?: string; material_revision_id?: number; trim_start_ms?: number; trim_end_ms?: number; volume?: number };
export type VideoTrack = { id: string; order: number; kind: "video" | "audio" | "subtitle" | "overlay" | "music"; items: VideoTimelineItem[] };
export type VideoCue = { id: string; order: number; text: string; start_ms: number; end_ms: number };
export type VideoOverlay = { id: string; order: number; text: string; start_ms: number; end_ms: number; x: number; y: number };
export type VideoPayload = {
  title: string; aspect_ratio: [number, number]; script: { blocks: VideoScriptBlock[] }; shots: VideoShot[];
  timeline: { duration_ms: number; tracks: VideoTrack[] }; voice: { mode: "none" | "recorded" | "tts"; material_revision_id?: number };
  subtitles: { cues: VideoCue[] }; overlays: VideoOverlay[]; music: { material_revision_id?: number }; cover: { material_revision_id?: number };
  render_asset_ref?: { material_revision_id: number };
};
export type VideoAssetRef = { material_revision_id: number; content_hash: string; role: string; slot_key?: string; sort_order?: number; placement?: Record<string, unknown> };
export type VideoEvidenceRef = { fact_pack_item_id: number; snapshot_checksum: string; role?: string; sort_order?: number; locator: Record<string, unknown> };
export type VideoDraft = { payloadSchema: "video.master.v2"; payload: VideoPayload; assetRefs: VideoAssetRef[]; evidenceRefs: VideoEvidenceRef[]; asrReceiptId?: string };
export type ExactVideoAsset = { material_revision_id: number; content_hash: string; kind: string; public_use_allowed: boolean; model_use_allowed: boolean };

const MAX_DURATION = 8 * 60 * 60 * 1000;
function reordered<T extends { order: number }>(rows: T[]): T[] { return rows.map((row, order) => ({ ...row, order })); }
function orderedAssetRefs(payload: VideoPayload, refs: VideoAssetRef[]): VideoAssetRef[] {
  const ordered: VideoAssetRef[] = [];
  function add(role: string, slot_key: string, material_revision_id: number, placement: Record<string, unknown>) {
    const ref = refs.find((row) => row.role === role && row.slot_key === slot_key && row.material_revision_id === material_revision_id && (role !== "timeline_media" || row.placement?.track_id === placement.track_id));
    if (!ref) throw new Error("Exact video media reference missing");
    ordered.push({ ...ref, sort_order: ordered.length, placement });
  }
  for (const shot of payload.shots) if (shot.source_material_revision_id) add("shot_source", shot.id, shot.source_material_revision_id, { shot_id: shot.id });
  for (const track of payload.timeline.tracks) for (const item of track.items) if (item.material_revision_id) {
    const placement: Record<string, unknown> = { track_id: track.id, item_id: item.id, start_ms: item.start_ms, end_ms: item.end_ms };
    for (const field of ["trim_start_ms", "trim_end_ms", "volume"] as const) if (item[field] !== undefined) placement[field] = item[field];
    add("timeline_media", item.id, item.material_revision_id, placement);
  }
  for (const [field, role] of [["voice", "voice_audio"], ["music", "music_audio"], ["cover", "cover_image"]] as const) {
    const revision = payload[field].material_revision_id;
    if (revision) add(role, field, revision, { [field]: "main" });
  }
  if (payload.render_asset_ref) add("render_output", "final", payload.render_asset_ref.material_revision_id, { render: "final" });
  return ordered;
}
function changed(draft: VideoDraft, payload: VideoPayload, assetRefs = draft.assetRefs): VideoDraft {
  const next = { ...payload };
  delete next.render_asset_ref;
  return { ...draft, payload: next, assetRefs: assetRefs.filter((ref) => ref.role !== "render_output") };
}
function duration(shots: VideoShot[], current: number): number {
  const minimum = shots.reduce((sum, shot) => sum + shot.duration_ms, 0);
  if (minimum > MAX_DURATION) throw new Error("Video duration limit reached");
  return Math.max(current, minimum);
}

export function createVideoDraft(): VideoDraft {
  return { payloadSchema: "video.master.v2", payload: { title: "", aspect_ratio: [9, 16], script: { blocks: [] }, shots: [], timeline: { duration_ms: 0, tracks: [] }, voice: { mode: "none" }, subtitles: { cues: [] }, overlays: [], music: {}, cover: {} }, assetRefs: [], evidenceRefs: [] };
}

export function acceptAsrCues(draft: VideoDraft, receiptId: string, cues: VideoCue[]): VideoDraft {
  if (!/^[0-9a-f]{32}$/.test(receiptId) || cues.length < 1 || cues.length > 1000) throw new Error("ASR receipt/cues invalid");
  let end = 0;
  for (const [order, cue] of cues.entries()) {
    if (cue.order !== order || !Number.isInteger(cue.start_ms) || !Number.isInteger(cue.end_ms) || cue.start_ms < end || cue.end_ms <= cue.start_ms || cue.end_ms > draft.payload.timeline.duration_ms || !cue.text.trim() || cue.text.length > 500) throw new Error("ASR cues do not fit current timeline");
    end = cue.end_ms;
  }
  return { ...changed(draft, { ...draft.payload, subtitles: { cues: structuredClone(cues) } }), asrReceiptId: receiptId };
}

export function videoUpgradeDraftFromPreview(fields: { title: string | null; script: string | null; shots: { id: string; order: number }[] }): VideoDraft {
  const draft = createVideoDraft();
  const script = fields.script || "";
  if (script.length > 2_000_000 || fields.shots.length > 300 || fields.title && fields.title.length > 500) throw new Error("Legacy Video exceeds v2 conversion limits");
  const blocks = Array.from({ length: Math.ceil(script.length / 10_000) }, (_, index) => ({ id: `legacy-script-${index + 1}`, order: index, text: script.slice(index * 10_000, (index + 1) * 10_000) }));
  const shots = fields.shots.map((shot) => ({ id: shot.id, order: shot.order, label: "", duration_ms: 1000 }));
  return { ...draft, payload: { ...draft.payload, title: fields.title || "", script: { blocks }, shots, timeline: { duration_ms: shots.length * 1000, tracks: [] } } };
}

export function updateAspectRatio(draft: VideoDraft, width: number, height: number): VideoDraft {
  if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1 || width > 8192 || height > 8192) throw new Error("Video aspect ratio invalid");
  let a = width; let b = height;
  while (b) [a, b] = [b, a % b];
  if (a !== 1) throw new Error("Video aspect ratio must be reduced");
  if (draft.payload.aspect_ratio[0] === width && draft.payload.aspect_ratio[1] === height) return draft;
  return changed(draft, { ...draft.payload, aspect_ratio: [width, height] });
}

export function videoDraftFromMaster(master: { payload_schema: string; payload: Record<string, unknown>; assets?: Record<string, unknown>[]; evidence?: Record<string, unknown>[] }): VideoDraft {
  if (master.payload_schema !== "video.master.v2") throw new Error("Video Master v1 requires explicit upgrade before editing");
  if (!Array.isArray((master.payload.script as { blocks?: unknown[] } | undefined)?.blocks) || !Array.isArray(master.payload.shots)) throw new Error("Unsupported Video document");
  return {
    payloadSchema: "video.master.v2", payload: structuredClone(master.payload) as VideoPayload,
    assetRefs: (master.assets || []).map((row) => ({ material_revision_id: Number(row.material_revision_id), content_hash: String(row.content_hash), role: String(row.role), ...(row.slot_key != null ? { slot_key: String(row.slot_key) } : {}), ...(row.sort_order != null ? { sort_order: Number(row.sort_order) } : {}), ...(row.placement != null ? { placement: row.placement as Record<string, unknown> } : {}) })),
    evidenceRefs: (master.evidence || []).map((row) => ({ fact_pack_item_id: Number(row.fact_pack_item_id), snapshot_checksum: String(row.snapshot_checksum), ...(row.role != null ? { role: String(row.role) } : {}), ...(row.sort_order != null ? { sort_order: Number(row.sort_order) } : {}), locator: row.locator as Record<string, unknown> })),
  };
}

export function updateVideoTitle(draft: VideoDraft, title: string): VideoDraft {
  if (title.length > 500 || title.includes("\0")) throw new Error("Video title invalid");
  return title === draft.payload.title ? draft : changed(draft, { ...draft.payload, title });
}

export function addScriptBlock(draft: VideoDraft): VideoDraft {
  const blocks = draft.payload.script.blocks;
  if (blocks.length >= 200) throw new Error("Script block limit reached");
  return changed(draft, { ...draft.payload, script: { blocks: [...blocks, { id: crypto.randomUUID(), order: blocks.length, text: "" }] } });
}

export function updateScriptBlock(draft: VideoDraft, id: string, text: string): VideoDraft {
  if (text.length > 10_000 || text.includes("\0")) throw new Error("Script text invalid");
  const block = draft.payload.script.blocks.find((row) => row.id === id);
  if (!block) throw new Error("Script block not found");
  if (block.text === text) return draft;
  return changed(draft, { ...draft.payload, script: { blocks: draft.payload.script.blocks.map((row) => row.id === id ? { ...row, text } : row) } });
}

export function addShot(draft: VideoDraft): VideoDraft {
  if (draft.payload.shots.length >= 300) throw new Error("Shot limit reached");
  const shots = [...draft.payload.shots, { id: crypto.randomUUID(), order: draft.payload.shots.length, label: "", duration_ms: 1000 }];
  return changed(draft, { ...draft.payload, shots, timeline: { ...draft.payload.timeline, duration_ms: duration(shots, draft.payload.timeline.duration_ms) } });
}

export function updateShot(draft: VideoDraft, id: string, patch: Partial<Pick<VideoShot, "label" | "purpose" | "duration_ms" | "script_block_id" | "framing" | "transition">>): VideoDraft {
  const old = draft.payload.shots.find((shot) => shot.id === id);
  if (!old) throw new Error("Shot not found");
  const shot = { ...old, ...patch };
  if (!Number.isInteger(shot.duration_ms) || shot.duration_ms < 1 || shot.duration_ms > MAX_DURATION || shot.label.length > 200 || (shot.purpose?.length || 0) > 1000) throw new Error("Shot fields invalid");
  if (shot.framing && !["wide", "medium", "close", "custom"].includes(shot.framing)) throw new Error("Shot framing invalid");
  if (shot.transition && !["cut", "fade", "dissolve"].includes(shot.transition)) throw new Error("Shot transition invalid");
  if (shot.script_block_id && !draft.payload.script.blocks.some((block) => block.id === shot.script_block_id)) throw new Error("Script block reference missing");
  if (JSON.stringify(shot) === JSON.stringify(old)) return draft;
  const shots = draft.payload.shots.map((row) => row.id === id ? shot : row);
  return changed(draft, { ...draft.payload, shots, timeline: { ...draft.payload.timeline, duration_ms: duration(shots, draft.payload.timeline.duration_ms) } });
}

export function reorderShots(draft: VideoDraft, id: string, toIndex: number): VideoDraft {
  const shots = [...draft.payload.shots];
  const fromIndex = shots.findIndex((shot) => shot.id === id);
  if (fromIndex < 0 || !Number.isInteger(toIndex) || toIndex < 0 || toIndex >= shots.length) throw new Error("Shot order invalid");
  if (fromIndex === toIndex) return draft;
  shots.splice(toIndex, 0, shots.splice(fromIndex, 1)[0]);
  const ordered = reordered(shots);
  const payload = { ...draft.payload, shots: ordered };
  return changed(draft, payload, orderedAssetRefs(payload, draft.assetRefs));
}

export function removeShot(draft: VideoDraft, id: string): VideoDraft {
  if (!draft.payload.shots.some((shot) => shot.id === id)) throw new Error("Shot not found");
  if (draft.payload.timeline.tracks.some((track) => track.items.some((item) => item.shot_id === id))) throw new Error("Remove timeline placement before deleting shot");
  const shots = reordered(draft.payload.shots.filter((shot) => shot.id !== id));
  const payload = { ...draft.payload, shots };
  return changed(draft, payload, orderedAssetRefs(payload, draft.assetRefs));
}

export function bindShotSource(draft: VideoDraft, id: string, asset: ExactVideoAsset | null): VideoDraft {
  const old = draft.payload.shots.find((shot) => shot.id === id);
  if (!old) throw new Error("Shot not found");
  if (asset && !asset.model_use_allowed && !asset.public_use_allowed) throw new Error("Asset rights allow neither model nor public use");
  if (asset && !["image", "video"].includes(asset.kind)) throw new Error("Shot source kind must be image or video");
  if (asset && (!Number.isInteger(asset.material_revision_id) || asset.material_revision_id < 1 || !/^[0-9a-f]{64}$/.test(asset.content_hash))) throw new Error("Exact asset revision/hash invalid");
  const current = draft.assetRefs.find((ref) => ref.role === "shot_source" && ref.slot_key === id);
  if (asset ? current?.material_revision_id === asset.material_revision_id && current.content_hash === asset.content_hash : !current) return draft;
  const shots = draft.payload.shots.map((shot) => {
    if (shot.id !== id) return shot;
    const next = { ...shot };
    if (asset) next.source_material_revision_id = asset.material_revision_id;
    else delete next.source_material_revision_id;
    return next;
  });
  const payload = { ...draft.payload, shots };
  const refs = orderedAssetRefs(payload, [...draft.assetRefs.filter((ref) => !(ref.role === "shot_source" && ref.slot_key === id)), ...(asset ? [{ material_revision_id: asset.material_revision_id, content_hash: asset.content_hash, role: "shot_source", slot_key: id, placement: { shot_id: id } }] : [])]);
  return changed(draft, payload, refs);
}

export function updateTimelineDuration(draft: VideoDraft, duration_ms: number): VideoDraft {
  if (!Number.isInteger(duration_ms) || duration_ms < 0 || duration_ms > MAX_DURATION) throw new Error("Timeline duration invalid");
  if (draft.payload.shots.some((shot) => shot.duration_ms > duration_ms) || draft.payload.timeline.tracks.some((track) => track.items.some((item) => item.end_ms > duration_ms)) || draft.payload.subtitles.cues.some((cue) => cue.end_ms > duration_ms) || draft.payload.overlays.some((overlay) => overlay.end_ms > duration_ms)) throw new Error("Timeline duration shorter than existing content timing");
  if (duration_ms === draft.payload.timeline.duration_ms) return draft;
  return changed(draft, { ...draft.payload, timeline: { ...draft.payload.timeline, duration_ms } });
}

export function addTrack(draft: VideoDraft, kind: VideoTrack["kind"]): VideoDraft {
  if (!["video", "audio", "subtitle", "overlay", "music"].includes(kind)) throw new Error("Track kind invalid");
  if (draft.payload.timeline.tracks.length >= 16) throw new Error("Track limit reached");
  const tracks = [...draft.payload.timeline.tracks, { id: crypto.randomUUID(), order: draft.payload.timeline.tracks.length, kind, items: [] }];
  return changed(draft, { ...draft.payload, timeline: { ...draft.payload.timeline, tracks } });
}

export function removeTrack(draft: VideoDraft, trackId: string): VideoDraft {
  if (!draft.payload.timeline.tracks.some((track) => track.id === trackId)) throw new Error("Track not found");
  const tracks = reordered(draft.payload.timeline.tracks.filter((track) => track.id !== trackId));
  const payload = { ...draft.payload, timeline: { ...draft.payload.timeline, tracks } };
  return changed(draft, payload, orderedAssetRefs(payload, draft.assetRefs));
}

function validTiming(start_ms: number, end_ms: number, total: number): void {
  if (!Number.isInteger(start_ms) || !Number.isInteger(end_ms) || start_ms < 0 || end_ms <= start_ms || end_ms > total) throw new Error("Timeline item timing invalid");
}

export function addTimelineItem(draft: VideoDraft, trackId: string, input: { start_ms: number; end_ms: number; shot_id?: string; asset?: ExactVideoAsset }): VideoDraft {
  const track = draft.payload.timeline.tracks.find((row) => row.id === trackId);
  if (!track) throw new Error("Track not found");
  if (track.items.length >= 300) throw new Error("Timeline item limit reached");
  validTiming(input.start_ms, input.end_ms, draft.payload.timeline.duration_ms);
  if (input.shot_id) {
    const shot = draft.payload.shots.find((row) => row.id === input.shot_id);
    if (!shot || track.kind !== "video" || input.end_ms - input.start_ms > shot.duration_ms) throw new Error("Timeline shot placement invalid");
  }
  if (track.kind === "audio" || track.kind === "music") {
    if (!input.asset) throw new Error("Audio track requires exact asset");
  }
  if (input.asset) {
    if (!input.asset.model_use_allowed && !input.asset.public_use_allowed) throw new Error("Asset rights allow neither model nor public use");
    const kinds = track.kind === "video" ? ["image", "video"] : track.kind === "audio" || track.kind === "music" ? ["audio"] : [];
    if (!kinds.includes(input.asset.kind)) throw new Error("Timeline media kind invalid");
    if (!Number.isInteger(input.asset.material_revision_id) || input.asset.material_revision_id < 1 || !/^[0-9a-f]{64}$/.test(input.asset.content_hash)) throw new Error("Exact timeline media revision/hash invalid");
  }
  if (track.kind === "video" && !input.shot_id && !input.asset) throw new Error("Video placement needs shot or exact asset");
  const item: VideoTimelineItem = { id: crypto.randomUUID(), order: track.items.length, start_ms: input.start_ms, end_ms: input.end_ms, ...(input.shot_id ? { shot_id: input.shot_id } : {}), ...(input.asset ? { material_revision_id: input.asset.material_revision_id } : {}) };
  const tracks = draft.payload.timeline.tracks.map((row) => row.id === trackId ? { ...row, items: [...row.items, item] } : row);
  const payload = { ...draft.payload, timeline: { ...draft.payload.timeline, tracks } };
  const refs = input.asset ? [...draft.assetRefs, { material_revision_id: input.asset.material_revision_id, content_hash: input.asset.content_hash, role: "timeline_media", slot_key: item.id, placement: { track_id: trackId, item_id: item.id, start_ms: item.start_ms, end_ms: item.end_ms } }] : draft.assetRefs;
  return changed(draft, payload, orderedAssetRefs(payload, refs));
}

export function updateTimelineItem(draft: VideoDraft, trackId: string, itemId: string, patch: Partial<Pick<VideoTimelineItem, "start_ms" | "end_ms" | "trim_start_ms" | "trim_end_ms" | "volume">>): VideoDraft {
  const track = draft.payload.timeline.tracks.find((row) => row.id === trackId);
  const old = track?.items.find((item) => item.id === itemId);
  if (!track || !old) throw new Error("Timeline item not found");
  const item = { ...old, ...patch };
  validTiming(item.start_ms, item.end_ms, draft.payload.timeline.duration_ms);
  if (item.shot_id) {
    const shot = draft.payload.shots.find((row) => row.id === item.shot_id);
    if (!shot || item.end_ms - item.start_ms > shot.duration_ms) throw new Error("Timeline shot duration invalid");
  }
  if (item.trim_start_ms !== undefined || item.trim_end_ms !== undefined) {
    if (!Number.isInteger(item.trim_start_ms) || !Number.isInteger(item.trim_end_ms) || item.trim_start_ms! < 0 || item.trim_end_ms! > MAX_DURATION || item.trim_end_ms! - item.trim_start_ms! < item.end_ms - item.start_ms) throw new Error("Timeline trim invalid");
  }
  if (item.volume !== undefined && (!Number.isFinite(item.volume) || item.volume < 0 || item.volume > 2)) throw new Error("Timeline volume invalid");
  if (JSON.stringify(item) === JSON.stringify(old)) return draft;
  const tracks = draft.payload.timeline.tracks.map((row) => row.id === trackId ? { ...row, items: row.items.map((current) => current.id === itemId ? item : current) } : row);
  const payload = { ...draft.payload, timeline: { ...draft.payload.timeline, tracks } };
  return changed(draft, payload, orderedAssetRefs(payload, draft.assetRefs));
}

export function removeTimelineItem(draft: VideoDraft, trackId: string, itemId: string): VideoDraft {
  const track = draft.payload.timeline.tracks.find((row) => row.id === trackId);
  if (!track || !track.items.some((item) => item.id === itemId)) throw new Error("Timeline item not found");
  const tracks = draft.payload.timeline.tracks.map((row) => row.id === trackId ? { ...row, items: reordered(row.items.filter((item) => item.id !== itemId)) } : row);
  const payload = { ...draft.payload, timeline: { ...draft.payload.timeline, tracks } };
  return changed(draft, payload, orderedAssetRefs(payload, draft.assetRefs));
}

function validateMedia(asset: ExactVideoAsset | null, kind: string, label: string, requirePublic = false): void {
  if (!asset) return;
  if (!asset.model_use_allowed && !asset.public_use_allowed) throw new Error(`${label} rights allow neither model nor public use`);
  if (requirePublic && !asset.public_use_allowed) throw new Error(`${label} rights do not allow public use`);
  if (asset.kind !== kind) throw new Error(`${label} kind must be ${kind}`);
  if (!Number.isInteger(asset.material_revision_id) || asset.material_revision_id < 1 || !/^[0-9a-f]{64}$/.test(asset.content_hash)) throw new Error(`${label} exact revision/hash invalid`);
}

function replaceWholeMedia(draft: VideoDraft, payload: VideoPayload, role: string, slot: string, asset: ExactVideoAsset | null): VideoDraft {
  const refs = draft.assetRefs.filter((ref) => ref.role !== role);
  if (asset) refs.push({ material_revision_id: asset.material_revision_id, content_hash: asset.content_hash, role, slot_key: slot, placement: { [slot]: "main" } });
  return changed(draft, payload, orderedAssetRefs(payload, refs));
}

export function setVoice(draft: VideoDraft, mode: VideoPayload["voice"]["mode"], asset: ExactVideoAsset | null): VideoDraft {
  if (!["none", "recorded", "tts"].includes(mode) || (mode === "none") !== (asset === null)) throw new Error("Voice mode and exact audio binding invalid");
  validateMedia(asset, "audio", "Voice");
  if (draft.payload.voice.mode === mode && draft.payload.voice.material_revision_id === asset?.material_revision_id && (!asset || draft.assetRefs.find((ref) => ref.role === "voice_audio")?.content_hash === asset.content_hash)) return draft;
  const voice: VideoPayload["voice"] = asset ? { mode, material_revision_id: asset.material_revision_id } : { mode: "none" };
  return replaceWholeMedia(draft, { ...draft.payload, voice }, "voice_audio", "voice", asset);
}

export function setMusic(draft: VideoDraft, asset: ExactVideoAsset | null): VideoDraft {
  validateMedia(asset, "audio", "Music");
  if (draft.payload.music.material_revision_id === asset?.material_revision_id && (!asset || draft.assetRefs.find((ref) => ref.role === "music_audio")?.content_hash === asset.content_hash)) return draft;
  return replaceWholeMedia(draft, { ...draft.payload, music: asset ? { material_revision_id: asset.material_revision_id } : {} }, "music_audio", "music", asset);
}

export function setCover(draft: VideoDraft, asset: ExactVideoAsset | null): VideoDraft {
  validateMedia(asset, "image", "Cover");
  if (draft.payload.cover.material_revision_id === asset?.material_revision_id && (!asset || draft.assetRefs.find((ref) => ref.role === "cover_image")?.content_hash === asset.content_hash)) return draft;
  return replaceWholeMedia(draft, { ...draft.payload, cover: asset ? { material_revision_id: asset.material_revision_id } : {} }, "cover_image", "cover", asset);
}

export function bindFinalRender(draft: VideoDraft, asset: ExactVideoAsset | null): VideoDraft {
  validateMedia(asset, "video", "Final render", true);
  const old = draft.assetRefs.find((ref) => ref.role === "render_output");
  if (draft.payload.render_asset_ref?.material_revision_id === asset?.material_revision_id && (!asset || old?.content_hash === asset.content_hash)) return draft;
  const payload = { ...draft.payload };
  if (asset) payload.render_asset_ref = { material_revision_id: asset.material_revision_id };
  else delete payload.render_asset_ref;
  const refs = draft.assetRefs.filter((ref) => ref.role !== "render_output");
  if (asset) refs.push({ material_revision_id: asset.material_revision_id, content_hash: asset.content_hash, role: "render_output", slot_key: "final", placement: { render: "final" } });
  return { ...draft, payload, assetRefs: orderedAssetRefs(payload, refs) };
}

function validateCues(cues: VideoCue[], duration_ms: number): void {
  let previousEnd = 0;
  for (const cue of cues) {
    validTiming(cue.start_ms, cue.end_ms, duration_ms);
    if (cue.start_ms < previousEnd) throw new Error("Subtitle cues overlap");
    if (cue.text.length > 500 || cue.text.includes("\0")) throw new Error("Subtitle text invalid");
    previousEnd = cue.end_ms;
  }
}

export function addSubtitleCue(draft: VideoDraft, input: Pick<VideoCue, "text" | "start_ms" | "end_ms">): VideoDraft {
  const cues = draft.payload.subtitles.cues;
  if (cues.length >= 1000) throw new Error("Subtitle cue limit reached");
  const next = [...cues, { id: crypto.randomUUID(), order: cues.length, ...input }];
  validateCues(next, draft.payload.timeline.duration_ms);
  return changed(draft, { ...draft.payload, subtitles: { cues: next } });
}

export function updateSubtitleCue(draft: VideoDraft, id: string, patch: Partial<Pick<VideoCue, "text" | "start_ms" | "end_ms">>): VideoDraft {
  const old = draft.payload.subtitles.cues.find((cue) => cue.id === id);
  if (!old) throw new Error("Subtitle cue not found");
  const next = draft.payload.subtitles.cues.map((cue) => cue.id === id ? { ...cue, ...patch } : cue);
  validateCues(next, draft.payload.timeline.duration_ms);
  return JSON.stringify(old) === JSON.stringify(next[old.order]) ? draft : changed(draft, { ...draft.payload, subtitles: { cues: next } });
}

export function removeSubtitleCue(draft: VideoDraft, id: string): VideoDraft {
  if (!draft.payload.subtitles.cues.some((cue) => cue.id === id)) throw new Error("Subtitle cue not found");
  return changed(draft, { ...draft.payload, subtitles: { cues: reordered(draft.payload.subtitles.cues.filter((cue) => cue.id !== id)) } });
}

export function importSubtitleSrt(draft: VideoDraft, raw: string): VideoDraft {
  if (typeof raw !== "string" || raw.length > 512_000 || raw.includes("\0")) throw new Error("SRT file invalid or too large");
  const entries = raw.replace(/^\uFEFF/, "").replace(/\r\n?/g, "\n").trim().split(/\n\s*\n/);
  if (entries.length === 0 || entries.length > 1000) throw new Error("SRT cue count invalid");
  function time(value: string): number {
    const match = /^(\d{2}):(\d{2}):(\d{2}),(\d{3})$/.exec(value);
    if (!match) throw new Error("SRT timecode invalid");
    const [, hours, minutes, seconds, milliseconds] = match;
    if (Number(minutes) >= 60 || Number(seconds) >= 60) throw new Error("SRT timecode invalid");
    return ((Number(hours) * 60 + Number(minutes)) * 60 + Number(seconds)) * 1000 + Number(milliseconds);
  }
  const cues = entries.map((entry, order): VideoCue => {
    const lines = entry.split("\n");
    const timingIndex = /^\d+$/.test(lines[0].trim()) ? 1 : 0;
    const match = /^(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})$/.exec(lines[timingIndex]?.trim() || "");
    if (!match || lines.length <= timingIndex + 1) throw new Error("SRT cue structure invalid");
    return { id: crypto.randomUUID(), order, start_ms: time(match[1]), end_ms: time(match[2]), text: lines.slice(timingIndex + 1).join("\n") };
  });
  validateCues(cues, draft.payload.timeline.duration_ms);
  return changed(draft, { ...draft.payload, subtitles: { cues } });
}

function validateOverlay(input: Pick<VideoOverlay, "text" | "start_ms" | "end_ms" | "x" | "y">, duration_ms: number): void {
  validTiming(input.start_ms, input.end_ms, duration_ms);
  if (!input.text.trim() || input.text.length > 1000 || input.text.includes("\0")) throw new Error("Overlay text invalid");
  if (![input.x, input.y].every((value) => Number.isFinite(value) && value >= 0 && value <= 1)) throw new Error("Overlay position invalid");
}

export function addOverlay(draft: VideoDraft, input: Pick<VideoOverlay, "text" | "start_ms" | "end_ms" | "x" | "y">): VideoDraft {
  if (draft.payload.overlays.length >= 300) throw new Error("Overlay limit reached");
  validateOverlay(input, draft.payload.timeline.duration_ms);
  return changed(draft, { ...draft.payload, overlays: [...draft.payload.overlays, { id: crypto.randomUUID(), order: draft.payload.overlays.length, ...input }] });
}

export function updateOverlay(draft: VideoDraft, id: string, patch: Partial<Pick<VideoOverlay, "text" | "start_ms" | "end_ms" | "x" | "y">>): VideoDraft {
  const old = draft.payload.overlays.find((overlay) => overlay.id === id);
  if (!old) throw new Error("Overlay not found");
  const next = { ...old, ...patch };
  validateOverlay(next, draft.payload.timeline.duration_ms);
  if (JSON.stringify(old) === JSON.stringify(next)) return draft;
  return changed(draft, { ...draft.payload, overlays: draft.payload.overlays.map((overlay) => overlay.id === id ? next : overlay) });
}

export function removeOverlay(draft: VideoDraft, id: string): VideoDraft {
  if (!draft.payload.overlays.some((overlay) => overlay.id === id)) throw new Error("Overlay not found");
  return changed(draft, { ...draft.payload, overlays: reordered(draft.payload.overlays.filter((overlay) => overlay.id !== id)) });
}
