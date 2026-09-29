export type GraphicClaim = { fact_pack_item_id: number; snapshot_checksum: string; start: number; end: number };
export type GraphicTextRun = { text: string; style: { font_size: number; color: string; weight?: number; italic?: boolean; align?: "left" | "center" | "right" } };
type LayerBase = { id: string; order: number; x: number; y: number; width: number; height: number; rotation?: number; opacity?: number; visible?: boolean; locked?: boolean };
export type GraphicTextLayer = LayerBase & { type: "text"; runs: GraphicTextRun[]; claims?: GraphicClaim[] };
export type GraphicMediaLayer = LayerBase & { type: "image" | "chart"; material_revision_id: number; fit: "cover" | "contain" | "fill"; crop?: { x: number; y: number; width: number; height: number }; focal?: { x: number; y: number } };
export type GraphicShapeLayer = LayerBase & { type: "shape"; shape: "rectangle" | "ellipse" | "line"; fill: string; stroke?: string; stroke_width?: number };
export type GraphicLayer = GraphicTextLayer | GraphicMediaLayer | GraphicShapeLayer;
export type GraphicCanvas = { id: string; order: number; width: number; height: number; background: { color: string }; role?: "cover" | "body"; variant_of_canvas_id?: string; layers: GraphicLayer[] };
export type GraphicPayload = { title: string; canvases: GraphicCanvas[]; render_asset_ref?: { canvas_id: string; material_revision_id: number }[] };
export type GraphicAssetRef = { material_revision_id: number; content_hash: string; role: string; slot_key?: string; sort_order?: number; placement?: { canvas_id: string; layer_id?: string } };
export type GraphicEvidenceRef = { fact_pack_item_id: number; snapshot_checksum: string; role?: string; sort_order?: number; locator: { canvas_id: string; layer_id: string; start: number; end: number } };
export type GraphicDraft = { payloadSchema: "graphic.master.v2"; payload: GraphicPayload; assetRefs: GraphicAssetRef[]; evidenceRefs: GraphicEvidenceRef[] };

function reorder<T extends { order: number }>(items: T[]): T[] { return items.map((item, index) => ({ ...item, order: index })); }
function newCanvas(order: number): GraphicCanvas { return { id: crypto.randomUUID(), order, width: 1080, height: 1440, background: { color: "#ffffff" }, layers: [] }; }
function withChangedContent(draft: GraphicDraft, payload: GraphicPayload, assetRefs = draft.assetRefs, evidenceRefs = draft.evidenceRefs): GraphicDraft {
  const next = { ...payload };
  delete next.render_asset_ref;
  return { ...draft, payload: next, assetRefs: assetRefs.filter((ref) => ref.role !== "render_output"), evidenceRefs };
}

export function updateGraphicTitle(draft: GraphicDraft, title: string): GraphicDraft { return title === draft.payload.title ? draft : withChangedContent(draft, { ...draft.payload, title }); }
export function updateCanvas(draft: GraphicDraft, canvas: GraphicCanvas): GraphicDraft {
  const current = draft.payload.canvases.find((item) => item.id === canvas.id);
  if (!current) throw new Error("Canvas not found");
  if (JSON.stringify(current) === JSON.stringify(canvas)) return draft;
  return withChangedContent(draft, { ...draft.payload, canvases: draft.payload.canvases.map((item) => item.id === canvas.id ? canvas : item) });
}

export function createGraphicDraft(): GraphicDraft {
  return { payloadSchema: "graphic.master.v2", payload: { title: "", canvases: [newCanvas(0)] }, assetRefs: [], evidenceRefs: [] };
}

