import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

assert.equal(process.env.F7_ISOLATED_ACCEPTANCE, "yes");
assert.equal(process.env.F7_BROWSER_URL, "http://127.0.0.1:15671");
assert.match(process.env.F7_ACCEPTANCE_DB || "", /^sqlite:\/\/\/\/tmp\/aicontent-f7-media\.[^/]+\/studio\.db$/);
const { chromium } = createRequire(import.meta.url)("playwright");
const ui = process.env.F7_BROWSER_URL;
const headers = { "X-Studio-User": "admin@studio.local" };
const artifacts = mkdtempSync(join(tmpdir(), "aicontent-f7-renderer-browser-"));
const report = { artifacts, evidence: "actual local deterministic Text renderer; no provider fixture or remote effect invoked", gates: [], pageErrors: [] };
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const page = await browser.newPage();
page.on("pageerror", error => report.pageErrors.push(error.message));
async function api(path, data) {
  const response = data === undefined ? await page.request.get(`${ui}/api/v1${path}`, { headers }) : await page.request.post(`${ui}/api/v1${path}`, { headers, data });
  assert(response.ok(), `${path}: ${response.status()} ${await response.text()}`);
  return response.json();
}
try {
  const persona = await api("/content-personas", { name: "Renderer browser author" });
  const project = await api("/content-projects", { title: "Renderer browser project" });
  const unit = await api(`/content-projects/${project.id}/units`, { title: "Text", modality: "text", persona_id: persona.id, channel_id: "wechat" });
  const path = `/content-projects/${project.id}/units/${unit.id}/master-revisions`;
  const initial = await api(path, { payload_schema: "text.master.v1", idempotency_key: "renderer-browser-v1", payload: { markdown: "## 原文不改写\n\n真实本地渲染" } });
  await page.goto(`${ui}/projects/${project.id}/units/${unit.id}/production`);
  const panel = page.getByRole("region", { name: "文字渲染验证", exact: true });
  await panel.getByRole("button", { name: "实际渲染并验证", exact: true }).click();
  await panel.getByText("当前精确范围已验证", { exact: true }).waitFor();
  assert.equal((await api(path)).items.length, 1);
  assert.equal((await api(path)).items[0].payload_hash, initial.payload_hash);
  report.gates.push("actual v1 render verifies safe exact scope without Master write");
  await page.reload();
  await panel.getByText("当前精确范围已验证", { exact: true }).waitFor();
  report.gates.push("refresh reads persistent verification without implicit probe");
  page.once("dialog", dialog => dialog.accept());
  await panel.getByRole("button", { name: "撤销渲染验证", exact: true }).click();
  await panel.getByText("当前精确范围尚未验证 / 已失效", { exact: true }).waitFor();
  assert.equal((await api(path)).items.length, 1);
  report.gates.push("explicit revocation is durable and content remains immutable");
  const preview = await api(`${path}/${initial.id}/text-v2-upgrade-preview`);
  const current = await api(`${path}/${initial.id}/text-v2-upgrade`, { expected_revision: 1,
    expected_payload_hash: preview.source_payload_hash, expected_context_hash: preview.current_context_hash, idempotency_key: "renderer-browser-upgrade" });
  await page.reload();
  await panel.getByText(/text.studio.document.v1/).waitFor();
  await panel.getByRole("button", { name: "实际渲染并验证", exact: true }).click();
  await panel.getByText("当前精确范围已验证", { exact: true }).waitFor();
  assert.equal((await api(path)).items.length, 2);
  assert.equal((await api(path)).items[0].payload_hash, current.payload_hash);
  report.gates.push("actual v2 structured render verifies independently without extra revision");
  await page.getByRole("button", { name: "Master v1 · 历史", exact: true }).click();
  await panel.getByRole("button", { name: "实际渲染并验证", exact: true }).waitFor();
  assert(await panel.getByRole("button", { name: "实际渲染并验证", exact: true }).isDisabled());
  report.gates.push("historical Master disables probe; prior text remains viewable");
  await page.goto(`${ui}/settings`);
  await page.getByRole("navigation", { name: "设置分区" }).getByRole("button", { name: "渠道", exact: true }).click();
  await page.getByRole("heading", { name: "渲染能力（只读清单）", exact: true }).waitFor();
  assert.equal(await page.getByText("人工成片；自动渲染不可用", { exact: true }).count(), 4);
  assert.equal((await api(path)).items.length, 2);
  report.gates.push("Settings reports Graphic/Video manual-only, never fake verified auto renderer");
  assert.deepEqual(report.pageErrors, []);
  await page.screenshot({ path: join(artifacts, "renderer-inventory.png"), fullPage: true });
} finally {
  writeFileSync(join(artifacts, "report.json"), JSON.stringify(report, null, 2));
  await browser.close();
}
console.log(JSON.stringify(report));
