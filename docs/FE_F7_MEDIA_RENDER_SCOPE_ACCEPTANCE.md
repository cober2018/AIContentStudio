# F7 Media Renderer 精确范围验证与执行验收

## 需求背景与目录

依据 F7 renderer verification 与 exact acceptance 长期契约，本批闭合 5.11/7.5/7.6/7.7。范围为通用媒体协议＋已显式配置的实际 Graphic Chromium 路径；真实 Video 自动 renderer、外部生成/TTS/ASR/Publisher 仍未完成或未配置。F7 **90/105**，F8 尚未 apply，不以本批替代全产品终验。

- `apps/api/app/services/media_renderers.py`：stage/readback 验证、scope/runtime/Profile predicate、独立 verified execution 和撤销。
- `capability_integrations.py`：保持旧 Text deterministic/manual 边界，媒体验证分派至实际 typed executor。
- `provider_media.py`：per-stage operation lock，短暂 global cache 读取/提交校验，接受不等待 DB 时持 global lock。
- `apps/api/app/routers/product_settings.py` / `content_masters.py`：管理验证/撤销与 editor 输出入口。
- `apps/web/src/product/GraphicRenderPanel.tsx`：独立 lazy 验证/撤销、editor request；`ProviderMediaPanel.tsx` 保持明确许可接受。
- 测试：`test_f7_media_renderer_verification.py`、`test_f7_media_renderer_ui.py`；实际 browser 脚本复用 `fe-f7-graphic-render-browser-acceptance.mjs`。

## 关键设计

```text
admin real stage + explicitly confirmed exact input/output hashes
 → current source/context/bytes/rights/runtime/Profile check
 → append existing CapabilityVerification (renderer_output, 24h)

editor explicit media-render-outputs
 → exact active scope check → one real render → scope/source check
 → non-durable actor stage → explicit license acceptance
 → scope/source/rights recheck + registration write lock
 → exact MaterialRevision + Project reference only

revoke → append event → block new execution/acceptance
historical Master / Candidate / accepted bytes remain immutable
```

只读库存仅读 loaded safe declarations 与 recorded scope/expiry。`not_probed / verified=false / executable=false` 是 GET 当前运行环境未经探测的诚实状态，不否认历史验证。`can_request_execution` 不是执行成功承诺，服务端每次检查当前 runtime。

验证不重渲染、不接受素材、不保存 Master、不自动 attestation；真实 bytes 的许可仍需独立人工确认。execution mode 是服务器冻结字段，客户端不支持提交它。未知结果不自动重试。配置/代码/Profile/expiry/revocation 漂移拒绝，无 admin-preview fallback。

### 锁顺序

accept/verify 先短暂读取 cache，退出 global lock 后获取 per-stage operation lock 与 DB 来源/registration 锁；提交边界短暂 cache 重验 actor/TTL/同一 stage/bytes。render rollback 后才写 cache。revoke/verified accept 共用 registration 写锁直到提交。

SQLite 真实文件库、两独立 Session/thread 的回归让 revoke 持写锁，accept 进入 owned_unit DB 边界；此时全局 cache 可获取，释放 revoke 后 accept 拒绝且零 Material，旧 verified 行未改。该证据不等于真实 PostgreSQL 并发验证。late browser 回归延迟真实响应交给 UI，不宣称 Renderer worker 双连接竞争。

## 实际门禁

- 缺失接口首次 17 失败；新增锁序检查首次失败。实现后新 verification/锁序测试 22 项及 inventory 4 项通过。
- 最新集中定向：**106 passed / 1 既有 warning（5.76s）**，包括后补强的 DB 等待点。
- 显式实际 Node/Playwright/Chrome/字体环境全后端：**1400 passed / 2 skipped / 8 既有 warnings（94.32s）**。该轮后仅补强测试等待点，由上述最新定向复跑覆盖；业务代码未再改。
- TypeScript/Vite/FE-P1：PASS；`/projects` 224.84 kB raw / 72.95 gzip，common Production 280.20 / 89.13；GraphicRenderPanel lazy 5.04 / 2.77，无通用 TipTap/XYFlow 污染。
- strict 30/30、范围 Ruff、Node syntax、diff-check PASS。独立 plan、implementation 与新增验收范围只读复核 APPROVE；复核者未自行重跑测试。
- 实际 Chrome 13 gates / zero pageErrors：明确 stage scope 验证、实际 preview 零业务写入、GET503 后不重复 accept、exact ref、local dirty、explicit save/manual confirm/reload、历史只读、迟到响应、viewer、editor actual verified-output、显式 revoke 留史。
- 最终浏览器报告 `/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f7-graphic-browser-YfL1fs/report.json`，说明明确是 local renderer scope verification，不是外部 Provider/account verification。

## 接口、依赖与启动

管理员 `POST /api/v1/settings/media-renderer-verifications` 提交 `stage_id / confirmed / expected_input_hash / expected_output_hash`；只有其未过期真实 renderer stage 可以成功。撤销 `POST /api/v1/settings/media-renderer-verifications/{verification_id}/revoke` 无需缓存仍存在。

editor `POST /api/v1/content-projects/{project_id}/units/{unit_id}/master-revisions/{master_id}/media-render-outputs` 提交 exact renderer key/version、Master payload/context hash、canvas 与 output MIME；与 admin-only `media-render-previews` 分离。输出继续复用 `/provider-media/{stage_id}/raw` 和显式 `/accept`。

依赖/四个显式 `GRAPHIC_RENDER_*` 设置沿用 `FE_F7_LOCAL_GRAPHIC_RENDER_ACCEPTANCE.md`，不将任何本机 Codex runtime 路径写成应用默认配置。无新表/迁移，仅已有 f7b head。

在 `apps/api` 明确上述真实 runtime 后运行 `.venv/bin/python -m pytest -q`；定向为本批两测试文件与既有 `test_f7_media_acceptance.py / test_f7_media_renderers.py / test_f7_renderer_capabilities.py`。前端 `npm run build`。browser 脚本沿用隔离保护：15670 API、15671 Vite、`F7_ISOLATED_ACCEPTANCE=yes` 和临时 SQLite `F7_ACCEPTANCE_DB`，实际复用 `/tmp/aicontent-f7-media.10l2Ot/studio.db` 与子目录 `media`。

## TODO / 授权边界

仍需真实 Video Renderer、生成/TTS/外部 ASR/账号绑定 immutable Publisher、F7 全阶段验收与 F8。中文/字体样式覆盖限制不变，不伪造 Vendor 验证。没有 remote account effect、push、deploy、生产 migration、canonical sync/archive。