export function graphicDraftFromMaster(master: { payload_schema: string; payload: Record<string, unknown>; assets?: Record<string, unknown>[]; evidence?: Record<string, unknown>[] }): GraphicDraft {
  if (master.payload_schema !== "graphic.master.v2") throw new Error("Graphic Master v1 requires explicit upgrade before editing");
  if (!Array.isArray(master.payload?.canvases)) throw new Error("Unsupported Graphic document");
  return {
    payloadSchema: "graphic.master.v2", payload: structuredClone(master.payload) as GraphicPayload,
    assetRefs: (master.assets || []).map((row) => ({ material_revision_id: Number(row.material_revision_id), content_hash: String(row.content_hash), role: String(row.role), ...(row.slot_key != null ? { slot_key: String(row.slot_key) } : {}), ...(row.sort_order != null ? { sort_order: Number(row.sort_order) } : {}), ...(row.placement != null ? { placement: row.placement as GraphicAssetRef["placement"] } : {}) })),
    evidenceRefs: (master.evidence || []).map((row) => ({ fact_pack_item_id: Number(row.fact_pack_item_id), snapshot_checksum: String(row.snapshot_checksum), ...(row.role != null ? { role: String(row.role) } : {}), ...(row.sort_order != null ? { sort_order: Number(row.sort_order) } : {}), locator: row.locator as GraphicEvidenceRef["locator"] })),
  };
}

export function addCanvas(draft: GraphicDraft): GraphicDraft {
  if (draft.payload.canvases.length >= 24) throw new Error("Canvas limit reached");
  return withChangedContent(draft, { ...draft.payload, canvases: [...draft.payload.canvases, newCanvas(draft.payload.canvases.length)] });
}

export function duplicateCanvas(draft: GraphicDraft, canvasId: string): GraphicDraft {
  if (draft.payload.canvases.length >= 24) throw new Error("Canvas limit reached");
  const source = draft.payload.canvases.find((item) => item.id === canvasId);
  if (!source) throw new Error("Canvas not found");
  const copyId = crypto.randomUUID();
  const layerIds = new Map(source.layers.map((layer) => [layer.id, crypto.randomUUID()]));
  const copy: GraphicCanvas = { ...structuredClone(source), id: copyId, order: draft.payload.canvases.length, role: "body", variant_of_canvas_id: source.id, layers: source.layers.map((layer): GraphicLayer => layer.type === "text" ? { ...structuredClone(layer), id: layerIds.get(layer.id)!, claims: [] } : { ...structuredClone(layer), id: layerIds.get(layer.id)! }) };
  const clonedRefs: GraphicAssetRef[] = source.layers.filter((layer) => layer.type === "image" || layer.type === "chart").map((layer, index) => {
    const ref = draft.assetRefs.find((item) => item.role === "graphic_layer" && item.placement?.canvas_id === canvasId && item.placement?.layer_id === layer.id);
    if (!ref) throw new Error("Exact media reference missing");
    return { ...ref, slot_key: layerIds.get(layer.id)!, sort_order: draft.assetRefs.length + index, placement: { canvas_id: copyId, layer_id: layerIds.get(layer.id)! } };
  });
  return withChangedContent(draft, { ...draft.payload, canvases: [...draft.payload.canvases, copy] }, [...draft.assetRefs, ...clonedRefs]);
}

export function removeCanvas(draft: GraphicDraft, canvasId: string): GraphicDraft {
  if (draft.payload.canvases.length === 1) throw new Error("Cannot remove last canvas");
  if (!draft.payload.canvases.some((item) => item.id === canvasId)) throw new Error("Canvas not found");
  const canvases = reorder(draft.payload.canvases.filter((item) => item.id !== canvasId).map((item) => {
    if (item.variant_of_canvas_id !== canvasId) return item;
    const next = { ...item };
    delete next.variant_of_canvas_id;
    return next;
  }));
  return withChangedContent(draft, { ...draft.payload, canvases }, draft.assetRefs.filter((ref) => ref.placement?.canvas_id !== canvasId), draft.evidenceRefs.filter((ref) => ref.locator.canvas_id !== canvasId));
}

export function reorderCanvases(draft: GraphicDraft, canvasId: string, toIndex: number): GraphicDraft {
  const canvases = [...draft.payload.canvases];
  const fromIndex = canvases.findIndex((item) => item.id === canvasId);
  if (fromIndex < 0 || toIndex < 0 || toIndex >= canvases.length) throw new Error("Canvas order invalid");
  canvases.splice(toIndex, 0, canvases.splice(fromIndex, 1)[0]);
  if (fromIndex === toIndex) return draft;
  return withChangedContent(draft, { ...draft.payload, canvases: reorder(canvases) });
}

