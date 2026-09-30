# FE-F7 本地图文 Renderer：真实实现与 API 接受

## 范围与边界

F7 86/105 保持不变，本批推进 7.5–7.7 的真实实现，不代表三项全面验收。新增 `graphic.chromium@1`，首批只支持 `graphic.master.v2 → xiaohongshu/image_note → image/png`。复用既有管理员 preview、actor 临时缓存、MaterialRevision 与显式 Master save；零新表、零 migration。

```text
current saved Graphic v2 / exact context + profile + refs
→ 显式管理员 probe
→ 实际 Chromium 渲染 selected canvas PNG
→ 未入库 / 未 verified 的 preview
→ 人工许可与权利确认
→ exact MaterialRevision + Project reference
→ 用户显式 final binding + manual confirmation
→ 新 append-only Master revision
```

本批没有普通用户 verified renderer execution、自动 attestation、前端按钮/浏览器产品验收或真实 Video renderer；不会将未配置的环境显示为可执行，也没有宣称 Candidate→Review→ZIP 本轮已跑完整链路。F8 未启动。

## 目录、依赖与启动

- `apps/api/app/services/local_graphic_renderer.py`：canonical validation、字体覆盖、来源字节/预算、运行身份、隔离临时目录、进程树 timeout、safe typed result。
- 同目录 `local_graphic_renderer.cjs`：固定浏览器截图参数，DOM `textContent`、CSS 白名单、inline exact image/chart bytes；层序/可见性/旋转/透明度、裁剪/fit/focal、矩形/椭圆/线条和普通文字。
- `content_harness/providers.py`：只注册 descriptor；bootstrap 不探测运行环境。
- `tests/test_f7_local_graphic_renderer.py`：真实配置时运行 Chromium 像素/确定性测试和 API stage/accept/explicit Master bind。

运行 API 前由操作人员显式配置四个绝对路径环境变量：

| 环境变量 | 对象 |
|---|---|
| `GRAPHIC_RENDER_NODE` | 实际 Node executable |
| `GRAPHIC_RENDER_BROWSER` | Chromium/Chrome executable |
| `GRAPHIC_RENDER_PLAYWRIGHT` | 已安装 `playwright` 包目录，与 `playwright-core` 同级 |
| `GRAPHIC_RENDER_FONT` | 浏览器可加载且 Pillow 可读取的字体文件 |

没有内置 Codex runtime 路径，没有自动下载依赖/浏览器/字体，没有更改 shell profile 或真实服务配置。设置路径不等于 capability verified。运行命令沿用 API 启动方式；实际执行入口为现有 `/master-revisions/{id}/media-render-previews`，renderer key/version 为上述 exact 值。私密/本地配置路径不进入 API、素材元数据或错误。

当前只支持单一字体的 normal/400；缺字、混合段落对齐、bold/italic、动画源图和非整数 canvas 像素尺寸明确拒绝，不静默 fallback/合成样式。不是全字体排版完成。字体、Node、实际 Playwright JS/JSON、Chrome app bundle、脚本和验证代码的字节变化会改变 execution fingerprint。

## 实跑证据

使用当前机器已有的 Node、Chrome、Playwright 和 Arial 字体，通过单次测试命令环境变量显式配置。没有联网素材下载或外部账号调用。

- 初始不存在 implementation：RED；缺字体样式被合成的两个负例 RED，随后拒绝缺变体 GREEN。
- 真 PNG 的 red rectangle/background 像素、同输入两次独立 browser 输出字节一致。
- exact red/blue 源图 crop 右半侧，输出像素确为 blue；缺 source bytes 拒绝。
- 用户 `<script>` 内容只作为文字，输出确有文字像素；非法 CSS URL 不进入 DOM。
- Layer order、visibility、alpha 的输出像素验证；字体字节改变指纹，坏字体拒绝。
- API probe→accept 只存真实素材及项目引用，不改 Master；显式 bind/save 追加第二个 Master，attestation origin 仍为 `manual`。

| 最终门禁 | 结果 |
|---|---|
| 本批真实 local renderer 新回归 | 17 passed / 1 既有 warning |
| Renderer 集中定向 | 73 passed / 1 既有 warning，30.38s |
| 全后端 | 1371 passed / 2 skipped / 8 既有 warnings，88.79s |
| TypeScript / Vite / FE-P1 | PASS；Projects 224.84 kB raw / 72.94 kB gzip |
| OpenSpec 全量 strict | 30/30 PASS |
| 范围 Ruff / Node syntax / diff-check | PASS |
| 独立窄 SPEC/plan 与 implementation | APPROVE，仅本批 |

复核未重跑门禁，采用已读取的执行证据并独立审实现。之后追加六个像素/对齐回归，不改实现。Chromium renderer 的自动化测试不等于产品 UI browser acceptance；确定性只针对实测配置，不宣称跨操作系统一致。浏览器 route/CSP、禁后台请求、黑洞 proxy/DNS、禁非代理 WebRTC 和 sandbox 是防御边界，不冒充操作系统防火墙隔离验收。

实际测试命令为在单次命令中显式设置上述四个环境变量后，执行 `cd apps/api && .venv/bin/pytest -q`，定向命令为 `.venv/bin/pytest -q tests/test_f7_local_graphic_renderer.py tests/test_f7_media_renderers.py tests/test_f7_renderer_capabilities.py`。未设置时仅跳过需要真实浏览器的测试，缺配置 fail-closed 测试仍运行；不能把 skip 当作真实 renderer 验收。

## 待完成

多字体/样式映射及中文实际排版验收、普通用户 exact-scope verification、Graphic Studio preview/accept/final-bind UX、真实 Video 输出、F7 全部真实 Provider/Publisher 验证和 F8。无 push/deploy/生产迁移/canonical sync/archive。
