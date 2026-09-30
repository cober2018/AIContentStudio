# F7 Graphic Studio Renderer UI 验收

## 需求与边界

依据已授权 F7 Decision 8 与 Graphic Studio scenario；本批把实际 `graphic.chromium@1` 管理员预览接入产品 UI，不新增表/迁移、不自动验证能力、不代替人工最终渲染确认。F7 仍 86/105；F8 未 apply。旧 Text/Graphic/Video、Provider 生图/搜索接受默认路径保留。

## 目录与设计

- `apps/api/app/services/media_renderers.py`：safe preview inventory，只读 loaded descriptor，不调用 runtime。
- `apps/api/app/services/product_settings.py`：现有 capabilities response 投影该 inventory。
- `apps/web/src/product/GraphicRenderPanel.tsx`：Graphic-only lazy state，绑定当前 saved Master/canvas/actor。dirty/history/stale/read-only 时禁用；请求代次隔离迟到结果。
- `GraphicStudioShell.tsx` / `ContentMasterPanel.tsx`：分开渲染、接受、local binding 与 durable Master save。
- `ProviderMediaPanel.tsx`：Renderer MIME 预览与接受回调；成功接受后 read model 失败只重读，不重复写入。
- `apps/api/tests/test_f7_media_renderer_ui.py`、`apps/web/scripts/fe-f7-graphic-render-browser-acceptance.mjs`：本批 API 与真实 browser regression。

```text
saved Master + selected canvas
  → explicit real PNG preview (no durable write)
  → explicit license acceptance (MaterialRevision + Project reference only)
  → fresh exact Shared Assets revision/hash/live public rights
  → explicit local bind (dirty only)
  → explicit append-only Master save
  → separate manual render-input attestation
```

## 实际验收

- UI 原先没有 Renderer 入口，浏览器首次失败；新增 inventory 两项失败 API 测试后实现，三项 API 测试通过。
- 隔离实际 app.main + Vite + Chrome，无 Renderer mock；数据库 `/tmp/aicontent-f7-media.10l2Ot/studio.db`、媒体子目录 `media`，新库实际 Alembic upgrade head 到 f7b000000001。只为验收临时创建项目、明确 Brief/作者观点 FactPack/边界；不伪造 production evidence。
- 十个浏览器 gate：预览不写库、接受后 GET 失败不重复 accept、精确项目引用、local bind 不保存、显式保存精确 ref/hash、manual confirmation + reload、历史不变、dirty 禁用、actual in-flight output 被 local edit 隔离、同 owner viewer 只读。零 page error。
- 迟到结果回归通过真实 `route.fetch()` 获得渲染响应，再延迟交给 UI 并编辑标题，证明迟到响应不恢复预览；不是 Renderer worker 正在执行时的双连接竞态证明。
- 浏览器报告与截图：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-graphic-browser-v5S1pV/report.json`；同目录 `graphic-render-dirty.png`。
- 全后端显式真实 Renderer 环境：**1374 passed / 2 skipped / 8 既有 warnings，102.66s**。无环境首次运行 1358/18 skipped 不作为实际 Renderer 验收。
- TypeScript/Vite/FE-P1 PASS：`/projects` 224.84 kB raw / 72.95 gzip，common Production 280.20 / 89.13；GraphicRenderPanel lazy chunk 3.43 / 2.15，common Production 无 TipTap/XYFlow。
- OpenSpec `--all --strict` 30/30；范围 Ruff、Node syntax、diff-check PASS。窄独立 SPEC/plan 与 implementation 只读 APPROVE；审查者未自行重跑测试，测试数字来自本轮实际命令。

## 依赖与复跑

显式 Renderer 的四个环境变量、安装要求和字体限制见 `FE_F7_LOCAL_GRAPHIC_RENDER_ACCEPTANCE.md`；不提供任何 Codex 私有路径作为应用默认值。测试设置只对单次本地命令生效。沿用现有 API Python、Node、Vite 和已安装 Playwright/Chrome。

后端：在 `apps/api` 明确配置四个 `GRAPHIC_RENDER_*` 变量后执行 `.venv/bin/python -m pytest -q`。

浏览器脚本要求 `F7_ISOLATED_ACCEPTANCE=yes`、`F7_BROWSER_URL=http://127.0.0.1:15671`、`F7_ACCEPTANCE_DB=sqlite:////tmp/aicontent-f7-media.<suffix>/studio.db`；API 在 15670，Vite 在 15671。Playwright 用已有本地依赖，API 必须是同一隔离库。脚本只在验证过的临时库调整 fixture 用户角色，并 finally 恢复，不访问真实库。

## TODO / 非本批声明

归档/途中 actor 或 canvas 切换只审 guards，没有单列浏览器证明；本批没有 Candidate/Approval/ZIP 浏览器验收。单字体 normal/400 限制不变，中文覆盖、多样式、普通用户媒体 scope verification、真实 Video Renderer、其他真实 Provider/Publisher 与 F7 终验继续。没有 push/deploy/生产迁移/真实远端发布/canonical sync/archive。