export function appendTextLayer(draft: GraphicDraft, canvasId: string): GraphicDraft {
  let found = false;
  const canvases = draft.payload.canvases.map((canvas) => {
    if (canvas.id !== canvasId) return canvas;
    found = true;
    if (canvas.layers.length >= 128) throw new Error("Layer limit reached");
    const layer: GraphicTextLayer = { id: crypto.randomUUID(), order: canvas.layers.length, type: "text", x: 20, y: 20, width: Math.min(400, canvas.width), height: 80, runs: [{ text: "", style: { font_size: 30, color: "#123456" } }], claims: [] };
    return { ...canvas, layers: [...canvas.layers, layer] };
  });
  if (!found) throw new Error("Canvas not found");
  return withChangedContent(draft, { ...draft.payload, canvases });
}

export function updateTextLayer(draft: GraphicDraft, canvasId: string, layerId: string, text: string): GraphicDraft {
  let found = false;
  let changed = false;
  const canvases = draft.payload.canvases.map((canvas) => canvas.id !== canvasId ? canvas : { ...canvas, layers: canvas.layers.map((layer) => {
    if (layer.id !== layerId) return layer;
    if (layer.type !== "text") throw new Error("Layer is not text");
    found = true;
    if (text.length > 10_000) throw new Error("Text layer too long");
    if (layer.runs.map((run) => run.text).join("") === text) return layer;
    changed = true;
    return { ...layer, runs: [{ text, style: layer.runs[0].style }], claims: [] };
  }) });
  if (!found) throw new Error("Text layer not found");
  if (!changed) return draft;
  return withChangedContent(draft, { ...draft.payload, canvases }, draft.assetRefs, draft.evidenceRefs.filter((ref) => ref.locator.canvas_id !== canvasId || ref.locator.layer_id !== layerId));
}

export function insertMediaLayer(draft: GraphicDraft, canvasId: string, asset: { material_revision_id: number; content_hash: string; kind: string; public_use_allowed: boolean }): GraphicDraft {
  if (!asset.public_use_allowed) throw new Error("Asset rights do not allow public use");
  if (asset.kind !== "image" && asset.kind !== "chart") throw new Error("Graphic media kind unsupported");
  let found = false;
  const layerId = crypto.randomUUID();
  const canvases = draft.payload.canvases.map((canvas) => {
    if (canvas.id !== canvasId) return canvas;
    found = true;
    if (canvas.layers.length >= 128) throw new Error("Layer limit reached");
    const layer: GraphicMediaLayer = { id: layerId, order: canvas.layers.length, type: asset.kind as "image" | "chart", x: 20, y: 20, width: Math.min(400, canvas.width), height: Math.min(300, canvas.height), material_revision_id: asset.material_revision_id, fit: "contain" };
    return { ...canvas, layers: [...canvas.layers, layer] };
  });
  if (!found) throw new Error("Canvas not found");
  return withChangedContent(draft, { ...draft.payload, canvases }, [...draft.assetRefs, { material_revision_id: asset.material_revision_id, content_hash: asset.content_hash, role: "graphic_layer", slot_key: layerId, sort_order: draft.assetRefs.length, placement: { canvas_id: canvasId, layer_id: layerId } }]);
}

export function removeLayer(draft: GraphicDraft, canvasId: string, layerId: string): GraphicDraft {
  let found = false;
  const canvases = draft.payload.canvases.map((canvas) => {
    if (canvas.id !== canvasId) return canvas;
    const layers = canvas.layers.filter((layer) => layer.id !== layerId);
    found = layers.length !== canvas.layers.length;
    return { ...canvas, layers: reorder(layers) };
  });
  if (!found) throw new Error("Layer not found");
  return withChangedContent(draft, { ...draft.payload, canvases }, draft.assetRefs.filter((ref) => ref.placement?.canvas_id !== canvasId || ref.placement.layer_id !== layerId), draft.evidenceRefs.filter((ref) => ref.locator.canvas_id !== canvasId || ref.locator.layer_id !== layerId));
}

