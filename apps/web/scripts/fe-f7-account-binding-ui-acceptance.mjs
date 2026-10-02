import assert from "node:assert/strict";
import { createRequire } from "node:module";

assert.equal(process.env.F7_ISOLATED_ACCEPTANCE, "yes");
const { chromium } = createRequire(import.meta.url)("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", chromiumSandbox: true });
const page = await browser.newPage();
page.setDefaultTimeout(5000);
// Isolated acceptance must not depend on external fonts or permit external effects.
await page.route("**/*", route => new URL(route.request().url()).origin === "http://127.0.0.1:15391"
  ? route.continue() : route.abort("blockedbyclient"));
let role = "admin";
let ancestryArchived = false;
let verificationRevoked = false;
const writes = [], errors = [];
const account = { id: 10, name: "账号A", status: "active", persona_id: 1, current_revision: 0, platform_channel: null, platform_account_id: null };
const accountB = { ...account, id: 11, name: "账号B", platform_channel: "wechat", platform_account_id: "wxfedcba9876543210" };
let connection = { content_account_id: 10, revision: 0, enabled: false, credential_version: null, credential_ref: "AICS_WECHAT_ACCOUNT_10_APPSECRET", configured: false, verified: false, executable: false, unavailable_reason: "official_contract_unresolved" };
const scopeA = { channel: "wechat", content_form: "article", action: "auto_draft", content_account_id: 10,
  account_ref: "wx0123456789abcdef", publisher_key: "publisher.wechat.official", publisher_version: "1" };
