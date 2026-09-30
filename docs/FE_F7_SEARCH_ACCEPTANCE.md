# F7 受控素材搜索批验收

## 范围与产品契约

公共搜索 → 安全候选 → 明确下载 → 临时预览 → 核对许可/署名/权利 → 明确接受 → 精确 MaterialRevision/可选项目引用。

没有新增表或迁移，没有 Master 自动写入。首次实现 Commons 单一受控来源；PNG/JPEG/WebP，元数据 1 MB，下载 5 MB，最多 10 候选；actor 候选 15 分钟过期，重启失效。适配器只观察许可，不提供法律或平台验证结论。

## 实际门禁

| 验证 | 结果 |
|---|---|
| 搜索/接受/能力定向 | 64 passed |
| 全量后端 | 1270 passed / 2 skipped / 8 existing warnings，51.82s |
| TypeScript/Vite/FE-P1 | 最终重跑 PASS；/projects 224.84 kB raw / 72.94 gzip，/assets 258.81 / 82.80 |
| OpenSpec strict | 30/30 |
| 范围 Ruff / diff-check | PASS |
| 隔离搜索浏览器 | 4 gates，0 page error |
| 原生成浏览器回归 | 4 gates，0 page error |
| 独立复核 | 超长署名 blocker 修复后窄复核 APPROVE |

浏览器首次发现许可 select 标签包含选项文本而不精确，补 aria-label 后重新验收通过。超长署名、畸形 URL、异常 MIME/SHA1 均有拒绝回归；未知许可不可接受，许可/署名不能在接受时替换。

## 证据与限制

- 搜索：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-search-browser-pwjgVU`。
- 生成：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-media-browser-nqhsBn`。
- 隔离 SQLite/media：`/tmp/aicontent-f7-media.MPIOsP/`。
- 浏览器使用明确隔离 Provider 和实际 PNG 字节，不代表外部 Commons/生成 Provider 验证。
- 真实 Commons 请求因本机 DNS/保留地址安全门槛被拒；未关闭 SSRF 防护，未取得真实 Commons 成功证据。
- F7 75/105；4.9 跨 Unit 实际消费与 10.2 真实集成未关闭。ASR/Renderer/真实单次 Provider/Publisher/F8 继续待办。
- 参考官方契约：[MediaWiki Imageinfo](https://www.mediawiki.org/wiki/API:Imageinfo)、[Search](https://www.mediawiki.org/wiki/API:Search)。
- 不 push/deploy/生产迁移/canonical sync/archive；本地提交只收本批文件，既有未跟踪规格包不纳入。

## 重跑

API：`.venv/bin/pytest -q tests/test_f7_material_search.py tests/test_f7_media_acceptance.py tests/test_f7_capability_persistence.py`；全量 `.venv/bin/pytest -q`。前端 `npm run build`。

浏览器需使用 guarded `fe_f7_media_acceptance_server`、独立 `/tmp/aicontent-f7-media.<suffix>/studio.db` 与 media，先隔离迁移再启动 18271 API、15671 Vite；脚本 `fe-f7-search-browser-acceptance.mjs` 需 `F7_ISOLATED_ACCEPTANCE=yes`，不连接产品数据或外部 Provider。
