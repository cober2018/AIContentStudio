import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

assert.equal(process.env.F7_ISOLATED_ACCEPTANCE, "yes");
assert.equal(process.env.F7_BROWSER_URL, "http://127.0.0.1:15671");
assert.match(process.env.F7_ACCEPTANCE_DB || "", /^sqlite:\/\/\/\/tmp\/aicontent-f7-media\.[^/]+\/studio\.db$/);
const { chromium } = createRequire(import.meta.url)("playwright");
const ui = process.env.F7_BROWSER_URL;
const headers = { "X-Studio-User": "admin@studio.local" };
const artifacts = mkdtempSync(join(tmpdir(), "aicontent-f7-graphic-browser-"));
const report = { artifacts, evidence: "actual explicitly configured local Chromium renderer; manual acceptance, no external Provider or capability verification", gates: [], pageErrors: [] };
const browser = await chromium.launch({ headless: true, channel: "chrome", chromiumSandbox: true });
const page = await browser.newPage();
page.on("pageerror", error => report.pageErrors.push(error.message));
async function api(path, data) {
  const response = data === undefined ? await page.request.get(`${ui}/api/v1${path}`, { headers }) : await page.request.post(`${ui}/api/v1${path}`, { headers, data });
  assert(response.ok(), `${path}: ${response.status()} ${await response.text()}`);
  return response.json();
}
try {
  const persona = await api("/content-personas", { name: "Graphic renderer author" });
  const project = await api("/content-projects", { title: "Graphic render browser acceptance" });
  const unit = await api(`/content-projects/${project.id}/units`, { title: "Graphic", modality: "graphic", persona_id: persona.id,
    channel_id: "xiaohongshu", content_form: "image_note" });
  await api(`/content-projects/${project.id}/brief/revisions`, { objective: "Explicit isolated graphic acceptance", expected_revision: 0 });
  const pack = await api("/fact-packs", { name: "Explicit graphic opinion boundary" });
  await api(`/fact-packs/${pack.id}/items`, { evidence_kind: "author_opinion", snapshot: { excerpt: "An original red rectangle", attribution: "Isolated graphic author", source_locator: "manual:isolated-graphic" }, public_use_allowed: true });
  await api(`/fact-packs/${pack.id}/freeze`, {});
  await api(`/content-projects/${project.id}/fact-boundary`, { fact_pack_id: pack.id, expected_revision: 0 });
  const path = `/content-projects/${project.id}/units/${unit.id}/master-revisions`;
  const initial = await api(path, { payload_schema: "graphic.master.v2", idempotency_key: "graphic-render-initial",
    payload: { title: "Real PNG", canvases: [{ id: "cover", order: 0, width: 64, height: 64, role: "cover",
      background: { color: "#ffffff" }, layers: [{ id: "rectangle", order: 0, type: "shape", shape: "rectangle",
        x: 8, y: 8, width: 32, height: 32, fill: "#ff0000" }] }] } });
  await page.goto(`${ui}/projects/${project.id}/units/${unit.id}/production`);
  const panel = page.getByRole("region", { name: "图文渲染预览", exact: true });
  const probe = panel.getByRole("button", { name: "渲染当前已保存画布", exact: true });
  await probe.waitFor({ timeout: 10000 });
  await page.waitForFunction(() => [...document.querySelectorAll('button')].some(button => button.textContent === '渲染当前已保存画布' && !button.disabled));
  assert.equal(await probe.isDisabled(), false);
  await probe.click();
  const preview = panel.getByRole("region", { name: "渲染预览与接受", exact: true });
  await preview.getByAltText("未入库的渲染预览").waitFor({ timeout: 30000 });
  assert.equal((await api(path)).items.length, 1);
  assert.equal((await api(`/content-projects/${project.id}/shared-assets`)).length, 0);
  report.gates.push("actual selected-canvas PNG preview writes neither Master nor library material");
  await preview.getByLabel("素材标题", { exact: true }).fill("Actual browser rendered PNG");
  await preview.getByLabel("你已核对的许可", { exact: true }).selectOption("owned");
  await preview.getByLabel("许可依据文件 SHA256（不上传原文或秘密）", { exact: true }).fill("b".repeat(64));
  await preview.getByLabel("允许公开使用", { exact: true }).check();
  await preview.getByLabel("我已看过媒体并核对", { exact: false }).check();
  let accepts = 0;
  page.on("request", request => { if (request.url().endsWith("/accept") && request.method() === "POST") accepts += 1; });
  await page.route(`**/api/v1/content-projects/${project.id}/shared-assets`, route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"isolated read failure"}' }));
  const acceptance = page.waitForResponse(response => response.url().endsWith("/accept") && response.request().method() === "POST");
  await preview.getByRole("button", { name: "明确接受并保存素材版本", exact: true }).click();
  const acceptedResponse = await acceptance;
  assert.equal(acceptedResponse.status(), 201);
  const accepted = await acceptedResponse.json();
  await preview.getByRole("status").waitFor();
  await panel.getByRole("button", { name: "重新读取已接受的项目素材（不重复接受）", exact: true }).waitFor();
  assert.equal(await preview.getByRole("button", { name: "明确接受并保存素材版本", exact: true }).count(), 0);
  assert.equal(await panel.getByRole("button", { name: "将接受的图片绑定到当前画布（仅本地）", exact: true }).count(), 0);
  await page.unroute(`**/api/v1/content-projects/${project.id}/shared-assets`);
  await panel.getByRole("button", { name: "重新读取已接受的项目素材（不重复接受）", exact: true }).click();
  await panel.getByRole("button", { name: "将接受的图片绑定到当前画布（仅本地）", exact: true }).waitFor();
  assert.equal(accepts, 1);
  report.gates.push("accept succeeds but projection read fails: retained accepted state, explicit reread, no duplicate accept");
  assert.equal((await api(path)).items.length, 1);
  const assets = await api(`/content-projects/${project.id}/shared-assets`);
  assert.equal(assets.length, 1);
  assert.equal(assets[0].material_revision_id, accepted.material_revision_id);
  report.gates.push("explicit rights acceptance saves exact project asset without Master write");
  await panel.getByRole("button", { name: "将接受的图片绑定到当前画布（仅本地）", exact: true }).click();
  assert.equal((await api(path)).items.length, 1);
  assert(await probe.isDisabled());
  report.gates.push("explicit local bind marks dirty, blocks further probes and does not save Master");
  await page.getByRole("button", { name: "保存内容 Master", exact: true }).click();
  await page.getByRole("button", { name: "Master v2 · 当前", exact: true }).waitFor();
  const second = (await api(path)).items[0];
  assert.equal(second.payload.render_asset_ref[0].material_revision_id, accepted.material_revision_id);
  assert.equal(second.assets[0].content_hash, assets[0].content_hash);
  report.gates.push("explicit durable save stores render ref and exact hash in append-only revision");
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "确认当前渲染并保存新修订", exact: true }).click();
  await page.getByRole("button", { name: "Master v3 · 当前", exact: true }).waitFor();
  const third = (await api(path)).items[0];
  assert.equal(third.edit_summary.render_attestation.origin, "manual");
  assert.equal(third.edit_summary.render_attestation.confirmed, true);
  await page.reload();
  await page.getByText(new RegExp(`^Master #${third.id} · graphic.master.v2`)).waitFor();
  assert.equal((await api(path)).items.length, 3);
  report.gates.push("manual confirmation and reload preserve exact real output, never automatic verified");
  await page.getByRole("button", { name: "Master v1 · 历史", exact: true }).click();
  assert(await probe.isDisabled());
  assert.equal(initial.payload_hash, (await api(path)).items.find(item => item.id === initial.id).payload_hash);
  report.gates.push("historical view disables renderer and keeps original revision immutable");
  await page.getByRole("button", { name: "Master v3 · 当前", exact: true }).click();
  let releaseRender;
  const release = new Promise(resolve => { releaseRender = resolve; });
  let renderStarted;
  const started = new Promise(resolve => { renderStarted = resolve; });
  let renderCompleted;
  const completed = new Promise(resolve => { renderCompleted = resolve; });
  await page.route("**/media-render-previews", async route => {
    const response = await route.fetch();
    renderStarted();
    await release;
    await route.fulfill({ response });
    renderCompleted();
  });
  await probe.click();
  await started;
  await page.getByLabel("图文标题", { exact: true }).fill("Unsaved change");
  releaseRender();
  await completed;
  await page.unroute("**/media-render-previews");
  assert(await probe.isDisabled());
  assert.equal(await panel.getByRole("region", { name: "渲染预览与接受", exact: true }).count(), 0);
  assert.equal((await api(path)).items.length, 3);
  report.gates.push("unsaved title prevents rendering the wrong saved base");
  report.gates.push("actual in-flight render completing after local edit cannot restore stale preview or controls");
  await page.screenshot({ path: join(artifacts, "graphic-render-dirty.png"), fullPage: true });
  const dbPath = process.env.F7_ACCEPTANCE_DB.replace('sqlite:///', '');
  execFileSync('sqlite3', [dbPath, "UPDATE user SET role='viewer' WHERE email='admin@studio.local';"]);
  try {
    await page.reload();
    await panel.getByText("仅管理员可探测", { exact: false }).waitFor();
    assert(await probe.isDisabled());
    assert.equal((await api(path)).items.length, 3);
    report.gates.push("same owner viewer may read saved history but cannot request rendering");
  } finally {
    execFileSync('sqlite3', [dbPath, "UPDATE user SET role='admin' WHERE email='admin@studio.local';"]);
  }
  assert.deepEqual(report.pageErrors, []);
} catch (error) {
  await page.screenshot({ path: join(artifacts, "failure.png"), fullPage: true });
  writeFileSync(join(artifacts, "failure.txt"), `${error}\n${await page.locator('body').innerText()}`);
  console.error(`Acceptance evidence: ${artifacts}`);
  throw error;
} finally {
  writeFileSync(join(artifacts, "report.json"), JSON.stringify(report, null, 2));
  await browser.close();
}
console.log(JSON.stringify(report));
