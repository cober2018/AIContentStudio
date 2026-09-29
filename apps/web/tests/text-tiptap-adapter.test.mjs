import test from "node:test";
import assert from "node:assert/strict";
import { runsToTiptap, tiptapToRuns } from "../src/product/TextTiptapAdapter.ts";

test("Studio runs round-trip through bounded TipTap JSON without persisting editor schema", () => {
  const runs = [{ text: "A😀", marks: [] }, { text: "bold", marks: [{ type: "bold" }] }, { text: "\nB", marks: [] }];
  assert.deepEqual(tiptapToRuns(runsToTiptap(runs)), runs);
});

test("unsupported editor nodes or marks fail closed", () => {
  assert.throws(() => tiptapToRuns({ type: "doc", content: [{ type: "table" }] }), /unsupported/i);
  assert.throws(() => tiptapToRuns({ type: "doc", content: [{ type: "paragraph", content: [{ type: "text", text: "x", marks: [{ type: "highlight" }] }] }] }), /unsupported/i);
});
