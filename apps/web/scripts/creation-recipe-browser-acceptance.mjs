import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { createRequire } from "node:module";

const { chromium } = createRequire(import.meta.url)("playwright");

assert.equal(process.env.CREATION_RECIPE_ISOLATED, "yes", "Use the dedicated Mock API, never the formal database");
assert.equal(process.env.CREATION_RECIPE_API, "http://127.0.0.1:18331/api/v1");
const apiUrl = process.env.CREATION_RECIPE_API;
const ui = "http://127.0.0.1:15331";
const artifacts = mkdtempSync(join(tmpdir(), "aicontent-recipe-browser-"));
const report = { artifacts, gates: [], pageErrors: [], runCalls: 0 };
async function api(path, data) {
  const response = await fetch(`${apiUrl}${path}`, { method: data === undefined ? "GET" : "POST",
    headers: { "X-Studio-User": "recipe@studio.test", "Content-Type": "application/json" },
    body: data === undefined ? undefined : JSON.stringify(data) });
  assert(response.ok, `${path}: ${response.status} ${await response.clone().text()}`);
  return response.json();
}
const persona = await api("/content-personas", { name: "隔离浏览器作者" });
const project = await api("/content-projects", { title: "Creation Recipe 隔离验收" });
const unit = await api(`/content-projects/${project.id}/units`, { title: "文章", persona_id: persona.id, modality: "text" });
const base = `/content-projects/${project.id}/units/${unit.id}`;
await api(`${base}/workflow-override`, { expected_revision: 0, definition: {
  nodes: ["outline", "draft"].map((id, index) => ({ id, kind: "AI", plugin: "stage.master.propose", plugin_version: "1",
    stage_schema: "stage.master.propose.v1", config: { instruction: index ? "从已接受大纲形成初稿" : "生成有结构的内容大纲", candidate_count: index ? 1 : 3, length: "short" } })),
  edges: [{ from: "outline", to: "draft" }], visual_order: ["outline", "draft"],
} });
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true, args: ["--no-proxy-server"] });
const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
const page = await context.newPage();
page.on("pageerror", error => report.pageErrors.push(error.message));
page.on("dialog", dialog => dialog.accept());
page.on("request", request => { if (request.method() === "POST" && /creation-recipe\/stages\/[^/]+\/run$/.test(new URL(request.url()).pathname)) report.runCalls += 1; });
await context.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
await context.addInitScript(() => localStorage.setItem("studio-user", "recipe@studio.test"));
try {
  await page.goto(`${ui}/projects/${project.id}/units/${unit.id}/production`);
  let recipe = page.getByRole("region", { name: "Creation Recipe 创作流程" });
  await recipe.getByRole("button", { name: "准备本次运行（不调用模型）" }).click();
  await recipe.getByRole("button", { name: "执行本阶段", exact: true }).waitFor();
  const instruction = recipe.locator("textarea").first();
  await instruction.fill("减少科普解释，重点讨论架构价值");
  await recipe.getByRole("button", { name: "预览实际请求", exact: true }).click();
  await recipe.getByText("实际将发送给 AI 的内容", { exact: true }).waitFor();
  await recipe.getByRole("tab").nth(0).focus();
  await page.keyboard.press("ArrowRight");
  assert.equal(await recipe.getByRole("tab").nth(1).getAttribute("aria-selected"), "true");
  await page.keyboard.press("ArrowLeft");
  assert.equal(await instruction.inputValue(), "减少科普解释，重点讨论架构价值");
  await instruction.fill("只讲架构价值，并给出清晰边界");
  assert.equal(await recipe.getByText("实际将发送给 AI 的内容", { exact: true }).count(), 0);
  report.gates.push("per_stage_override_and_preview_invalidation");
  report.gates.push("keyboard_stage_navigation");
  await recipe.getByRole("button", { name: "预览实际请求", exact: true }).click();
  await recipe.locator("summary").filter({ hasText: "完整 System / User Prompt" }).click();
  await recipe.getByText("模型：mock", { exact: false }).waitFor();
  await recipe.getByRole("button", { name: "执行本阶段", exact: true }).click();
  let review = recipe.getByLabel("阶段候选审阅");
  await review.getByRole("button", { name: /^候选 3/ }).waitFor();
  assert.equal(report.runCalls, 1);
  assert.equal((await api(`${base}/master-revisions`)).items.length, 0);
  report.gates.push("generate_three_proposals_without_master_write");
  let releaseRead;
  let announceRead;
  const readHeld = new Promise(resolve => { releaseRead = resolve; });
  const readStarted = new Promise(resolve => { announceRead = resolve; });
  await page.route("**/creation-recipe/stages/*/result?*", async route => {
    announceRead();
    await readHeld;
    await route.continue();
  });
  await page.reload();
  recipe = page.getByRole("region", { name: "Creation Recipe 创作流程" });
  await readStarted;
  assert.equal(await recipe.getByRole("button", { name: "预览实际请求", exact: true }).isEnabled(), false,
    "A delayed original-result read must block Preview/new execution");
  assert.equal(report.runCalls, 1);
  releaseRead();
  review = recipe.getByLabel("阶段候选审阅");
  await review.getByRole("button", { name: /^候选 3/ }).waitFor();
  await page.unroute("**/creation-recipe/stages/*/result?*");
  report.gates.push("delayed_readback_blocks_new_execution");
  assert.equal(report.runCalls, 1, "Reload must read the original Attempt, not rerun");
  report.gates.push("remount_recovers_original_candidates_without_dispatch");
  await page.route("**/creation-recipe/stages/*/result?*", route => route.fulfill({ status: 503,
    contentType: "application/json", body: JSON.stringify({ detail: { code: "stage_result_read_unavailable" } }) }));
  await page.reload();
  recipe = page.getByRole("region", { name: "Creation Recipe 创作流程" });
  await recipe.getByText("503 · stage_result_read_unavailable", { exact: true }).waitFor();
  assert.equal(await recipe.getByRole("button", { name: "预览实际请求", exact: true }).isEnabled(), false,
    "Failed readback cannot silently enable a new invocation");
  assert.equal(report.runCalls, 1);
  await page.unroute("**/creation-recipe/stages/*/result?*");
  await recipe.getByRole("button", { name: "回读原尝试（不重发）", exact: true }).click();
  review = recipe.getByLabel("阶段候选审阅");
  await review.getByRole("button", { name: /^候选 3/ }).waitFor();
  assert.equal(report.runCalls, 1);
  report.gates.push("failed_readback_requires_exact_read_only_recovery");
  await review.getByRole("button", { name: /^候选 2/ }).click();
  await review.getByRole("textbox", { name: "Text Master 标题", exact: true }).fill("浏览器人工修改后采用");
  await page.getByRole("textbox", { name: "Text Master 标题", exact: true }).last().fill("独立母版未保存编辑");
  await review.getByRole("button", { name: "接受为 Content Master", exact: true }).click();
  await review.getByText(/已接受为 Master #/).waitFor();
  const masters = (await api(`${base}/master-revisions`)).items;
  assert.equal(masters.length, 1);
  assert.equal(masters[0].payload.title, "浏览器人工修改后采用");
  assert.equal(masters[0].edit_summary.stage_provenance.decision, "accepted_with_edits");
  assert.equal(await page.getByRole("textbox", { name: "Text Master 标题", exact: true }).last().inputValue(), "独立母版未保存编辑");
  report.gates.push("explicit_adoption_and_independent_master_dirty_state");
  await recipe.getByRole("tab").nth(1).click();
  await recipe.locator('[aria-label="阶段候选审阅"]:visible').getByRole("button", { name: /^候选 1/ }).waitFor();
  const read = await api(`${base}/creation-recipe`);
  const next = read.stages.find(stage => stage.node_id === "draft");
  assert.equal(next.status, "waiting_input");
  const nextResult = await api(`${base}/creation-recipe/stages/draft/result?run_id=${read.run_id}&attempt_id=${next.last_attempt.id}`);
  assert.equal(nextResult.receipt.request_mode, "automatic");
  assert.equal(nextResult.resolved_stage.upstream.outline.payload.title, masters[0].payload.title);
  assert.equal(report.runCalls, 1, "Automatic successor is server-owned, not a browser retry");
  assert.equal((await api(`${base}/master-revisions`)).items.length, 1, "Next proposal is not automatically adopted");
  report.gates.push("accepted_commit_auto_successor_stops_for_review");
  await page.reload();
  await page.getByRole("region", { name: "Creation Recipe 创作流程" }).getByText(/已提交 Master v1 · 浏览器人工修改后采用/).waitFor();
  assert.equal(report.runCalls, 1, "Accepted readback must not dispatch again");
  report.gates.push("accepted_master_revision_readback");
  await page.screenshot({ path: join(artifacts, "recipe-result-review.png"), fullPage: true });
  assert.deepEqual(report.pageErrors, []);
  console.log(JSON.stringify(report));
} finally {
  writeFileSync(join(artifacts, "report.json"), JSON.stringify(report, null, 2));
  await browser.close();
}
