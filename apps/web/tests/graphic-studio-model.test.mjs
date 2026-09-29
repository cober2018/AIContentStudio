import test from "node:test";
import assert from "node:assert/strict";
import { createGraphicDraft, graphicDraftFromMaster, addCanvas, duplicateCanvas, removeCanvas, reorderCanvases, appendTextLayer, updateTextLayer, insertMediaLayer, removeLayer, updateLayerGeometry, updateTextStyle, reorderLayers, setLayerFlags, updateMediaPlacement, replaceMediaLayer, insertShapeLayer, bindFinalRender, bindGraphicClaim, unbindGraphicClaim, updateGraphicTitle } from "../src/product/GraphicStudioModel.ts";

test("new Graphic Studio state is v2 with one editable canvas and no fabricated render", () => {
  const draft = createGraphicDraft();
  assert.equal(draft.payloadSchema, "graphic.master.v2");
  assert.equal(draft.payload.canvases.length, 1);
  assert.equal(draft.payload.canvases[0].order, 0);
  assert.equal("render_asset_ref" in draft.payload, false);
  assert.deepEqual(draft.assetRefs, []);
});

test("existing v2 reload preserves exact refs while v1 requires explicit upgrade", () => {
  const draft = createGraphicDraft();
  const master = { payload_schema: "graphic.master.v2", payload: draft.payload, assets: [{ material_revision_id: 7, content_hash: "a".repeat(64), role: "graphic_layer", slot_key: "hero", placement: { canvas_id: "one", layer_id: "hero" } }], evidence: [] };
  assert.equal(graphicDraftFromMaster(master).assetRefs[0].slot_key, "hero");
  assert.throws(() => graphicDraftFromMaster({ ...master, payload_schema: "graphic.master.v1" }), /explicit.*upgrade/i);
});

test("canvas ordering and text edits preserve IDs but invalidate old claims", () => {
  const start = createGraphicDraft();
  const withSecond = addCanvas(start);
  const firstId = start.payload.canvases[0].id;
  const secondId = withSecond.payload.canvases[1].id;
  assert.notEqual(firstId, secondId);
  assert.deepEqual(reorderCanvases(withSecond, secondId, 0).payload.canvases.map((row) => [row.id, row.order]), [[secondId, 0], [firstId, 1]]);
  const withLayer = appendTextLayer(start, firstId);
  const layerId = withLayer.payload.canvases[0].layers[0].id;
  const claimed = { ...withLayer, payload: { ...withLayer.payload, canvases: [{ ...withLayer.payload.canvases[0], layers: [{ ...withLayer.payload.canvases[0].layers[0], claims: [{ fact_pack_item_id: 8, snapshot_checksum: "b".repeat(64), start: 0, end: 1 }] }] }] }, evidenceRefs: [{ fact_pack_item_id: 8, snapshot_checksum: "b".repeat(64), role: "claim", locator: { canvas_id: firstId, layer_id: layerId, start: 0, end: 1 } }] };
  assert.deepEqual(updateTextLayer(claimed, firstId, layerId, "").evidenceRefs, claimed.evidenceRefs);
  const edited = updateTextLayer(claimed, firstId, layerId, "新文");
  assert.equal(edited.payload.canvases[0].layers[0].id, layerId);
  assert.deepEqual(edited.payload.canvases[0].layers[0].claims, []);
  assert.deepEqual(edited.evidenceRefs, []);
});

test("exact media insertion and removal update layer plus per-placement ref together", () => {
  const start = createGraphicDraft();
  const canvasId = start.payload.canvases[0].id;
  const asset = { material_revision_id: 12, content_hash: "a".repeat(64), kind: "image", public_use_allowed: true };
  const inserted = insertMediaLayer(start, canvasId, asset);
  const layerId = inserted.payload.canvases[0].layers[0].id;
  assert.deepEqual(inserted.assetRefs[0].placement, { canvas_id: canvasId, layer_id: layerId });
  assert.equal(inserted.assetRefs[0].role, "graphic_layer");
  assert.equal(inserted.payload.canvases[0].layers[0].material_revision_id, 12);
  const removed = removeLayer(inserted, canvasId, layerId);
  assert.deepEqual(removed.assetRefs, []);
  assert.deepEqual(removed.payload.canvases[0].layers, []);
  assert.throws(() => insertMediaLayer(start, canvasId, { ...asset, public_use_allowed: false }), /rights/i);
});

test("content changes drop stale final render declarations and output refs", () => {
  const start = createGraphicDraft();
  const canvasId = start.payload.canvases[0].id;
  const withLayer = appendTextLayer(start, canvasId);
  const layerId = withLayer.payload.canvases[0].layers[0].id;
  const rendered = { ...withLayer, payload: { ...withLayer.payload, render_asset_ref: [{ canvas_id: canvasId, material_revision_id: 22 }] }, assetRefs: [{ material_revision_id: 22, content_hash: "a".repeat(64), role: "render_output", slot_key: canvasId, sort_order: 0, placement: { canvas_id: canvasId } }] };
  assert.equal(updateTextLayer(rendered, canvasId, layerId, "").payload.render_asset_ref.length, 1);
  const changed = updateTextLayer(rendered, canvasId, layerId, "修改后");
  assert.equal("render_asset_ref" in changed.payload, false);
  assert.deepEqual(changed.assetRefs, []);
  const expanded = addCanvas(rendered);
  assert.equal("render_asset_ref" in expanded.payload, false);
  assert.deepEqual(expanded.assetRefs, []);
});

