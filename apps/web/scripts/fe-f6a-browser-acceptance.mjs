import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const ui = process.env.F6A_BROWSER_URL;
const apiUrl = process.env.F6A_BROWSER_API;
assert.equal(ui, "http://127.0.0.1:15661");
assert.equal(apiUrl, "http://127.0.0.1:18261/api/v1");
assert.equal(process.env.F6A_ISOLATED_ACCEPTANCE, "yes", "Only run against the dedicated temporary database");
const artifacts = mkdtempSync(join(tmpdir(), "aicontent-f6a-browser-evidence-"));
const report = { artifacts, ui, gates: [], ids: {}, consoleErrors: [] };
console.log(`Artifacts: ${artifacts}`);
async function api(path, data, method = data === undefined ? "GET" : "POST") {
  const response = await fetch(`${apiUrl}${path}`, { method, headers: { "X-Studio-User": "admin@studio.local", ...(data === undefined ? {} : { "Content-Type": "application/json" }) }, body: data === undefined ? undefined : JSON.stringify(data) });
  const text = await response.text();
  assert(response.ok, `${method} ${path}: ${response.status} ${text}`);
  return text ? JSON.parse(text) : null;
}
const browser = await chromium.launch({ executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless: true, args: ["--no-proxy-server"] });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
const page = await context.newPage();
page.on("pageerror", (error) => report.consoleErrors.push(error.message));
page.on("dialog", (dialog) => dialog.accept());
const suffix = Date.now();
try {
  const persona = await api("/content-personas", { name: `F6A acceptance author ${suffix}` });
  await api(`/content-personas/${persona.id}/revisions`, { expected_revision: 0, profile: { positioning: "隔离验收作者", target_audience: ["产品使用者"] } });
  const project = await api("/content-projects", { title: `F6A browser ${suffix}`, objective: "本地隔离生产核心验收" });
  const pbase = `/content-projects/${project.id}`;
  await api(`${pbase}/brief/revisions`, { expected_revision: 0, objective: "验证真实 Master 保存、审核与人工交付，不操作平台" });
  const pack = await api("/fact-packs", { name: `F6A browser evidence ${suffix}` });
  await api(`/fact-packs/${pack.id}/items`, { evidence_kind: "author_opinion", snapshot: { excerpt: "此内容为作者个人观点，不是外部事实断言。", attribution: "隔离验收作者", source_locator: { type: "manual", note: "local browser acceptance" } }, public_use_allowed: true, model_use_allowed: true });
  await api(`/fact-packs/${pack.id}/freeze`, {});
  await api(`${pbase}/fact-boundary`, { expected_revision: 0, fact_pack_id: pack.id });
  const templates = await api("/templates/channel-templates");
  const template = await api(`/templates/channel-templates/clone?source_id=${templates[0].id}`, { channel: `f6a_local_video_${suffix}`, name: "隔离验收视频，非远端渠道", profile_json: { content_forms: { final: { artifact_kind: "video", publisher_candidates: ["publisher.copy"] } } } });
  await api(`/templates/channel-templates/${template.id}/status`, { status: "published" });
  report.ids.project = project.id;
  async function makeUnit(title, modality, channel) { return api(`${pbase}/units`, { title, persona_id: persona.id, modality, channel_id: channel }); }
  const units = [await makeUnit("Text manual browser", "text", "wechat"), await makeUnit("Graphic manual browser", "graphic", "xiaohongshu"), await makeUnit("Video manual browser", "video", template.channel)];
  async function upload(modality) {
    const image = modality === "graphic";
    const file = join(artifacts, image ? "render.png" : "render.mp4");
    execFileSync("/opt/homebrew/bin/ffmpeg", ["-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x4f46e5:s=320x180:r=24", ...(image ? ["-frames:v", "1"] : ["-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p"]), file]);
    const form = new FormData(); form.append("file", new Blob([readFileSync(file)], { type: image ? "image/png" : "video/mp4" }), image ? "render.png" : "render.mp4");
    const response = await fetch(`${apiUrl}/materials/upload?kind=${image ? "image" : "video"}&public_use_allowed=true&rights_status=cleared`, { method: "POST", headers: { "X-Studio-User": "admin@studio.local" }, body: form });
    assert(response.ok, await response.text().then((text) => { if (!response.ok) return text; return ""; }));
    const material = await api(`/materials?kind=${image ? "image" : "video"}`);
    const detail = await api(`/materials/${material[0].id}`);
    const revision = detail.revisions[0];
    await api(`${pbase}/materials/references`, { material_revision_id: revision.id });
    return revision;
  }
  const renders = { graphic: await upload("graphic"), video: await upload("video") };
  const route = (unit) => `${ui}/projects/${project.id}/units/${unit.id}/production`;
  const root = () => page.getByRole("region", { name: "Content Master", exact: true });
  const editor = (target, modality) => target.getByRole("textbox", { name: `${modality === "text" ? "Text" : modality === "graphic" ? "Graphic" : "Video"} Master 内容 JSON`, exact: true });
  const masterPath = (unit) => `${pbase}/units/${unit.id}/master-revisions`;
  async function current(unit) { return (await api(masterPath(unit))).items[0]; }
  async function loaded(target = page) { await target.getByRole("button", { name: "保存内容 Master", exact: true }).waitFor(); }
  async function clickAndRequest(name, fragment, target = page) {
    const response = target.waitForResponse((row) => row.url().includes(fragment) && row.request().method() === "POST");
    await target.getByRole("button", { name, exact: true }).click();
    const result = await response; assert(result.ok(), `${name}: ${result.status()} ${await result.text()}`);
    await target.getByRole("button", { name: "保存内容 Master", exact: true }).isEnabled().catch(() => false);
    return result.json();
  }
  for (const unit of units) {
    await page.goto(route(unit)); await loaded();
    const revision = renders[unit.modality];
    const payload = unit.modality === "text" ? { title: "浏览器手工文字", markdown: "# 手工内容\n\n此正文直接来自 Content Master，无 Draft / TopicBrief / MotherRevision。" } : unit.modality === "graphic" ? { title: "浏览器画布", canvases: [{ id: "canvas-a", order: 0, width: 320, height: 180 }], render_asset_ref: { material_revision_id: revision.id, canvas_id: "canvas-a" } } : { title: "浏览器视频", script: "作者口播观点", shots: [{ id: "shot-a", order: 0 }], timeline: {}, render_asset_ref: { material_revision_id: revision.id } };
    await editor(page, unit.modality).fill(JSON.stringify(payload));
    if (revision) {
      await root().getByText("精确素材与证据引用", { exact: true }).click();
      await page.getByRole("textbox", { name: "Master 素材引用 JSON", exact: true }).fill(JSON.stringify([{ material_revision_id: revision.id, content_hash: revision.content_hash, role: "render_output" }]));
    }
    await clickAndRequest("保存内容 Master", `${masterPath(unit)}`);
    await page.reload(); await loaded();
    const persisted = await current(unit); assert.equal(persisted.payload.title, payload.title); assert.equal(JSON.parse(await editor(page, unit.modality).inputValue()).title, payload.title);
    report.gates.push(`${unit.modality}: UI save, API persisted revision, browser reload`);
    report.ids[unit.modality] = { unit: unit.id, master: persisted.id };
  }
  const text = units[0];
  await page.goto(route(text)); await loaded();
  const other = await context.newPage(); other.on("dialog", (dialog) => dialog.accept());
  await other.goto(route(text)); await loaded(other);
  await editor(page, "text").fill(JSON.stringify({ title: "文字 v2", markdown: "当前编辑者的新正文" }));
  await clickAndRequest("保存内容 Master", masterPath(text));
  const ownEdit = JSON.stringify({ title: "保留冲突中的本地编辑", markdown: "不应被409覆盖" });
  await editor(other, "text").fill(ownEdit);
  const conflictResponse = other.waitForResponse((row) => row.url().includes(masterPath(text)) && row.request().method() === "POST");
  await other.getByRole("button", { name: "保存内容 Master", exact: true }).click();
  assert.equal((await conflictResponse).status(), 409);
  assert.equal(await editor(other, "text").inputValue(), ownEdit);
  await other.getByRole("button", { name: "重新加载 Master", exact: true }).click();
  await other.getByText("Master v2 · 当前", { exact: true }).waitFor(); await other.close();
  report.gates.push("409: concurrent browser save rejected, unsaved edit preserved, explicit reload");
  await api(`${pbase}/brief/revisions`, { expected_revision: 1, objective: "经明确确认的新项目目标" });
  await page.reload(); await loaded();
  await page.getByRole("checkbox", { name: /明确接纳最新项目上下文/ }).waitFor();
  await page.getByRole("checkbox", { name: /明确接纳最新项目上下文/ }).check();
  await clickAndRequest("保存内容 Master", masterPath(text));
  report.gates.push("Brief advance: old Master stale, explicit save creates new-context revision");
  for (const unit of units) {
    await page.goto(route(unit)); await loaded();
    if (unit.modality !== "text") {
      await page.getByRole("checkbox", { name: /明确接纳最新项目上下文/ }).check();
      await clickAndRequest("保存内容 Master", masterPath(unit));
      assert.equal(await page.getByRole("button", { name: "冻结 Master Candidate v4", exact: true }).isEnabled(), false);
      await clickAndRequest("确认当前渲染并保存新修订", masterPath(unit));
    }
    await clickAndRequest("运行 Master 检查", "/checks");
    const frozen = await clickAndRequest("冻结 Master Candidate v4", "/candidates/freeze");
    assert.equal(frozen.manifest.schema_version, 4);
    report.ids[unit.modality].candidate = frozen.id;
    if (unit.modality === "text") assert.equal(frozen.manifest.production.workflow, null);
    await page.getByRole("link", { name: `审阅 Candidate #${frozen.id}`, exact: true }).click();
    await page.getByRole("heading", { name: `Candidate #${frozen.id}`, exact: true }).waitFor();
    if (unit.modality === "graphic") { const img = page.getByRole("img", { name: "冻结画布 canvas-a" }); await img.waitFor(); await page.waitForFunction(() => document.querySelector('img[alt="冻结画布 canvas-a"]')?.naturalWidth === 320); }
    if (unit.modality === "video") await page.waitForFunction(() => document.querySelector('video[aria-label="冻结视频渲染"]')?.readyState >= 1);
    await page.getByRole("tab", { name: "变更", exact: true }).click();
    if (unit.modality !== "text") await page.getByText("图文/视频按结构化区段比较，不计算文本相似度。", { exact: true }).waitFor();
    await page.getByRole("tab", { name: "检查", exact: true }).click();
    await page.getByText("冻结检查：4 项", { exact: true }).waitFor();
    await page.getByRole("tab", { name: "交付", exact: true }).click();
    let response = page.waitForResponse((row) => row.url().endsWith(`/candidates/${frozen.id}/approve`) && row.request().method() === "POST");
    await page.getByRole("button", { name: "批准内容", exact: true }).click(); assert((await response).ok());
    await page.getByPlaceholder("人工发布账号标识").fill("isolated-manual-account");
    response = page.waitForResponse((row) => row.url().endsWith("/delivery-authorizations") && row.request().method() === "POST");
    await page.getByRole("button", { name: "授权交付目标", exact: true }).click(); assert((await response).ok());
    const downloading = page.waitForEvent("download");
    await page.getByRole("button", { name: "下载成品包 ZIP", exact: true }).click();
    const download = await downloading; const zip = join(artifacts, `${unit.modality}.zip`); await download.saveAs(zip);
    const inspected = execFileSync("/Users/mshengran/Project/AIContentStudio/apps/api/.venv/bin/python", ["-c", "import sys,json,zipfile; z=zipfile.ZipFile(sys.argv[1]); m=json.loads(z.read('manifest.json')); assert m['schema_version']==4; assert m['remote_call'] is False; assert 'publish-guide.md' in z.namelist(); print(json.dumps({'names':z.namelist(),'master':m['content_master']['id'],'candidate':m['candidate']['id']}))", zip], { encoding: "utf8" });
    assert.equal(JSON.parse(inspected).candidate, frozen.id);
    await page.screenshot({ path: join(artifacts, `${unit.modality}-review.png`), fullPage: true });
    report.gates.push(`${unit.modality}: checks, verified render, v4 freeze, actual Review preview/diff/checks, approval, authorization, downloaded ZIP`);
  }
  const debug = await makeUnit("Workflow debugger browser", "text", "wechat");
  const debugBase = `${pbase}/units/${debug.id}`;
  const definition = { nodes: [{ id: "constant", kind: "System", plugin: "system.constant", label: "真实常量", config: { value: { note: "persistent execution" } } }, { id: "human", kind: "Human", plugin: "builtin.confirm_facts", label: "人工确认", config: {} }], edges: [{ from: "constant", to: "human" }], visual_order: ["constant", "human"] };
  await api(`${debugBase}/workflow-override`, { expected_revision: 0, definition });
  await page.goto(route(debug)); await loaded();
  let response = page.waitForResponse((row) => row.url().endsWith(`${debugBase}/runs`) && row.request().method() === "POST");
  await page.getByRole("button", { name: "启动真实 Run", exact: true }).click();
  let run = await (await response).json(); assert.equal(run.status, "waiting_input");
  await page.getByText("人工确认", { exact: true }).click();
  response = page.waitForResponse((row) => row.url().endsWith("/nodes/human/complete") && row.request().method() === "POST");
  await page.getByRole("button", { name: "完成人工节点", exact: true }).click();
  run = await (await response).json(); assert.equal(run.status, "succeeded");
  await page.getByText("真实常量", { exact: true }).click();
  response = page.waitForResponse((row) => row.url().endsWith("/nodes/constant/rerun") && row.request().method() === "POST");
  await page.getByRole("button", { name: "运行此节点 / 刷新数据", exact: true }).click(); assert((await response).ok());
  response = page.waitForResponse((row) => row.url().endsWith("/nodes/constant/rerun-from-here") && row.request().method() === "POST");
  await page.getByRole("button", { name: "从这里重跑", exact: true }).click(); assert((await response).ok());
  await page.getByText("人工确认", { exact: true }).click();
  response = page.waitForResponse((row) => row.url().endsWith("/nodes/human/complete") && row.request().method() === "POST");
  await page.getByRole("button", { name: "完成人工节点", exact: true }).click(); assert((await response).ok());
  await page.reload(); await loaded();
  assert((await api(`${debugBase}/runs/${run.id}/nodes/constant/attempts`)).length >= 3);
  report.gates.push("Workflow debugger: browser starts persisted Run, completes Human, reruns node/from-here, history survives reload");
  await page.getByRole("button", { name: "进入设计模式", exact: true }).click();
  await page.getByRole("button", { name: "新增节点", exact: true }).click();
  await editor(page, "text").fill(JSON.stringify({ title: "独立内容编辑状态", markdown: "内容与流程独立保存" }));
  await clickAndRequest("保存内容 Master", masterPath(debug));
  assert(await page.getByRole("button", { name: "保存项目覆盖", exact: true }).isEnabled());
  const unsaved = JSON.stringify({ title: "保留内容未保存编辑", markdown: "保存流程不应覆盖内容" });
  await editor(page, "text").fill(unsaved);
  response = page.waitForResponse((row) => row.url().endsWith("/workflow-override") && row.request().method() === "POST");
  await page.getByRole("button", { name: "保存项目覆盖", exact: true }).click(); assert((await response).ok());
  assert.equal(await editor(page, "text").inputValue(), unsaved);
  await page.goto(route(units[1])); await loaded(); assert.equal(JSON.parse(await editor(page, "graphic").inputValue()).title, "浏览器画布");
  await page.goto(route(units[2])); await loaded(); assert.equal(JSON.parse(await editor(page, "video").inputValue()).title, "浏览器视频");
  report.gates.push("Independent Workflow/Master dirty saves and text/graphic/video navigation");
  const seeded = await makeUnit("Real Draft seed and legacy v3", "text", "wechat");
  const seedBase = `${pbase}/units/${seeded.id}`;
  const topic = await api("/topics", { title: "隔离真实工作流生成", core_thesis: "这是一条作者观点", fact_pack_id: pack.id, channels: ["wechat"] });
  await api(`${seedBase}/workflow-override`, { expected_revision: 0, definition: { nodes: [{ id: "generate", kind: "AI", plugin: "builtin.generate", config: { channel: "wechat", content_form: "article" } }], edges: [], visual_order: ["generate"] } });
  const generated = await api(`${seedBase}/runs`, { params: { topic_id: topic.id, channel: "wechat", content_form: "article" } });
  assert.equal(generated.status, "succeeded", JSON.stringify(generated));
  const output = (await api(`${seedBase}/outputs`)).find((row) => row.output_kind === "draft"); assert(output);
  await api(`/drafts/${output.entity_id}/materials`, { material_revision_id: renders.graphic.id, role: "cover" });
  await api(`/drafts/${output.entity_id}/fact-check`, {});
  for (const kind of ["platform", "media", "rights"]) await api(`/drafts/${output.entity_id}/checks/${kind}`, {});
  await api(`/drafts/${output.entity_id}/discoverability/post`, {});
  await page.goto(`${ui}/review?project=${project.id}&unit=${seeded.id}`);
  await page.getByRole("button", { name: "冻结 Candidate", exact: true }).waitFor();
  response = page.waitForResponse((row) => row.url().endsWith("/candidates/freeze") && row.request().method() === "POST");
  await page.getByRole("button", { name: "冻结 Candidate", exact: true }).click();
  const legacyResponse = await response; assert(legacyResponse.ok(), await legacyResponse.text());
  const legacy = await legacyResponse.json(); assert.equal(legacy.manifest.schema_version, 3);
  await page.goto(route(seeded)); await loaded();
  await page.getByRole("combobox", { name: "Draft seed 输出", exact: true }).selectOption(String(output.id));
  const seededMaster = await clickAndRequest("从 Draft 创建 Text Master", "/master-revisions/from-output");
  assert.equal(seededMaster.source_kind, "workflow_seed");
  assert.equal(seededMaster.origin_workflow_run_id, generated.id);
  assert.equal(seededMaster.origin_project_output_id, output.id);
  await page.reload(); await loaded();
  assert.equal((await current(seeded)).id, seededMaster.id);
  report.gates.push("Real engine Draft output (explicit mock provider), browser Draft→Master seed, exact Run/Attempt/output persisted");
  await editor(page, "text").fill(JSON.stringify({ title: "新 Master 候选", markdown: "保留旧 v3 清单，不修改历史正文" }));
  await clickAndRequest("保存内容 Master", masterPath(seeded));
  await clickAndRequest("运行 Master 检查", "/checks");
  await clickAndRequest("冻结 Master Candidate v4", "/candidates/freeze");
  await page.goto(`${ui}/review?project=${project.id}&unit=${seeded.id}&candidate=${legacy.id}`);
  await page.getByRole("heading", { name: `Candidate #${legacy.id}`, exact: true }).waitFor();
  assert((await page.locator("pre").first().textContent()).includes(legacy.manifest.content.body_markdown.slice(0, 80)));
  const preserved = await api(`/review-center/projects/${project.id}/units/${seeded.id}/candidates/${legacy.id}`);
  assert.deepEqual(preserved.manifest, legacy.manifest); assert.equal(preserved.candidate_hash, legacy.candidate_hash);
  await page.getByRole("tab", { name: "交付", exact: true }).click();
  await page.getByText("这是历史 Candidate；交付操作只针对当前候选。历史清单仍可在预览、变更和检查中查看。", { exact: true }).waitFor();
  report.gates.push("Historical v3 body, hash and manifest unchanged after new v4; history read-only");
  await api(pbase, undefined, "DELETE");
  await page.goto(route(debug)); await loaded();
  for (const name of ["保存内容 Master", "运行 Master 检查", "冻结 Master Candidate v4", "进入设计模式", "保存项目覆盖", "另存为角色默认新版本", "启动真实 Run"]) {
    assert(await page.getByRole("button", { name, exact: true }).isDisabled(), `Archived project must disable ${name}`);
  }
  await page.getByText("真实常量", { exact: true }).click();
  for (const name of ["运行此节点 / 刷新数据", "从这里重跑"]) {
    assert(await page.getByRole("button", { name, exact: true }).isDisabled(), `Archived project must disable ${name}`);
  }
  assert.equal(await editor(page, "text").getAttribute("readonly"), "");
  report.gates.push("Archived project: Master and Workflow mutations disabled; persisted history remains readable");
  assert.deepEqual(report.consoleErrors, []);
  writeFileSync(join(artifacts, "report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  report.failure = error.stack; await page.screenshot({ path: join(artifacts, "failure.png"), fullPage: true });
  writeFileSync(join(artifacts, "report.json"), JSON.stringify(report, null, 2));
  throw error;
} finally { await browser.close(); }