function editLayer(draft: GraphicDraft, canvasId: string, layerId: string, edit: (layer: GraphicLayer) => GraphicLayer, allowLocked = false): GraphicDraft {
  let found = false;
  let changed = false;
  const canvases = draft.payload.canvases.map((canvas) => canvas.id !== canvasId ? canvas : { ...canvas, layers: canvas.layers.map((layer) => {
    if (layer.id !== layerId) return layer;
    found = true;
    if (layer.locked && !allowLocked) throw new Error("Layer is locked");
    const next = edit(layer);
    if (JSON.stringify(next) !== JSON.stringify(layer)) changed = true;
    return next;
  }) });
  if (!found) throw new Error("Layer not found");
  return changed ? withChangedContent(draft, { ...draft.payload, canvases }) : draft;
}

export function updateLayerGeometry(draft: GraphicDraft, canvasId: string, layerId: string, patch: Partial<Pick<GraphicLayer, "x" | "y" | "width" | "height" | "rotation" | "opacity">>): GraphicDraft {
  for (const [key, value] of Object.entries(patch)) {
    const minimum = key === "width" || key === "height" ? 1 : key === "opacity" ? 0 : key === "rotation" ? -360 : -8192;
    const maximum = key === "opacity" ? 1 : key === "rotation" ? 360 : 8192;
    if (typeof value !== "number" || !Number.isFinite(value) || value < minimum || value > maximum) throw new Error("Graphic geometry invalid");
  }
  return editLayer(draft, canvasId, layerId, (layer) => ({ ...layer, ...patch }));
}

export function updateTextStyle(draft: GraphicDraft, canvasId: string, layerId: string, patch: Partial<GraphicTextRun["style"]>): GraphicDraft {
  return editLayer(draft, canvasId, layerId, (layer) => {
    if (layer.type !== "text") throw new Error("Layer is not text");
    const style = { ...layer.runs[0].style, ...patch };
    if (!Number.isFinite(style.font_size) || style.font_size < 1 || style.font_size > 256 || !/^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$/.test(style.color) || (style.weight !== undefined && (!Number.isInteger(style.weight) || style.weight < 100 || style.weight > 900 || style.weight % 100 !== 0)) || (style.align !== undefined && !["left", "center", "right"].includes(style.align))) throw new Error("Graphic text style invalid");
    return { ...layer, runs: layer.runs.map((run) => ({ ...run, style: { ...run.style, ...patch } })) };
  });
}

export function reorderLayers(draft: GraphicDraft, canvasId: string, layerId: string, toIndex: number): GraphicDraft {
  const canvas = draft.payload.canvases.find((item) => item.id === canvasId);
  if (!canvas) throw new Error("Canvas not found");
  const layers = [...canvas.layers];
  const fromIndex = layers.findIndex((layer) => layer.id === layerId);
  if (fromIndex < 0 || toIndex < 0 || toIndex >= layers.length) throw new Error("Layer order invalid");
  if (layers[fromIndex].locked) throw new Error("Layer is locked");
  if (fromIndex === toIndex) return draft;
  layers.splice(toIndex, 0, layers.splice(fromIndex, 1)[0]);
  return updateCanvas(draft, { ...canvas, layers: reorder(layers) });
}

export function setLayerFlags(draft: GraphicDraft, canvasId: string, layerId: string, flags: Partial<Pick<GraphicLayer, "visible" | "locked">>): GraphicDraft {
  if (Object.values(flags).some((value) => typeof value !== "boolean")) throw new Error("Layer flags invalid");
  return editLayer(draft, canvasId, layerId, (layer) => ({ ...layer, ...flags }), true);
}

