import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createHash } from "node:crypto";

assert.equal(process.env.F7_ISOLATED_ACCEPTANCE, "yes");
const { chromium } = createRequire(import.meta.url)("playwright");
const browser = await chromium.launch({ headless: true, channel: "chrome", chromiumSandbox: true });
const page = await browser.newPage();
page.setDefaultTimeout(5000);
await page.route("**/*", route => new URL(route.request().url()).origin === "http://127.0.0.1:15391"
  ? route.continue() : route.abort("blockedbyclient"));
const errors = [], external = [], diagnostics = [];
let imageStatus = 200, oversized = false;
const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEElEQVR4nGP8zwACTGCSAQANHQEDgslx/wAAAABJRU5ErkJggg==", "base64");
const pngHash = createHash("sha256").update(png).digest("hex");
page.on("pageerror", error => errors.push(error.message));
page.on("console", message => { if (message.type() === "error") diagnostics.push(message.text()); });
await page.route("**/api/v1/**", route => route.request().url().endsWith("/renders/28")
  ? route.fulfill({ status: imageStatus, contentType: "image/png", body: oversized ? Buffer.alloc(8 * 1024 * 1024 + 1) : png })
  : route.fulfill({ status: 200, contentType: "application/json", body: "[]" }));
await page.route("https://preview-canary.invalid/**", route => { external.push(route.request().url()); return route.abort(); });
try {
  await page.goto("http://127.0.0.1:15391/projects");
  await page.evaluate(async () => {
    const { default: React } = await import("/node_modules/.vite/deps/react.js");
    const { default: ReactDOM } = await import("/node_modules/.vite/deps/react-dom_client.js");
    const { CandidatePreview } = await import("/src/product/CandidatePreview.tsx");
    const container = document.createElement("div");
    document.body.append(container);
    const root = ReactDOM.createRoot(container);
    window.previewRoot = root;
    window.previewComponent = CandidatePreview;
    window.previewReact = React;
    window.previewProps = {
      path: "/content-projects/1/candidates/2", assets: [],
      preview: { modality: "text", title: "冻结候选", markdown: "旧通用预览", render: {},
        target: { channel: "wechat", content_form: "article", artifact_kind: "text" },
        official_render: { schema: "wechat.official.article.v1", renderer: "wechat.official.html", renderer_version: "1",
          title: "冻结公众号标题", author: "", digest: "", status: "local_ready", reasons: [], render_hash: "frozen-hash",
          remote_contract: "unresolved_body_limits", asset_slots: [{ slot_key: "cover", usage: "cover", material_revision_id: 27, content_hash: "exact-cover-hash" }],
          html_template: '<h2>冻结正文</h2><p>原样 &amp; 保留</p><script>parent.__previewExecuted=true</script><img src="https://preview-canary.invalid/image"><a href="https://preview-canary.invalid/navigate" target="_top">禁止跳转</a>' } }
    };
    root.render(React.createElement(CandidatePreview, window.previewProps));
  });
  const frameElement = page.getByTitle("冻结公众号 HTML 预览");
  await frameElement.waitFor();
  assert.equal(await frameElement.getAttribute("sandbox"), "");
  const frame = page.frameLocator('iframe[title="冻结公众号 HTML 预览"]');
  await frame.getByText("冻结正文", { exact: true }).waitFor();
  await frame.getByText("原样 & 保留", { exact: true }).waitFor();
  await frame.getByText("禁止跳转", { exact: true }).click();
  assert.match(page.url(), /\/projects$/);
  assert.equal(await page.evaluate(() => window.__previewExecuted), undefined);
  await page.getByText("远端不可执行：官方正文限制尚未核实", { exact: true }).waitFor();
  await page.getByText(/cover.*Revision #27.*exact-cover-hash/).waitFor();
  assert.equal(await page.getByRole("button", { name: /发布|上传|创建草稿/ }).count(), 0);
  await page.evaluate(() => Object.defineProperty(window.crypto, "subtle", { value: undefined, configurable: true }));
  for (const size of [0, 3, 55, 56, 63, 64, 65, 1000]) {
    const bytes = Buffer.from(Array.from({ length: size }, (_, index) => index % 256));
    const hash = await page.evaluate(async value => {
      const { previewByteHash } = await import("/src/product/previewByteHash.ts");
      return previewByteHash(new Uint8Array(value).buffer);
    }, Array.from(bytes));
    assert.equal(hash, createHash("sha256").update(bytes).digest("hex"));
  }
  await page.evaluate(hash => {
    const props = structuredClone(window.previewProps);
    props.preview.official_render.asset_slots.push({ slot_key: "img1", usage: "inline", block_id: "img1", material_revision_id: 28, content_hash: hash });
    props.preview.official_render.html_template = '<p>配图之前</p><figure data-block-id="img1"><img src="aics-resource:img1" alt="精确正文图"><figcaption>冻结图注</figcaption></figure><p>配图之后</p>';
    window.previewInlineProps = props;
    window.previewRoot.render(window.previewReact.createElement(window.previewComponent, props));
  }, pngHash);
  const inlineImage = frame.getByAltText("精确正文图");
  await inlineImage.waitFor();
  await page.waitForFunction(() => {
    const iframe = document.querySelector('iframe[title="冻结公众号 HTML 预览"]');
    return iframe?.getAttribute("srcdoc")?.includes("data:image/png;base64,");
  });
  assert.equal(await inlineImage.evaluate(async image => { await image.decode(); return image.complete && image.naturalWidth > 0; }), true);
  await frame.getByText("配图之后", { exact: true }).waitFor();
  await page.evaluate(() => {
    const props = structuredClone(window.previewInlineProps);
    props.preview.official_render.asset_slots[1].content_hash = "0".repeat(64);
    window.previewRoot.render(window.previewReact.createElement(window.previewComponent, props));
  });
  await page.getByText(/冻结正文图片不可预览.*字节哈希不匹配/).waitFor();
  imageStatus = 403;
  await page.evaluate(() => window.previewRoot.render(window.previewReact.createElement(window.previewComponent, window.previewInlineProps)));
  await page.getByText(/冻结正文图片不可预览.*实时权利或版本校验失败 \(403\)/).waitFor();
  imageStatus = 200; oversized = true;
  await page.evaluate(() => {
    const props = structuredClone(window.previewInlineProps);
    props.path = "/content-projects/1/candidates/3";
    window.previewRoot.render(window.previewReact.createElement(window.previewComponent, props));
  });
  await page.getByText(/冻结正文图片不可预览.*超出本地预览字节预算/).waitFor();
  oversized = false;
  await page.evaluate(() => {
    const props = structuredClone(window.previewProps);
    props.preview.official_render.status = "unavailable";
    props.preview.official_render.reasons = ["cover_required"];
    window.previewRoot.render(window.previewReact.createElement(window.previewComponent, props));
  });
  await page.getByText("适配不可用：cover_required", { exact: true }).waitFor();
  await page.evaluate(() => {
    const props = structuredClone(window.previewProps);
    delete props.preview.official_render;
    window.previewRoot.render(window.previewReact.createElement(window.previewComponent, props));
  });
  await frameElement.waitFor({ state: "detached" });
  await page.getByText("旧通用预览", { exact: true }).waitFor();
  assert.deepEqual(external, []);
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ gates: 12, evidence: "real CandidatePreview + frozen API-shaped fixture: exact HTML, script/external-network/top-navigation blocked, slots/current remote gate, local unavailable reason, exact inline authenticated bytes/in-place preview/hash mismatch/403/byte-budget rejection, LAN SHA256 boundary vectors, no effect controls, legacy absence unchanged; no platform call" }));
} catch (cause) { throw new Error(`${cause.message}\n${diagnostics.join("\n")}`); }
finally { await browser.close(); }
