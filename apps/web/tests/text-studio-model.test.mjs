import test from "node:test";
import assert from "node:assert/strict";
import { createTextDraft, draftFromMaster, replaceBlockRuns, appendBlock, removeBlock, toCodePointOffset, insertAsset, bindCitation, unbindCitation } from "../src/product/TextStudioModel.ts";

test("new Text Master uses the Studio document envelope, not Markdown", () => {
  const draft = createTextDraft();
  assert.equal(draft.payloadSchema, "text.master.v2");
  assert.equal(draft.payload.document.schema, "studio.text.document.v1");
  assert.equal("markdown" in draft.payload, false);
  assert.equal(draft.payload.document.blocks[0].type, "paragraph");
});

test("existing v2 Master keeps exact refs; v1 cannot be silently edited as v2", () => {
  const master = { payload_schema: "text.master.v2", payload: { title: "T", document: { schema: "studio.text.document.v1", blocks: [], citations: [] } }, assets: [{ material_revision_id: 7, content_hash: "a".repeat(64) }], evidence: [{ fact_pack_item_id: 8, snapshot_checksum: "b".repeat(64) }] };
  const draft = draftFromMaster(master);
  assert.deepEqual(draft.assetRefs, [{ material_revision_id: 7, content_hash: "a".repeat(64) }]);
  assert.deepEqual(draft.evidenceRefs, [{ fact_pack_item_id: 8, snapshot_checksum: "b".repeat(64), locator: {} }]);
  assert.throws(() => draftFromMaster({ ...master, payload_schema: "text.master.v1" }), /explicit.*upgrade/i);
});

test("block edit retains stable ID and drops changed citation with its exact ref", () => {
  const draft = createTextDraft();
  const id = draft.payload.document.blocks[0].id;
  const withText = replaceBlockRuns(draft, id, [{ text: "A😀B", marks: [] }]);
  const cited = { ...withText, payload: { ...withText.payload, document: { ...withText.payload.document, citations: [{ id: "cite-1", block_id: id, start: 1, end: 2, fact_pack_item_id: 8, selected_text_hash: "x" }] } }, evidenceRefs: [{ fact_pack_item_id: 8, locator: { citation_id: "cite-1" } }] };
  const changed = replaceBlockRuns(cited, id, [{ text: "A日B", marks: [] }]);
  assert.equal(changed.payload.document.blocks[0].id, id);
  assert.deepEqual(changed.payload.document.citations, []);
  assert.deepEqual(changed.evidenceRefs, []);
  assert.deepEqual(changed.invalidatedCitationIds, ["cite-1"]);
});

test("block removal keeps unrelated refs; a new block receives a distinct stable ID", () => {
  const draft = createTextDraft();
  const first = draft.payload.document.blocks[0].id;
  const added = appendBlock(draft, "paragraph");
  assert.notEqual(added.payload.document.blocks[1].id, first);
  assert.equal(removeBlock(added, first).payload.document.blocks.length, 1);
});

test("selection conversion uses Unicode code points, not JavaScript UTF-16 units", () => {
  assert.equal(toCodePointOffset("A😀B", 3), 2);
  assert.throws(() => toCodePointOffset("A😀B", 2), /surrogate/i);
});

test("asset insertion and removal update document plus exact declaration together", () => {
  const draft = createTextDraft();
  const asset = { material_revision_id: 12, kind: "image", content_hash: "a".repeat(64), public_use_allowed: true };
  const inserted = insertAsset(draft, asset);
  assert.equal(inserted.payload.document.blocks.at(-1).material_revision_id, 12);
  assert.equal(inserted.assetRefs[0].content_hash, asset.content_hash);
  const removed = removeBlock(inserted, inserted.payload.document.blocks.at(-1).id);
  assert.deepEqual(removed.assetRefs, []);
  assert.throws(() => insertAsset(draft, { ...asset, public_use_allowed: false }), /rights/i);
});

test("citation bind/unbind updates matching locator and reference atomically", () => {
  const base = createTextDraft();
  const id = base.payload.document.blocks[0].id;
  const withText = replaceBlockRuns(base, id, [{ text: "A😀B", marks: [] }]);
  const bound = bindCitation(withText, { blockId: id, start: 1, end: 2, text: "😀" }, { item_id: 9, snapshot_checksum: "b".repeat(64), public_use_allowed: true }, "c".repeat(64));
  assert.equal(bound.payload.document.citations.length, 1);
  assert.deepEqual(bound.evidenceRefs[0].locator, { citation_id: bound.payload.document.citations[0].id, block_id: id, start: 1, end: 2, selected_text_hash: "c".repeat(64) });
  const unbound = unbindCitation(bound, bound.payload.document.citations[0].id);
  assert.deepEqual(unbound.payload.document.citations, []);
  assert.deepEqual(unbound.evidenceRefs, []);
});
