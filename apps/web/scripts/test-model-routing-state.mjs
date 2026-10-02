import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

const source = await readFile(new URL("../src/product/modelRoutingState.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
const { retargetPlugin } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
const original = { enabled: true, capability: "image_generation", model_profile_id: "google", registry_key: "google.native", registry_version: "1" };
const profiles = { xai: { capability_bindings: { image_generation: { adapter_key: "xai.native", adapter_version: "1" } } } };
const next = retargetPlugin(original, "xai", profiles);
assert.equal(next.model_profile_id, "xai");
assert.equal(next.registry_key, "xai.native");
assert.equal(next.enabled, true);
assert.equal(original.registry_key, "google.native");
assert.equal(retargetPlugin(original, "", profiles).registry_key, null);
console.log("Model routing plugin state: PASS");
