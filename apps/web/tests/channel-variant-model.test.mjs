import test from "node:test";
import assert from "node:assert/strict";
import { descriptorIssue, setAtPath, changeList, newListItem, fieldsForObject } from "../src/product/ChannelVariantModel.ts";

const text = (path, required = true) => ({ path, type: "string", required, max_length: 10000, default: "" });
const ordered = (path) => [{ ...text(`${path}.id`), readonly: true }, { path: `${path}.order`, type: "integer", required: true, readonly: true, minimum: 0 }];
const paragraph = { id: ordered("blocks[]")[0], order: ordered("blocks[]")[1], kind: { ...text("blocks[].kind"), enum: ["paragraph"], default: "paragraph" }, text: text("blocks[].text") };
const list = { ...paragraph, kind: { ...paragraph.kind, enum: ["list"], default: "list" }, text: undefined, ordered: { path: "blocks[].ordered", type: "boolean", default: false }, items: { path: "blocks[].items", type: "list", min_items: 1, max_items: 250, ordered: true, unique_ids: true, item: { path: "blocks[].items[]", type: "object", fields: [...ordered("blocks[].items[]"), text("blocks[].items[].text")] } } };
delete list.text;
const descriptor = { schema_id: "x.articles.v1", descriptor_version: 1, fields: [text("title"), { path: "blocks", type: "list", required: true, min_items: 1, max_items: 250, ordered: true, unique_ids: true, item: { path: "blocks[]", type: "object", discriminator: "kind", variants: { paragraph, list } } }, { path: "citations", type: "list", readonly: true, item: { path: "citations[]", type: "object", additional_fields: true, fields: [] } }], additional_fields: false };
const body = { title: "原标题", blocks: [{ id: "paragraph-1", order: 0, kind: "paragraph", text: "A😀B" }, { id: "list-1", order: 1, kind: "list", ordered: false, items: [{ id: "item-1", order: 0, text: "列表正文" }] }], citations: [{ id: "cite-1", location_id: "paragraph-1", fact_pack_item_id: 7, snapshot_checksum: "a".repeat(64), locator: { start: 1, end: 2 } }] };

test("nested typed editing preserves IDs, order and exact citations", () => {
  const edited = setAtPath(body, ["blocks", 1, "items", 0, "text"], "修改列表正文");
  assert.equal(edited.blocks[1].items[0].id, "item-1");
  assert.equal(edited.blocks[1].items[0].order, 0);
  assert.equal(edited.blocks[1].items[0].text, "修改列表正文");
  assert.strictEqual(edited.citations, body.citations);
  assert.equal(descriptorIssue(descriptor, edited), "");
  assert.equal(body.blocks[1].items[0].text, "列表正文");
});

test("unknown payload or descriptor fields block save without dropping data", () => {
  const extended = { ...body, internal: { important: "keep" } };
  assert.match(descriptorIssue(descriptor, extended), /internal/);
  assert.equal(extended.internal.important, "keep");
  assert.match(descriptorIssue({ ...descriptor, fields: [...descriptor.fields, { path: "future", type: "future", required: true }] }, { ...body, future: "keep" }), /future/);
});

test("nested validation reports the exact path and counts Unicode code points", () => {
  assert.match(descriptorIssue(descriptor, setAtPath(body, ["blocks", 1, "items", 0, "text"], "")), /blocks\[1\].items\[0\].text/);
  assert.match(descriptorIssue(descriptor, setAtPath(body, ["blocks", 0, "text"], "A")), /citations\[0\]/);
  assert.equal(descriptorIssue(descriptor, body), "");
  assert.match(descriptorIssue(descriptor, setAtPath(body, ["blocks", 1, "ordered"], "false")), /blocks\[1\].ordered/);
});

test("safe list edits retain stable identity; deleting cited or media rows is blocked", () => {
  const reordered = changeList(body, ["blocks"], descriptor.fields[1], "move", 1, 0);
  assert.deepEqual(reordered.blocks.map(row => [row.id, row.order]), [["list-1", 0], ["paragraph-1", 1]]);
  assert.strictEqual(reordered.citations, body.citations);
  assert.throws(() => changeList(body, ["blocks"], descriptor.fields[1], "remove", 0), /引用/);
  const deleted = changeList(body, ["blocks"], descriptor.fields[1], "remove", 1);
  assert.equal(deleted.blocks[0].id, "paragraph-1");
  const withMedia = { ...body, blocks: [...body.blocks, { id: "image-1", order: 2, kind: "image", image_ref_key: "slot-1" }] };
  assert.throws(() => changeList(withMedia, ["blocks"], descriptor.fields[1], "remove", 2), /素材/);
});

test("new nested list items use descriptor defaults and new stable IDs", () => {
  const row = newListItem(descriptor.fields[1], "list");
  assert.equal(row.kind, "list");
  assert.equal(row.ordered, false);
  assert.equal(row.items.length, 1);
  assert.notEqual(row.id, row.items[0].id);
  assert.equal(row.items[0].order, 0);
  assert.ok(fieldsForObject(descriptor.fields[1].item, row).some(field => field.path === "blocks[].items"));
});

test("optional omitted lists can be explicitly started without mutating the original payload", () => {
  const field = { path: "tags", type: "list", default: [], min_items: 0, max_items: 50, unique_values: true, item: text("tags[]") };
  const changed = changeList(body, ["tags"], field, "add");
  assert.deepEqual(changed.tags, [""]);
  assert.equal("tags" in body, false);
});

test("cited text changes block save while edits outside the citation retain the exact link", () => {
  const altered = setAtPath(body, ["blocks", 0, "text"], "A日B");
  assert.match(descriptorIssue(descriptor, altered, body), /citations\[0\].*引用文字/);
  const appended = setAtPath(body, ["blocks", 0, "text"], "A😀B附加说明");
  assert.equal(descriptorIssue(descriptor, appended, body), "");
  assert.strictEqual(appended.citations, body.citations);
});

test("exact media lists reject additions before creating dangling empty slots", () => {
  const media = { path: "images", type: "list", default: [], max_items: 20, ordered: true, item: { path: "images[]", type: "object", fields: [...ordered("images[]"), { path: "images[].image_ref_key", type: "media_ref", required: true, default: "" }] } };
  assert.throws(() => changeList(body, ["images"], media, "add"), /精确素材/);
  assert.equal("images" in body, false);
  const bRoll = { path: "b_roll_ref_keys", type: "list", default: [], max_items: 20, item: { path: "b_roll_ref_keys[]", type: "media_ref", required: true, default: "" } };
  assert.throws(() => changeList(body, ["b_roll_ref_keys"], bRoll, "add"), /精确素材/);
  assert.equal("b_roll_ref_keys" in body, false);
});