const scopeB = { ...scopeA, content_account_id: 11, account_ref: accountB.platform_account_id };
page.on("pageerror", error => errors.push(error.message));
await page.route("**/api/v1/**", async route => {
  const request = route.request(), path = new URL(request.url()).pathname.replace("/api/v1", "");
  let body = [];
  if (request.method() === "PUT") {
    const data = request.postDataJSON();
    writes.push({ path, data });
    assert.equal(role, "admin");
    if (path.endsWith("/platform-binding")) { Object.assign(account, data); body = account; }
    else if (path.endsWith("/publisher-connection")) {
      assert.equal(data.expected_revision, connection.revision);
      connection = { ...connection, ...data, revision: connection.revision + 1, configured: true };
      body = { ...connection, read_only: ancestryArchived || role !== "admin" };
    } else assert.fail(`unexpected write ${path}`);
  } else if (request.method() === "POST" && path === "/settings/publisher-verifications") {
    assert.equal(role, "admin");
    const data = request.postDataJSON();
    assert.deepEqual(data, { ...scopeA, result: "revoked", reference_hash: "0".repeat(64), confirm_readback: true });
    writes.push({ path, data }); verificationRevoked = true; body = { result: "revoked" };
  } else if (request.method() !== "GET") assert.fail(`unexpected action ${path}`);
  else if (path === "/users/me") body = { role, id: 1, email: "fixture@studio.local" };
  else if (path === "/content-personas") body = [{ id: 1, name: "角色", status: "active", current_revision: 0 }];
  else if (path === "/content-personas/1/accounts") body = [account, accountB];
  else if (path === "/content-accounts/10") body = account;
  else if (path === "/content-accounts/10/publisher-connection") body = { ...connection, read_only: ancestryArchived || role !== "admin" };
  else if (path === "/content-accounts/11") body = accountB;
  else if (path === "/content-accounts/11/publisher-connection") body = { ...connection, content_account_id: 11, credential_ref: "AICS_WECHAT_ACCOUNT_11_APPSECRET", credential_version: "credential-b", revision: 5, read_only: ancestryArchived || role !== "admin" };
  else if (path === "/settings/product") body = { sections: [{ key: "channels", label: "渠道", editability: "read_only", data: {} }] };
  else if (path === "/settings/capabilities") body = { publishers: [scopeA, scopeB].map((scope, index) => ({
    scope, configured: true, verified: index !== 0 || !verificationRevoked, executable: false, reason: "official_contract_unresolved",
    last_verification: { result: index === 0 && verificationRevoked ? "revoked" : "verified",
      verified_at: "2026-09-30T10:00:00Z", expires_at: index === 0 && verificationRevoked ? null : "2026-10-02T10:00:00Z" },
  })), renderers: [], can_verify: role === "admin", publisher_verification_available: false };
  else if (path === "/content-identities/effective") body = { effective_profile: {}, field_origins: {}, revision_ids: {} };
  else if (path.includes("default-workflows") || path.includes("effective-workflow")) body = { revision: 0, workflow_id: null, definition: {} };
  await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
});
try {
  await page.goto("http://127.0.0.1:15391/identities");
  await page.getByRole("button", { name: /账号A/ }).click();
  await page.getByRole("tab", { name: "账号与栏目" }).click();
  await page.getByLabel("公众号 AppID").fill("wx0123456789abcdef");
  await page.getByRole("button", { name: "绑定真实账号", exact: true }).click();
  await page.getByText("账号已绑定，尚未验证", { exact: true }).waitFor();
  await page.getByLabel("凭据版本").fill("credential-v1");
  await page.getByRole("button", { name: "保存账号连接", exact: true }).click();
  await page.getByText("连接配置已保存；未调用微信接口。", { exact: true }).waitFor();
  assert.equal(writes.length, 2);
  assert.deepEqual(writes[1].data, { expected_revision: 0, enabled: true, credential_version: "credential-v1" });
  assert.equal(await page.locator('input[type="password"]').count(), 0);
  await page.reload();
  await page.getByRole("button", { name: /账号A/ }).click();
  await page.getByRole("tab", { name: "账号与栏目" }).click();
  assert.equal(await page.getByLabel("凭据版本").inputValue(), "credential-v1");
  await page.getByText("远端不可执行：官方正文限制尚未核实", { exact: true }).waitFor();
  await page.getByLabel("凭据版本").fill("unsaved-v2");
  await page.getByRole("button", { name: "重读服务端版本（保留输入）", exact: true }).click();
  await page.getByText("已重读服务端版本，本地输入未改变；请核对后再明确保存。", { exact: true }).waitFor();
  assert.equal(await page.getByLabel("凭据版本").inputValue(), "unsaved-v2");
  page.once("dialog", dialog => dialog.dismiss());
  await page.getByRole("tab", { name: "身份", exact: true }).click();
  assert.equal(await page.getByLabel("凭据版本").inputValue(), "unsaved-v2");
  await page.evaluate(() => { window.history.pushState({}, "", "/projects"); window.dispatchEvent(new PopStateEvent("popstate")); });
  await page.getByLabel("凭据版本").waitFor({ state: "detached" });
  await page.goBack();
  await page.getByRole("button", { name: /账号A/ }).click();
  await page.getByRole("tab", { name: "账号与栏目" }).click();
  assert.equal(await page.getByLabel("凭据版本").inputValue(), "unsaved-v2");
  await page.getByLabel("凭据版本").fill("credential-v1");
  role = "viewer";
  await page.reload();
  await page.getByRole("button", { name: /账号A/ }).click();
  await page.getByRole("tab", { name: "账号与栏目" }).click();
  assert.equal(await page.getByRole("button", { name: "保存账号连接", exact: true }).isDisabled(), true);
  await page.goto("http://127.0.0.1:15391/settings");
  await page.getByRole("button", { name: "渠道", exact: true }).click();
  await page.getByLabel("官方公众号连接账号").selectOption("10");
  assert.equal(await page.getByLabel("凭据版本").inputValue(), "credential-v1");
  assert.equal(await page.getByRole("button", { name: "保存账号连接", exact: true }).isDisabled(), true);
  await page.getByLabel("官方公众号连接账号").selectOption("11");
  await page.getByText("已绑定 wxfedcba9876543210 · 未验证，不能直接交付", { exact: true }).waitFor();
  assert.equal(await page.getByLabel("凭据版本").inputValue(), "credential-b");
  await page.getByText("AICS_WECHAT_ACCOUNT_11_APPSECRET", { exact: true }).waitFor();
  assert.equal(await page.locator('input[type="password"]').count(), 0);
  assert.equal(await page.getByRole("button", { name: "记录账号核验", exact: true }).count(), 0);
  assert.equal(await page.getByRole("button", { name: "撤销验证", exact: true }).count(), 0);
  role = "admin";
  await page.reload();
  await page.getByRole("button", { name: "渠道", exact: true }).click();
  await page.getByLabel("官方公众号连接账号").selectOption("10");
  await page.getByLabel("凭据版本").fill("credential-a2");
  await page.getByRole("button", { name: "保存账号连接", exact: true }).click();
  await page.getByText("连接配置已保存；未调用微信接口。", { exact: true }).waitFor();
  assert.equal(writes.at(-1).path, "/content-accounts/10/publisher-connection");
  await page.getByLabel("官方公众号连接账号").selectOption("11");
  await page.getByText("已绑定 wxfedcba9876543210 · 未验证，不能直接交付", { exact: true }).waitFor();
  assert.equal(await page.getByLabel("凭据版本").inputValue(), "credential-b");
  assert.equal(writes.length, 3);
  const publisherA = page.locator("article").filter({ hasText: `${scopeA.account_ref} · 公众号文章` }).last();
  const publisherB = page.locator("article").filter({ hasText: `${scopeB.account_ref} · 公众号文章` }).last();
  page.once("dialog", dialog => dialog.dismiss());
  await publisherA.getByRole("button", { name: "撤销验证", exact: true }).click();
  assert.equal(writes.length, 3);
  page.once("dialog", dialog => dialog.accept());
  await publisherA.getByRole("button", { name: "撤销验证", exact: true }).click();
  await page.getByText("验证已撤销；历史记录仍可查看。", { exact: true }).waitFor();
  await publisherA.getByText("当前范围未验证 / 已失效", { exact: true }).waitFor();
  assert.equal(await publisherA.getByRole("button", { name: "撤销验证", exact: true }).isDisabled(), true);
  await publisherB.getByText("账号范围已验证", { exact: true }).waitFor();
  assert.equal(await publisherB.getByRole("button", { name: "撤销验证", exact: true }).isDisabled(), false);
  assert.equal(writes.length, 4);
  assert.equal(await page.getByRole("button", { name: "记录账号核验", exact: true }).count(), 0);
  assert.equal(JSON.stringify(writes).includes("AppSecret"), false);
  ancestryArchived = true;
  await page.reload();
  await page.getByRole("button", { name: "渠道", exact: true }).click();
  await page.getByLabel("官方公众号连接账号").selectOption("10");
  await page.getByLabel("凭据版本").waitFor();
  assert.equal(await page.getByRole("button", { name: "保存账号连接", exact: true }).isDisabled(), true);
  await page.goto("http://127.0.0.1:15391/identities");
  await page.getByRole("button", { name: /账号A/ }).click();
  await page.getByRole("tab", { name: "账号与栏目" }).click();
  await page.getByLabel("凭据版本").waitFor();
  assert.equal(await page.getByRole("button", { name: "保存账号连接", exact: true }).isDisabled(), true);
  assert.deepEqual(errors, []);
  assert.equal(writes.length, 4);
  console.log(JSON.stringify({ gates: 20, evidence: "UI fixture only: Identity/Settings dual-account config and readonly; viewer cannot revoke, cancel zero writes, explicit exact A scope revocation leaves B verified, unavailable contract cannot create verification, no secret/effect; backend checked separately" }));
} finally { await browser.close(); }
