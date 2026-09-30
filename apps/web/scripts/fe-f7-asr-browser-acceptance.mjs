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
const artifacts = mkdtempSync(join(tmpdir(), "aicontent-f7-asr-browser-"));
const report = { artifacts, evidence: "isolated real WAV bytes and fixture transcription, not real ASR provider verification", gates: [], pageErrors: [] };
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const page = await browser.newPage();
page.on("pageerror", error => report.pageErrors.push(error.message));
async function api(path, data) {
  const response = data === undefined ? await page.request.get(`${ui}/api/v1${path}`, { headers }) : await page.request.post(`${ui}/api/v1${path}`, { headers, data });
  assert(response.ok(), `${path}: ${response.status()} ${await response.text()}`);
  return response.json();
}
try {
  const wav = Buffer.alloc(44 + 128000);
  wav.write("RIFF", 0); wav.writeUInt32LE(wav.length - 8, 4); wav.write("WAVEfmt ", 8);
  wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(16000, 24); wav.writeUInt32LE(32000, 28); wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34);
  wav.write("data", 36); wav.writeUInt32LE(128000, 40);
  const upload = await page.request.post(`${ui}/api/v1/materials/upload?kind=audio&public_use_allowed=true&model_use_allowed=true&rights_status=cleared`, {
    headers, multipart: { file: { name: "asr-source.wav", mimeType: "audio/wav", buffer: wav } },
  });
  assert.equal(upload.status(), 201);
  const source = (await upload.json()).revisions[0];
  const persona = await api("/content-personas", { name: "ASR browser author" });
  const project = await api("/content-projects", { title: "ASR browser project" });
  const unit = await api(`/content-projects/${project.id}/units`, { title: "ASR Video", modality: "video", persona_id: persona.id });
  await api(`/content-projects/${project.id}/materials/references`, { material_revision_id: source.id });
  const masterPath = `/content-projects/${project.id}/units/${unit.id}/master-revisions`;
  await api(masterPath, { payload_schema: "video.master.v2", idempotency_key: "asr-browser-initial", payload: {
    title: "ASR", aspect_ratio: [9, 16], script: { blocks: [] }, shots: [], timeline: { duration_ms: 4000, tracks: [] },
    voice: { mode: "recorded", material_revision_id: source.id }, subtitles: { cues: [] }, overlays: [], music: {}, cover: {},
  }, asset_refs: [{ material_revision_id: source.id, content_hash: source.content_hash, role: "voice_audio", slot_key: "voice", sort_order: 0, placement: { voice: "main" } }] });
  await page.goto(`${ui}/projects/${project.id}/units/${unit.id}/production`);
  const panel = page.getByRole("region", { name: "ASR 转录建议", exact: true });
  await panel.getByLabel("ASR 精确来源版本").selectOption(String(source.id));
  await panel.getByRole("button", { name: "明确请求 ASR 建议", exact: true }).click();
  await panel.getByRole("button", { name: "拒绝转录建议", exact: true }).waitFor();
  assert.equal((await api(masterPath)).items.length, 1);
  report.gates.push("suggestion previews real-source cues without Master write");
  await panel.getByRole("button", { name: "拒绝转录建议", exact: true }).click();
  assert.equal((await api(masterPath)).items.length, 1);
  report.gates.push("Reject writes neither subtitles nor revision");
  await panel.getByRole("button", { name: "明确请求 ASR 建议", exact: true }).click();
  await panel.getByRole("button", { name: "明确接受并替换本地字幕", exact: true }).click();
  await panel.getByText("尚未保存", { exact: false }).waitFor();
  assert.equal((await api(masterPath)).items.length, 1);
  report.gates.push("Accept modifies local draft only");
  const saved = page.waitForResponse(response => response.url().endsWith(masterPath) && response.request().method() === "POST");
  await page.getByRole("button", { name: "保存内容 Master", exact: true }).click();
  const response = await saved;
  assert.equal(response.status(), 200, await response.text());
  const master = await response.json();
  assert.equal(master.edit_summary.asr_provenance.status, "verified_output_match");
  assert.equal(master.payload.subtitles.cues[0].text, "隔离转录字幕");
  assert.equal(master.edit_summary.asr_provenance.source.revision_id, source.id);
  assert(!JSON.stringify(master).includes("fixture-secret"));
  assert.equal((await api(masterPath)).items.length, 2);
  await page.reload();
  await panel.getByLabel("ASR 精确来源版本").waitFor();
  report.gates.push("explicit Save persists exact source/runtime provenance and refresh retains subtitles");
  assert.deepEqual(report.pageErrors, []);
  await page.screenshot({ path: join(artifacts, "saved-video-asr.png"), fullPage: true });
} finally {
  writeFileSync(join(artifacts, "report.json"), JSON.stringify(report, null, 2));
  await browser.close();
}
console.log(JSON.stringify(report));