test("duplicate canvas gets new stable IDs, exact media placement, but no inherited claim or final render", () => {
  const start = createGraphicDraft();
  const canvasId = start.payload.canvases[0].id;
  const withMedia = insertMediaLayer(start, canvasId, { material_revision_id: 12, content_hash: "a".repeat(64), kind: "image", public_use_allowed: true });
  const duplicated = duplicateCanvas(withMedia, canvasId);
  const copy = duplicated.payload.canvases[1];
  assert.notEqual(copy.id, canvasId);
  assert.equal(copy.variant_of_canvas_id, canvasId);
  assert.notEqual(copy.layers[0].id, withMedia.payload.canvases[0].layers[0].id);
  assert.equal(copy.layers[0].material_revision_id, 12);
  assert.deepEqual(duplicated.assetRefs[1].placement, { canvas_id: copy.id, layer_id: copy.layers[0].id });
  assert.equal("render_asset_ref" in duplicated.payload, false);
  const removed = removeCanvas(duplicated, canvasId);
  assert.deepEqual(removed.payload.canvases.map((row) => row.order), [0]);
  assert.equal("variant_of_canvas_id" in removed.payload.canvases[0], false);
  assert.equal(removed.assetRefs.length, 1);
  assert.throws(() => removeCanvas(removed, copy.id), /last canvas/i);
});

test("bounded geometry and text style edits invalidate render without dropping unchanged evidence", () => {
  const start = createGraphicDraft();
  const canvasId = start.payload.canvases[0].id;
  const withText = appendTextLayer(start, canvasId);
  const layerId = withText.payload.canvases[0].layers[0].id;
  const rendered = { ...withText, payload: { ...withText.payload, render_asset_ref: [{ canvas_id: canvasId, material_revision_id: 22 }] }, assetRefs: [{ material_revision_id: 22, content_hash: "a".repeat(64), role: "render_output", slot_key: canvasId, placement: { canvas_id: canvasId } }] };
  const moved = updateLayerGeometry(rendered, canvasId, layerId, { x: 34, y: 45, width: 200, rotation: 15 });
  assert.equal(moved.payload.canvases[0].layers[0].x, 34);
  assert.equal("render_asset_ref" in moved.payload, false);
  assert.deepEqual(moved.assetRefs, []);
  assert.equal(updateLayerGeometry(moved, canvasId, layerId, { x: 34 }), moved);
  assert.throws(() => updateLayerGeometry(moved, canvasId, layerId, { width: 0 }), /geometry/i);
  assert.throws(() => updateLayerGeometry(moved, canvasId, layerId, { x: Infinity }), /geometry/i);
  const styled = updateTextStyle(moved, canvasId, layerId, { font_size: 48, color: "#abcdef", align: "center" });
  assert.equal(styled.payload.canvases[0].layers[0].runs[0].style.font_size, 48);
  assert.equal(styled.payload.canvases[0].layers[0].runs[0].style.align, "center");
  assert.throws(() => updateTextStyle(moved, canvasId, layerId, { font_size: 300 }), /style/i);
});

test("layer ordering and lock controls preserve exact refs while blocking locked edits", () => {
  const start = createGraphicDraft();
  const canvasId = start.payload.canvases[0].id;
  const withText = appendTextLayer(start, canvasId);
  const withImage = insertMediaLayer(withText, canvasId, { material_revision_id: 12, content_hash: "a".repeat(64), kind: "image", public_use_allowed: true });
  const [textLayer, imageLayer] = withImage.payload.canvases[0].layers;
  const moved = reorderLayers(withImage, canvasId, imageLayer.id, 0);
  assert.deepEqual(moved.payload.canvases[0].layers.map((layer) => [layer.id, layer.order]), [[imageLayer.id, 0], [textLayer.id, 1]]);
  assert.deepEqual(moved.assetRefs, withImage.assetRefs);
  const locked = setLayerFlags(moved, canvasId, imageLayer.id, { locked: true, visible: false });
  assert.equal(locked.payload.canvases[0].layers[0].visible, false);
  assert.throws(() => updateLayerGeometry(locked, canvasId, imageLayer.id, { x: 50 }), /locked/i);
  assert.equal(setLayerFlags(locked, canvasId, imageLayer.id, { locked: false }).payload.canvases[0].layers[0].locked, false);
});

