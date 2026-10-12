import assert from "node:assert/strict";
import { existsSync, mkdtempSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { homedir, tmpdir } from "node:os";
import { createRequire } from "node:module";

const { chromium } = createRequire(import.meta.url)("playwright");

function browserExecutable() {
  if (process.env.PERSONA_TEXT_BROWSER) return process.env.PERSONA_TEXT_BROWSER;
  if (process.platform !== "darwin") return undefined;
  const cache = process.env.PLAYWRIGHT_BROWSERS_PATH || join(homedir(), "Library", "Caches", "ms-playwright");
  if (!existsSync(cache)) return undefined;
  const suffix = process.arch === "arm64" ? "mac-arm64" : "mac-x64";
  const installed = readdirSync(cache)
    .filter(name => /^chromium_headless_shell-\d+$/.test(name))
    .sort((a, b) => Number(b.split("-").at(-1)) - Number(a.split("-").at(-1)))
    .map(name => join(cache, name, `chrome-headless-shell-${suffix}`, "chrome-headless-shell"));
  return installed.find(path => existsSync(path));
}

assert.equal(process.env.PERSONA_TEXT_ISOLATED, "yes", "Never run against the formal SQLite database");
assert.equal(process.env.PERSONA_TEXT_API, "http://127.0.0.1:18331/api/v1");
const apiUrl = process.env.PERSONA_TEXT_API;
const artifacts = mkdtempSync(join(tmpdir(), "aics-persona-text-browser-"));
const report = { artifacts, gates: [], pageErrors: [], personas: [] };
async function api(path, body, method = body === undefined ? "GET" : "POST") {
  const response = await fetch(`${apiUrl}${path}`, { method,
    headers: { "X-Studio-User": "admin@studio.local", "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body) });
  assert(response.ok, `${path}: ${response.status} ${await response.clone().text()}`);
  return response.json();
}
assert.equal((await api("/settings")).llm.provider, "mock", "Browser acceptance may only call Mock");
assert.equal((await api("/content-personas")).length, 0, "Use a fresh disposable database");
const browser = await chromium.launch({ executablePath: browserExecutable(),
  headless: true, args: ["--no-proxy-server"] });
const context = await browser.newContext({ viewport: { width: 1440, height: 1050 }, acceptDownloads: true });
await context.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
await context.addInitScript(() => localStorage.setItem("studio-user", "admin@studio.local"));
const page = await context.newPage();
page.setDefaultTimeout(15000);
page.on("pageerror", error => report.pageErrors.push(error.message));
page.on("dialog", dialog => dialog.accept());
try {
  for (const [name, key] of [["AI科技研发技术博主", "starter.ai-tech-engineer.v1"], ["日常生活方式博主", "starter.lifestyle-observer.v1"]]) {
    await page.goto("http://127.0.0.1:15331/identities");
    const gallery = page.getByRole("region", { name: "内置创作角色" });
    const before = (await api("/content-personas")).length;
    await gallery.getByRole("button", { name: `预览${name}`, exact: true }).click();
    await gallery.getByText(`${name} · 蓝图预览`, { exact: true }).waitFor();
    assert.equal((await api("/content-personas")).length, before);
    await gallery.getByRole("button", { name: "确认初始化此角色", exact: true }).click();
    await page.getByText("已保存独立角色与默认流程；配置状态见就绪卡片，不代表真实成品质量已验收。已有记录和人工修改未覆盖。", { exact: true }).waitFor();
    const persona = (await api("/content-personas")).find(item => item.name === name);
    assert(persona);
    const original = (await api(`/content-personas/${persona.id}/revisions`))[0].profile;
    await page.getByRole("tab", { name: "身份", exact: true }).click();
    await page.getByRole("button", { name: "保存新修订 v2", exact: true }).click();
    await page.getByText("修订 v2 已保存，旧快照不会改变。", { exact: true }).waitFor();
    const edited = (await api(`/content-personas/${persona.id}/revisions`))[0].profile;
    assert.deepEqual(edited.text_creative_profile, original.text_creative_profile,
      "Basic identity save must preserve the separately managed creative profile");
    report.gates.push(`${key}:empty_tree_gallery_preview_and_preserved_identity_save`);
    const project = await api("/content-projects", { title: `隔离文字验收 · ${name}` });
    const unit = await api(`/content-projects/${project.id}/units`, { title: "文字全链路", modality: "text", persona_id: persona.id, channel_id: "wechat" });
    const base = `/content-projects/${project.id}/units/${unit.id}`;
    await api(`/content-projects/${project.id}/brief/revisions`, { expected_revision: 0, objective: "隔离合同验收，不代表真实模型质量" });
    const source = await api("/sources/text", { title: "隔离任务书", as_of: new Date().toISOString().slice(0, 10),
      content: "隔离验收使用 3 个初稿、2 个精修、1 个最终稿，仅为测试输入，不是现实事实。" });
    await api(`/sources/${source.id}/extract-facts`, {});
    const facts = await api(`/facts?source_id=${source.id}`);
    assert(facts.length > 0);
    await api("/facts/bulk-status", { fact_ids: facts.map(item => item.id), action: "confirm" });
    const pack = await api("/fact-packs", { name: `隔离事实包 ${persona.id}` });
    for (const fact of facts) await api(`/fact-packs/${pack.id}/items`, { fact_id: fact.id, evidence_kind: "fact", public_use_allowed: true, model_use_allowed: true });
    await api(`/fact-packs/${pack.id}/freeze`, {});
    await api(`/content-projects/${project.id}/fact-boundary`, { fact_pack_id: pack.id, expected_revision: 0 });
    await page.goto(`http://127.0.0.1:15331/projects/${project.id}/units/${unit.id}/production`);
    const recipe = page.getByRole("region", { name: "Creation Recipe 创作流程" });
    await recipe.getByRole("button", { name: "准备本次运行（不调用模型）", exact: true }).click();
    for (const node of ["evidence", "angles", "outline", "draft", "quality", "refine", "title", "final", "final_quality"]) {
      await recipe.locator(`#recipe-${project.id}-${unit.id}-${node}`).click();
      if (node === "evidence") {
        await recipe.getByRole("button", { name: "预览实际请求", exact: true }).click();
        await recipe.getByRole("button", { name: "执行本阶段", exact: true }).click();
      }
      await recipe.getByRole("button", { name: "查看本次结果", exact: true }).click();
      if (["draft", "refine", "final"].includes(node)) {
        const review = recipe.locator('[aria-label="阶段候选审阅"]:visible');
        await review.getByRole("button", { name: "接受为 Content Master", exact: true }).waitFor();
        const choices = review.getByRole("group", { name: "选择候选" }).getByRole("button");
        assert.equal(await choices.count(), node === "draft" ? 3 : node === "refine" ? 2 : 1);
        await choices.last().click();
        if (node === "final") await review.getByRole("textbox", { name: "Text Master 标题", exact: true }).fill(`${name} · 人工确认最终稿`);
        await review.getByRole("button", { name: "接受为 Content Master", exact: true }).click();
        await review.getByText(/已接受为 Master #/).waitFor();
      } else if (["quality", "final_quality"].includes(node)) {
        const review = recipe.locator('[aria-label="阶段领域结果"]:visible');
        await review.getByRole("button", { name: "确认接受本阶段结果", exact: true }).waitFor();
        assert.equal(await review.getByRole("button", { name: "确认接受本阶段结果", exact: true }).isEnabled(), false);
        for (const input of await review.locator("textarea").all()) await input.fill("人工确认隔离测试提醒，语义审查覆盖仍按报告记录。");
        await review.getByRole("checkbox").check();
        await review.getByRole("button", { name: "确认接受本阶段结果", exact: true }).click();
        await review.getByText(/已接受：/).waitFor();
      } else {
        const review = recipe.locator("section:visible").filter({ has: page.getByRole("heading", { name: "中间创作结果", exact: true }) });
        await review.getByRole("checkbox").waitFor();
        const mastersBefore = (await api(`${base}/master-revisions`)).items.length;
        await review.getByRole("checkbox").check();
        await review.getByRole("button", { name: "接受并继续下一阶段", exact: true }).click();
        await review.getByText("已接受本次中间候选，原尝试保持不变。", { exact: true }).waitFor();
        assert.equal((await api(`${base}/master-revisions`)).items.length, mastersBefore);
      }
      report.gates.push(`${key}:stage_${node}_explicit_acceptance`);
    }
    let masters = (await api(`${base}/master-revisions`)).items;
    assert.equal(masters.length, 3);
    assert.equal(masters[0].payload.title, `${name} · 人工确认最终稿`);
    assert.equal(masters[0].edit_summary.stage_provenance.decision, "accepted_with_edits");
    assert.equal(masters[0].edit_summary.stage_provenance.creative_configuration.profile.provenance.blueprint_key, key);
    await page.reload();
    assert.equal((await api(`${base}/master-revisions`)).items.length, 3);
    await page.screenshot({ path: join(artifacts, `${key}-recipe.png`), fullPage: true });
    report.gates.push(`${key}:nine_stages_explicit_adoption_warnings_provenance_reload`);
    await page.getByRole("button", { name: "重新加载 Master", exact: true }).click();
    await page.getByRole("button", { name: "冻结 Master Candidate v4", exact: true }).click();
    const candidateLink = page.getByRole("link", { name: /^审阅 Candidate #/ });
    await candidateLink.click();
    await page.getByRole("tab", { name: "交付", exact: true }).click();
    await page.getByRole("button", { name: "批准内容", exact: true }).waitFor();
    for (const input of await page.locator('textarea[aria-label^="Warning #"]').all()) await input.fill("人工确认隔离合同提醒，未将warning改成pass。");
    await page.getByRole("button", { name: "批准内容", exact: true }).click();
    await page.getByText("内容审批已记录。", { exact: true }).waitFor();
    await page.getByPlaceholder("人工发布账号标识").fill("manual-isolated");
    await page.getByRole("button", { name: "授权交付目标", exact: true }).click();
    await page.getByText("交付目标已授权；尚未发布。", { exact: true }).waitFor();
    const downloadEvent = page.waitForEvent("download");
    await page.getByRole("button", { name: /下载.*包|下载.*ZIP/ }).first().click();
    const download = await downloadEvent;
    await download.saveAs(join(artifacts, `${key}.zip`));
    await page.screenshot({ path: join(artifacts, `${key}-review.png`), fullPage: true });
    report.gates.push(`${key}:browser_candidate_v4_approval_authorization_local_zip`);
    report.personas.push({ persona_id: persona.id, project_id: project.id, unit_id: unit.id, master_id: masters[0].id, payload_hash: masters[0].payload_hash });
  }
  assert.deepEqual(report.pageErrors, []);
  console.log(JSON.stringify(report));
} finally {
  console.log(`Browser artifacts: ${artifacts}`);
  writeFileSync(join(artifacts, "report.json"), JSON.stringify(report, null, 2));
  await page.screenshot({ path: join(artifacts, "last-page.png"), fullPage: true }).catch(() => {});
  await browser.close();
}
