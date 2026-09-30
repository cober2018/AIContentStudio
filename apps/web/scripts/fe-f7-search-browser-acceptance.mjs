import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

assert.equal(process.env.F7_ISOLATED_ACCEPTANCE, "yes");
assert.equal(process.env.F7_BROWSER_URL, "http://127.0.0.1:15671");
assert.match(process.env.F7_ACCEPTANCE_DB || "", /^sqlite:\/\/\/\/tmp\/aicontent-f7-media\.[^/]+\/studio\.db$/);
const { chromium } = createRequire(import.meta.url)("playwright");
const artifacts = mkdtempSync(join(tmpdir(), "aicontent-f7-search-browser-"));
const report = { artifacts, evidence: "isolated search/PNG fixture; not real Wikimedia verification", gates: [], pageErrors: [] };
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const page = await browser.newPage();
page.on("pageerror", (error) => report.pageErrors.push(error.message));
const ui = process.env.F7_BROWSER_URL;
const headers = { "X-Studio-User": "admin@studio.local" };
async function api(path, data) {
  const response = data === undefined ? await page.request.get(`${ui}/api/v1${path}`, { headers }) : await page.request.post(`${ui}/api/v1${path}`, { headers, data });
  assert(response.ok(), `${path}: ${response.status()} ${await response.text()}`);
  return response.json();
}
try {
  const project = await api("/content-projects", { title: "搜索素材跨 Unit 验收" });
  const materialTitle = `F7 已接受搜索素材 ${project.id}`;
  const persona = await api("/content-personas", { name: "共享素材作者" });
  await page.goto(`${ui}/assets`);
  const before = await page.request.get(`${ui}/api/v1/system-library?type=material`, { headers });
  const count = (await before.json()).items.length;
  await page.getByRole("button", { name: "公共素材搜索与导入", exact: true }).click();
  const search = page.getByRole("region", { name: "公共素材搜索", exact: true });
  await search.getByLabel("公共素材关键词", { exact: true }).fill("fixture");
  await search.getByLabel("同时引用到项目 ID（可选）", { exact: true }).fill(String(project.id));
  await search.getByRole("button", { name: "明确搜索公共素材", exact: true }).click();
  await search.getByRole("heading", { name: "F7 搜索候选", exact: true }).waitFor();
  const afterSearch = await page.request.get(`${ui}/api/v1/system-library?type=material`, { headers });
  assert.equal((await afterSearch.json()).items.length, count);
  report.gates.push("explicit search returns safe candidates with no durable material");
  await search.getByRole("button", { name: "下载临时预览", exact: true }).click();
  const preview = page.getByRole("region", { name: "素材预览与接受", exact: true });
  await preview.getByAltText("未入库的生成预览").waitFor();
  assert.equal(await preview.getByLabel("你已核对的许可", { exact: true }).inputValue(), "CC-BY-4.0");
  assert.equal(await preview.getByLabel("你已核对的许可", { exact: true }).isDisabled(), true);
  assert.equal(await preview.getByLabel("署名 / 来源说明（CC BY 必填）", { exact: true }).inputValue(), "Fixture Author");
  assert.equal(await preview.getByRole("button", { name: "明确接受并保存素材版本", exact: true }).isDisabled(), true);
  report.gates.push("explicit selection downloads preview; observed license/attribution locked and rights unconfirmed");
  await preview.getByLabel("素材标题", { exact: true }).fill(materialTitle);
  await preview.getByLabel("允许公开使用", { exact: true }).check();
  await preview.getByLabel("我已看过媒体并核对", { exact: false }).check();
  const accepted = page.waitForResponse((response) => response.url().endsWith("/accept") && response.request().method() === "POST");
  await preview.getByRole("button", { name: "明确接受并保存素材版本", exact: true }).click();
  const response = await accepted;
  assert.equal(response.status(), 201);
  const result = await response.json();
  await preview.getByRole("status").waitFor();
  const detail = await page.request.get(`${ui}/api/v1/materials/${result.material_id}`, { headers });
  const revision = (await detail.json()).latest_revision;
  assert.equal(revision.source_kind, "web_search");
  assert.equal(revision.attribution_text, "Fixture Author");
  assert.equal(revision.source_url, "https://commons.wikimedia.org/wiki/File:Fixture.png");
  assert.equal(revision.public_use_allowed, true);
  assert.equal(revision.model_use_allowed, false);
  report.gates.push("accept creates exact web_search revision, attribution and explicit rights only");
  await page.reload();
  await page.getByRole("button").filter({ hasText: materialTitle }).waitFor();
  await page.screenshot({ path: join(artifacts, "accepted-search.png"), fullPage: true });
  report.gates.push("reload reads durable material without reviving temporary candidates");
  const masters = [];
  for (const modality of ["text", "video"]) {
    const unit = await api(`/content-projects/${project.id}/units`, { title: `共享 ${modality}`, modality, persona_id: persona.id });
    const payload = modality === "text" ? { document: { schema: "studio.text.document.v1", blocks: [
      { id: "body", type: "paragraph", content: [{ text: "共享素材正文", marks: [] }] },
      { id: "shared", type: "image", material_revision_id: result.material_revision_id, alt_text: "共享图片" }], citations: [] } }
      : { aspect_ratio: [9, 16], script: { blocks: [] }, shots: [], timeline: { duration_ms: 4000, tracks: [{ id: "visual", order: 0, kind: "video",
        items: [{ id: "shared", order: 0, start_ms: 0, end_ms: 4000, material_revision_id: result.material_revision_id }] }] },
      voice: { mode: "none" }, subtitles: { cues: [] }, overlays: [], music: {}, cover: {} };
    const ref = modality === "text" ? { role: "inline" } : { role: "timeline_media", slot_key: "shared", sort_order: 0,
      placement: { track_id: "visual", item_id: "shared", start_ms: 0, end_ms: 4000 } };
    const path = `/content-projects/${project.id}/units/${unit.id}/master-revisions`;
    const master = await api(path, { payload_schema: `${modality}.master.v2`, payload, idempotency_key: `shared-${modality}`,
      asset_refs: [{ material_revision_id: result.material_revision_id, content_hash: revision.content_hash, ...ref }] });
    assert.equal(master.assets[0].material_revision_id, result.material_revision_id);
    await page.goto(`${ui}/projects/${project.id}/units/${unit.id}/production`);
    await page.getByRole("region", { name: "Content Master", exact: true }).getByText(new RegExp(`^Master #${master.id} ·`)).waitFor();
    masters.push({ path, master });
  }
  assert.equal((await api(`/materials/${result.material_id}`)).revisions.length, 1);
  report.gates.push("Text image and Video timeline share one accepted exact revision; production pages reload it");
  await api(`/materials/${result.material_id}/revisions/${result.material_revision_id}/revoke-public-use`, { note: "隔离撤权验收" });
  for (const { path, master } of masters) {
    const checks = await api(`${path}/${master.id}/checks`, {});
    assert.equal(checks.items.find(row => row.check_kind === "rights").status, "blocker");
    assert.equal((await api(`${path}/${master.id}/readiness`)).candidate_freeze_available, false);
    assert.equal((await api(path)).items.length, 1);
  }
  report.gates.push("live public-use revocation blocks both Units' rights/readiness without rewriting historical Masters");
  await page.goto(`${ui}/settings`);
  const guidance = page.getByRole("region", { name: "Provider 配置指引", exact: true });
  await guidance.getByRole("heading", { name: "素材与音视频 Provider 配置指引", exact: true }).waitFor();
  assert.equal(await guidance.getByRole("button").count(), 0);
  await guidance.getByText(/已加载 \/ 配置记录不代表执行可用或真实外部验证/).waitFor();
  assert.equal((await api(`/materials/${result.material_id}`)).revisions.length, 1);
  report.gates.push("Settings Provider guidance is read-only, honest, and offers no fake Save/probe");
  assert.equal(report.pageErrors.length, 0, JSON.stringify(report.pageErrors));
  writeFileSync(join(artifacts, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} finally { await browser.close(); }