test("media replacement, crop and shape insertion keep exact placements and validate bounds", () => {
  const start = createGraphicDraft();
  const canvasId = start.payload.canvases[0].id;
  const image = insertMediaLayer(start, canvasId, { material_revision_id: 12, content_hash: "a".repeat(64), kind: "image", public_use_allowed: true });
  const layerId = image.payload.canvases[0].layers[0].id;
  const placed = updateMediaPlacement(image, canvasId, layerId, { fit: "cover", crop: { x: 0.1, y: 0.2, width: 0.8, height: 0.7 } });
  assert.equal(placed.payload.canvases[0].layers[0].crop.x, 0.1);
  assert.throws(() => updateMediaPlacement(image, canvasId, layerId, { crop: { x: 0.5, y: 0, width: 0.8, height: 1 } }), /crop/i);
  const chart = replaceMediaLayer(placed, canvasId, layerId, { material_revision_id: 14, content_hash: "b".repeat(64), kind: "chart", public_use_allowed: true });
  assert.equal(chart.payload.canvases[0].layers[0].id, layerId);
  assert.equal(chart.payload.canvases[0].layers[0].type, "chart");
  assert.equal(chart.assetRefs[0].material_revision_id, 14);
  assert.deepEqual(chart.assetRefs[0].placement, { canvas_id: canvasId, layer_id: layerId });
  assert.throws(() => replaceMediaLayer(chart, canvasId, layerId, { material_revision_id: 15, content_hash: "c".repeat(64), kind: "image", public_use_allowed: false }), /rights/i);
  const shaped = insertShapeLayer(chart, canvasId, "ellipse");
  assert.equal(shaped.payload.canvases[0].layers[1].shape, "ellipse");
  assert.equal(shaped.assetRefs.length, 1);
});

test("final render binds exact project image revisions in canonical canvas order without fabricating attestation", () => {
  const start = addCanvas(createGraphicDraft());
  const [first, second] = start.payload.canvases;
  const assetA = { material_revision_id: 21, content_hash: "a".repeat(64), kind: "image", public_use_allowed: true };
  const assetB = { material_revision_id: 22, content_hash: "b".repeat(64), kind: "image", public_use_allowed: true };
  const secondBound = bindFinalRender(start, second.id, assetB);
  assert.deepEqual(secondBound.payload.render_asset_ref, [{ canvas_id: second.id, material_revision_id: 22 }]);
  const both = bindFinalRender(secondBound, first.id, assetA);
  assert.deepEqual(both.payload.render_asset_ref, [{ canvas_id: first.id, material_revision_id: 21 }, { canvas_id: second.id, material_revision_id: 22 }]);
  assert.deepEqual(both.assetRefs.map((ref) => [ref.role, ref.slot_key, ref.sort_order]), [["render_output", first.id, 0], ["render_output", second.id, 1]]);
  assert.equal(bindFinalRender(both, first.id, assetA), both);
  assert.throws(() => bindFinalRender(both, first.id, assetB), /distinct/i);
  assert.throws(() => bindFinalRender(start, first.id, { ...assetA, kind: "chart" }), /image/i);
  assert.throws(() => bindFinalRender(start, first.id, { ...assetA, public_use_allowed: false }), /rights/i);
  const cleared = bindFinalRender(both, first.id, null);
  assert.deepEqual(cleared.payload.render_asset_ref, [{ canvas_id: second.id, material_revision_id: 22 }]);
  assert.equal("render_attestation" in cleared.payload, false);
  assert.equal(updateGraphicTitle(both, "new").payload.render_asset_ref, undefined);
});

test("text claim binding and unbinding change payload and exact evidence ref atomically", () => {
  const start = createGraphicDraft();
  const canvasId = start.payload.canvases[0].id;
  const text = appendTextLayer(start, canvasId);
  const layerId = text.payload.canvases[0].layers[0].id;
  const body = updateTextLayer(text, canvasId, layerId, "A😀B");
  const item = { item_id: 7, snapshot_checksum: "c".repeat(64), public_use_allowed: true, public_use_revoked_at: null };
  const bound = bindGraphicClaim(body, canvasId, layerId, 1, 2, item);
  assert.deepEqual(bound.payload.canvases[0].layers[0].claims, [{ fact_pack_item_id: 7, snapshot_checksum: "c".repeat(64), start: 1, end: 2 }]);
  assert.deepEqual(bound.evidenceRefs[0].locator, { canvas_id: canvasId, layer_id: layerId, start: 1, end: 2 });
  assert.equal(bindGraphicClaim(bound, canvasId, layerId, 1, 2, item), bound);
  assert.throws(() => bindGraphicClaim(body, canvasId, layerId, 1, 4, item), /range/i);
  assert.throws(() => bindGraphicClaim(body, canvasId, layerId, 1, 2, { ...item, public_use_allowed: false }), /rights/i);
  const unbound = unbindGraphicClaim(bound, canvasId, layerId, 7, 1, 2);
  assert.deepEqual(unbound.payload.canvases[0].layers[0].claims, []);
  assert.deepEqual(unbound.evidenceRefs, []);
  assert.equal("render_asset_ref" in unbound.payload, false);
});