export function updateMediaPlacement(draft: GraphicDraft, canvasId: string, layerId: string, patch: Partial<Pick<GraphicMediaLayer, "fit" | "crop" | "focal">>): GraphicDraft {
  if (patch.fit !== undefined && !["cover", "contain", "fill"].includes(patch.fit)) throw new Error("Media fit invalid");
  if (patch.crop !== undefined) {
    const { x, y, width, height } = patch.crop;
    if (![x, y, width, height].every((value) => Number.isFinite(value) && value >= 0 && value <= 1) || width === 0 || height === 0 || x + width > 1 || y + height > 1) throw new Error("Media crop invalid");
  }
  if (patch.focal !== undefined && ![patch.focal.x, patch.focal.y].every((value) => Number.isFinite(value) && value >= 0 && value <= 1)) throw new Error("Media focal invalid");
  return editLayer(draft, canvasId, layerId, (layer) => {
    if (layer.type !== "image" && layer.type !== "chart") throw new Error("Layer is not media");
    return { ...layer, ...patch };
  });
}

export function replaceMediaLayer(draft: GraphicDraft, canvasId: string, layerId: string, asset: { material_revision_id: number; content_hash: string; kind: string; public_use_allowed: boolean }): GraphicDraft {
  if (!asset.public_use_allowed) throw new Error("Asset rights do not allow public use");
  if (asset.kind !== "image" && asset.kind !== "chart") throw new Error("Graphic media kind unsupported");
  if (!Number.isInteger(asset.material_revision_id) || asset.material_revision_id <= 0 || !/^[a-f0-9]{64}$/i.test(asset.content_hash)) throw new Error("Exact media reference invalid");
  const edited = editLayer(draft, canvasId, layerId, (layer) => {
    if (layer.type !== "image" && layer.type !== "chart") throw new Error("Layer is not media");
    return { ...layer, type: asset.kind as "image" | "chart", material_revision_id: asset.material_revision_id };
  });
  const currentRef = edited.assetRefs.find((ref) => ref.role === "graphic_layer" && ref.placement?.canvas_id === canvasId && ref.placement.layer_id === layerId);
  if (!currentRef) throw new Error("Exact media reference missing");
  if (currentRef.material_revision_id === asset.material_revision_id && currentRef.content_hash === asset.content_hash) return edited;
  return withChangedContent(edited, edited.payload, edited.assetRefs.map((ref) => ref === currentRef ? { ...ref, material_revision_id: asset.material_revision_id, content_hash: asset.content_hash } : ref));
}

export function insertShapeLayer(draft: GraphicDraft, canvasId: string, shape: GraphicShapeLayer["shape"]): GraphicDraft {
  if (!["rectangle", "ellipse", "line"].includes(shape)) throw new Error("Shape invalid");
  const canvas = draft.payload.canvases.find((item) => item.id === canvasId);
  if (!canvas) throw new Error("Canvas not found");
  if (canvas.layers.length >= 128) throw new Error("Layer limit reached");
  const layer: GraphicShapeLayer = { id: crypto.randomUUID(), order: canvas.layers.length, type: "shape", shape, x: 20, y: 20, width: Math.min(400, canvas.width), height: Math.min(300, canvas.height), fill: "#00000000" };
  return updateCanvas(draft, { ...canvas, layers: [...canvas.layers, layer] });
}

