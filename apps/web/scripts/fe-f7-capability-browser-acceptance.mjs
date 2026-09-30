import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

assert.equal(process.env.F7_ISOLATED_ACCEPTANCE, "yes");
assert.equal(process.env.F7_BROWSER_URL, "http://127.0.0.1:15670");
assert.equal(process.env.F7_BROWSER_API, "http://127.0.0.1:18270/api/v1");
assert.match(process.env.F7_ACCEPTANCE_DB || "", /^sqlite:\/\/\/\/tmp\/aicontent-f7-acceptance\.[^/]+\/studio\.db$/);
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const ui = process.env.F7_BROWSER_URL;
const apiUrl = process.env.F7_BROWSER_API;
const artifacts = mkdtempSync(join(tmpdir(), "aicontent-f7-browser-evidence-"));
const report = { artifacts, gates: [], pageErrors: [], ids: {}, publisherEvidence: "synthetic isolated operator fixture; no remote publishing" };
const headers = { "X-Studio-User": "admin@studio.local" };
async function api(path, body, method = body === undefined ? "GET" : "POST") {
  const response = await fetch(`${apiUrl}${path}`, { method, headers: { ...headers, ...(body === undefined ? {} : { "Content-Type": "application/json" }) }, body: body === undefined ? undefined : JSON.stringify(body) });
  const text = await response.text();
  assert(response.ok, `${method} ${path}: ${response.status} ${text}`);
  return text ? JSON.parse(text) : null;
}
async function clickPost(page, label, path, container = page) {
  const waiting = page.waitForResponse((response) => response.url().includes(path) && response.request().method() === "POST");
  await container.getByRole("button", { name: label, exact: true }).click();
  const response = await waiting;
  assert(response.ok(), `${label}: ${response.status()} ${await response.text()}`);
  return response.json();
}
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true, args: ["--no-proxy-server"] });
const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
const page = await context.newPage();
page.on("pageerror", (error) => report.pageErrors.push(error.message));
page.on("dialog", (dialog) => dialog.accept());
try {
  const connector = await api("/connectors", { name: "F7 public read fixture", base_url: "https://httpbin.org", auth_style: "none" });
  const endpoint = await api(`/connectors/${connector.id}/endpoints`, { name: "Slide titles", path: "/json", method: "GET", title_template: "F7 isolated public JSON",
    fact_mapping: { items_path: "slideshow.slides", statement: "{title}", fields: { value: "{title}" } } });
  await page.goto(`${ui}/settings`);
  const reads = [];
  page.on("request", (request) => { if (request.method() === "POST") reads.push(request.url()); });
  await page.getByRole("button", { name: "数据源", exact: true }).click();
  const region = page.getByRole("region", { name: "能力验证" });
  await region.getByRole("combobox", { name: "已有只读数据接口" }).selectOption(String(endpoint.id));
  assert.equal(reads.length, 0, "Reading Settings must not probe or pull");
  const capability = await clickPost(page, "保存连接配置", "/data-source-capabilities", region);
  assert.equal(capability.verified, false);
  const profileCard = region.getByRole("article").filter({ hasText: `api.endpoint.${endpoint.id} · 版本 1` });
  await profileCard.getByRole("button", { name: "执行读取并验证" }).waitFor();
  const probed = await clickPost(page, "执行读取并验证", "/probe", profileCard);
  assert.equal(probed.verified, true);
  assert(probed.facts > 0);
  const profile = (await api("/data-source-capabilities")).find((row) => row.id === capability.id);
  assert.equal(profile.executable, true);
  await page.reload();
  await page.getByRole("button", { name: "数据源", exact: true }).click();
  await profileCard.getByText("已验证，可执行", { exact: true }).waitFor();
  report.ids.capability = capability.id;
  report.gates.push("Settings configures a typed API profile, performs a real bounded public GET, and persists mapped Source/Fact plus verification across reload");

  const persona = await api("/content-personas", { name: "F7 fixture author" });
  const account = await api(`/content-personas/${persona.id}/accounts`, { name: "F7 fixture WeChat account" });
  const project = await api("/content-projects", { title: "F7 capability workflow" });
  const unit = await api(`/content-projects/${project.id}/units`, { title: "Data profile test", persona_id: persona.id, modality: "text" });
  await page.goto(`${ui}/projects/${project.id}/units/${unit.id}/production`);
  await page.getByRole("button", { name: "进入设计模式", exact: true }).click();
  await page.getByRole("combobox", { name: "新增节点类型" }).selectOption("Data");
  await page.getByRole("button", { name: "新增节点", exact: true }).click();
  await page.getByRole("combobox", { name: "API 数据连接版本" }).selectOption(profile.source_ref);
  await clickPost(page, "保存项目覆盖", "/workflow-override");
  const savedWorkflow = await api(`/content-projects/${project.id}/units/${unit.id}/effective-workflow`);
  assert.equal(savedWorkflow.definition.nodes[0].config.source_ref, profile.source_ref);
  const run = await clickPost(page, "启动真实 Run", "/runs");
  assert.equal(run.steps[0].status, "succeeded");
  assert(run.steps[0].output.snapshot_id > 0);
  report.gates.push("Production Data Node picks an exact verified profile version; saved workflow and real Run persist the Source/DataSnapshot lineage");

  await page.goto(`${ui}/settings`);
  await page.getByRole("button", { name: "渠道", exact: true }).click();
  await region.getByText("当前 WeWrite 尚不能证明实际执行账号", { exact: false }).waitFor();
  assert.equal(await region.getByRole("button", { name: "记录账号核验", exact: true }).count(), 0);
  const unavailable = await fetch(`${apiUrl}/settings/publisher-verifications`, {
    method: "POST", headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify({channel: "wechat", content_form: "article", action: "auto_draft",
      content_account_id: account.id, account_ref: "isolated-wechat-fixture",
      publisher_key: "publisher.wechat.wewrite", publisher_version: "1", result: "verified",
      reference_hash: "a".repeat(64), confirm_readback: true}),
  });
  assert.equal(unavailable.status, 409);
  await page.reload();
  await page.getByRole("button", { name: "渠道", exact: true }).click();
  await region.getByText("当前 WeWrite 尚不能证明实际执行账号", { exact: false }).waitFor();
  assert.equal((await api("/settings/capabilities")).publisher_verification_available, false);
  report.gates.push("Installed account-unbound rewriting CLI remains unavailable across reload; API rejects even synthetic operator evidence and performs no remote publish");
  await context.addInitScript(() => localStorage.setItem("studio-user", "viewer-f7@studio.local"));
  await page.evaluate(() => localStorage.setItem("studio-user", "viewer-f7@studio.local"));
  await page.reload();
  await page.getByRole("button", { name: "渠道", exact: true }).click();
  await region.getByText("当前身份尚无账号发布验证。", { exact: false }).waitFor();
  assert.equal(await region.getByRole("button", { name: "记录账号核验", exact: true }).count(), 0);
  report.gates.push("Viewer can read safe Settings inventory but cannot verify another identity's publisher account");
  assert.deepEqual(report.pageErrors, []);
  await page.screenshot({ path: join(artifacts, "settings-viewer.png"), fullPage: true });
  writeFileSync(join(artifacts, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
} finally {
  await context.close();
  await browser.close();
}
