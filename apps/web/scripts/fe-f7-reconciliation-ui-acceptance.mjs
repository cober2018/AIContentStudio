import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";

// Fixture transport proves UI boundaries, not a real account or backend transaction.
assert.equal(process.env.F7_ISOLATED_ACCEPTANCE, "yes");
const { chromium } = createRequire(import.meta.url)("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", chromiumSandbox: true });
const page = await browser.newPage();
const origin = process.env.F7_UI_ORIGIN || "http://127.0.0.1:15671";
assert.equal(new URL(origin).hostname, "127.0.0.1");
assert.equal(new URL(origin).protocol, "http:");
await page.route("**/*", route => new URL(route.request().url()).origin === new URL(origin).origin
  ? route.continue() : route.abort("blockedbyclient"));
const errors = [], posts = [];
page.on("pageerror", error => errors.push(error.message));
let status = "reconciliation_needed";
let official = false, attemptStatus = "unknown", remoteId = null, archived = false;
const target = () => ({ id: 10, status, action: "auto_draft", account_ref: "isolated-account", content_account_id: 1,
  publisher_key: official ? "publisher.wechat.official" : "publisher.wechat.wewrite", publisher_version: "1",
  attempts: [{ id: 21, status: attemptStatus, remote_id: remoteId }, { id: 20, status: "failed" }], receipts: [] });
const projects = () => [{ project_id: 1, title: "Isolated reconciliation UI", status: "active", units: [{
  project_id: 1, unit_id: 1, title: "Text", modality: "text", unit_status: archived ? "archived" : "active", persona_id: 1,
  account_id: 1, summary: "unknown", dimensions: {}, current_candidate: { id: 1, hash: "a".repeat(64), status: "approved" },
  legacy_current_candidate: { id: 1 }, history: [], reviews: [], targets: [target()],
}] }];
await page.route("**/api/v1/**", async route => {
  const request = route.request();
  const path = new URL(request.url()).pathname.replace("/api/v1", "");
  let body = [];
  if (request.method() === "POST") {
    posts.push({ path, body: request.postDataJSON() });
    assert.ok(["/delivery-targets/10/reconcile", "/delivery-targets/10/official-readback"].includes(path));
    status = path.endsWith("official-readback") ? "awaiting_manual_receipt" : request.postDataJSON().resolution === "not_delivered" ? "target_authorized" : "human_confirmed";
    if (path.endsWith("official-readback")) attemptStatus = "succeeded";
    body = { target_id: 10, status };
  } else if (path === "/review-center/projects") body = projects();
  else if (path === "/assets/1/delivery-targets") body = [target()];
  else if (path.endsWith("/candidates/1")) body = { id: 1, status: "approved", candidate_hash: "a".repeat(64), manifest: {}, preview: { modality: "text", title: "Frozen", markdown: "Frozen body" } };
  else if (path.endsWith("/diff")) body = { changed_sections: {}, text: null };
  await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
});
try {
  await page.goto(`${origin}/review?project=1&unit=1`);
  await page.getByRole("tab", { name: "交付", exact: true }).click();
  const button = page.getByRole("button", { name: "确认已交付", exact: true });
  await button.waitFor();
  assert.equal(await button.isDisabled(), true);
  const evidence = "Readback token=DO_NOT_UPLOAD confirmed draft";
  await page.getByPlaceholder("平台核验依据", { exact: false }).fill(evidence);
  page.once("dialog", dialog => dialog.dismiss());
  await button.click();
  assert.equal(posts.length, 0);
  page.once("dialog", dialog => dialog.accept());
  await button.click();
  await page.getByText("人工核验回执已保存；不是平台自动验证或正式发布。", { exact: true }).waitFor();
  assert.equal(posts.length, 1);
  assert.deepEqual(posts[0].body, { resolution: "delivered", expected_attempt_id: 21,
    evidence_ref: `sha256:${createHash("sha256").update(evidence).digest("hex")}` });
  assert.equal(JSON.stringify(posts).includes("DO_NOT_UPLOAD"), false);
  official = true; status = "reconciliation_needed"; remoteId = "known-draft-id";
  await page.reload();
  await page.getByRole("tab", { name: "交付", exact: true }).click();
  const readback = page.getByRole("button", { name: "回读已知草稿（不重建）", exact: true });
  await readback.waitFor();
  page.once("dialog", dialog => dialog.dismiss());
  await readback.click();
  assert.equal(posts.length, 1);
  page.once("dialog", dialog => dialog.accept());
  await readback.click();
  await page.getByText("已请求精确草稿回读；未创建新草稿，也不代表公开发布。", { exact: true }).waitFor();
  assert.deepEqual(posts.at(-1), { path: "/delivery-targets/10/official-readback", body: { expected_attempt_id: 21 } });
  assert.equal(posts.length, 2);
  status = "target_authorized"; attemptStatus = "running"; remoteId = null;
  await page.reload();
  await page.getByRole("tab", { name: "交付", exact: true }).click();
  await page.getByRole("button", { name: "确认未交付", exact: true }).waitFor();
  assert.equal(await page.getByRole("button", { name: "确认未交付", exact: true }).isDisabled(), true);
  assert.equal(await page.getByRole("button", { name: "下载成品包 ZIP", exact: true }).isDisabled(), true);
  assert.equal(await readback.count(), 0);
  await page.getByPlaceholder("平台核验依据", { exact: false }).fill("explicit interrupted-worker verification");
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "确认未交付", exact: true }).click();
  await page.getByText("已记录未交付证据；不会自动重发，再次执行仍须通过当前权限与能力验证。", { exact: true }).waitFor();
  assert.equal(posts.length, 3);
  assert.deepEqual(posts.at(-1), { path: "/delivery-targets/10/reconcile", body: {
    resolution: "not_delivered", expected_attempt_id: 21,
    evidence_ref: `sha256:${createHash("sha256").update("explicit interrupted-worker verification").digest("hex")}` } });
  archived = true;
  await page.reload();
  await page.getByRole("tab", { name: "交付", exact: true }).click();
  assert.equal(await page.getByRole("button", { name: "确认未交付", exact: true }).isDisabled(), true);
  assert.equal(posts.length, 3);
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ evidence: "UI fixture transport only; backend tested separately", gates: [
    "empty evidence disables decision", "cancel causes zero writes", "explicit confirmation sends exact latest attempt and only evidence hash", "known-ID readback cancel has zero effect", "exact Attempt readback only, no create", "running official recovery", "archived history readonly", "no execute or remote call", "zero page errors",
  ] }));
} finally { await browser.close(); }