export function bindFinalRender(draft: GraphicDraft, canvasId: string, asset: { material_revision_id: number; content_hash: string; kind: string; public_use_allowed: boolean } | null): GraphicDraft {
  if (!draft.payload.canvases.some((canvas) => canvas.id === canvasId)) throw new Error("Canvas not found");
  if (asset && (!asset.public_use_allowed || asset.kind !== "image" || !Number.isInteger(asset.material_revision_id) || asset.material_revision_id <= 0 || !/^[a-f0-9]{64}$/i.test(asset.content_hash))) throw new Error(asset.public_use_allowed === false ? "Final render rights do not allow public use" : "Final render must be an exact image revision");
  const existing = draft.assetRefs.filter((ref) => ref.role === "render_output" && ref.placement?.canvas_id !== canvasId);
  if (asset && existing.some((ref) => ref.material_revision_id === asset.material_revision_id)) throw new Error("Final render revisions must be distinct per canvas");
  const current = draft.assetRefs.find((ref) => ref.role === "render_output" && ref.placement?.canvas_id === canvasId);
  if (asset && current?.material_revision_id === asset.material_revision_id && current.content_hash === asset.content_hash) return draft;
  if (!asset && !current) return draft;
  const byCanvas = new Map(existing.map((ref) => [ref.placement!.canvas_id, ref]));
  if (asset) byCanvas.set(canvasId, { material_revision_id: asset.material_revision_id, content_hash: asset.content_hash, role: "render_output", slot_key: canvasId, placement: { canvas_id: canvasId } });
  const ordered = draft.payload.canvases.flatMap((canvas) => {
    const ref = byCanvas.get(canvas.id);
    return ref ? [{ ...ref, sort_order: canvas.order, slot_key: canvas.id, placement: { canvas_id: canvas.id } }] : [];
  });
  const payload = { ...draft.payload };
  if (ordered.length) payload.render_asset_ref = ordered.map((ref) => ({ canvas_id: ref.placement!.canvas_id, material_revision_id: ref.material_revision_id }));
  else delete payload.render_asset_ref;
  return { ...draft, payload, assetRefs: [...draft.assetRefs.filter((ref) => ref.role !== "render_output"), ...ordered] };
}

export function bindGraphicClaim(draft: GraphicDraft, canvasId: string, layerId: string, start: number, end: number, item: { item_id: number; snapshot_checksum: string; public_use_allowed: boolean; public_use_revoked_at: string | null }): GraphicDraft {
  if (!item.public_use_allowed || item.public_use_revoked_at) throw new Error("Evidence rights do not allow public use");
  if (!Number.isInteger(item.item_id) || item.item_id <= 0 || !/^[a-f0-9]{64}$/i.test(item.snapshot_checksum)) throw new Error("Exact evidence invalid");
  const layer = draft.payload.canvases.find((canvas) => canvas.id === canvasId)?.layers.find((value) => value.id === layerId);
  if (layer?.type !== "text") throw new Error("Text layer not found");
  const length = Array.from(layer.runs.map((run) => run.text).join("")).length;
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start || end > length) throw new Error("Evidence range invalid");
  if (layer.claims?.some((claim) => claim.fact_pack_item_id === item.item_id && claim.snapshot_checksum === item.snapshot_checksum && claim.start === start && claim.end === end)) return draft;
  if ((layer.claims?.length || 0) >= 100) throw new Error("Evidence claim limit reached");
  const claim = { fact_pack_item_id: item.item_id, snapshot_checksum: item.snapshot_checksum, start, end };
  const edited = editLayer(draft, canvasId, layerId, (value) => {
    if (value.type !== "text") throw new Error("Text layer not found");
    return { ...value, claims: [...(value.claims || []), claim] };
  });
  return { ...edited, evidenceRefs: [...edited.evidenceRefs, { fact_pack_item_id: item.item_id, snapshot_checksum: item.snapshot_checksum, role: "claim", sort_order: edited.evidenceRefs.length, locator: { canvas_id: canvasId, layer_id: layerId, start, end } }] };
}

export function unbindGraphicClaim(draft: GraphicDraft, canvasId: string, layerId: string, factPackItemId: number, start: number, end: number): GraphicDraft {
  const edited = editLayer(draft, canvasId, layerId, (layer) => {
    if (layer.type !== "text") throw new Error("Text layer not found");
    if (!layer.claims?.some((claim) => claim.fact_pack_item_id === factPackItemId && claim.start === start && claim.end === end)) return layer;
    return { ...layer, claims: layer.claims.filter((claim) => claim.fact_pack_item_id !== factPackItemId || claim.start !== start || claim.end !== end) };
  });
  if (edited === draft) return draft;
  return { ...edited, evidenceRefs: edited.evidenceRefs.filter((ref) => ref.locator.canvas_id !== canvasId || ref.locator.layer_id !== layerId || ref.fact_pack_item_id !== factPackItemId || ref.locator.start !== start || ref.locator.end !== end) };
}
