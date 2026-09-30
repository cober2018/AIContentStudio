# FE-F6E 隔离验收记录（本地门禁通过）

## 范围与环境

- 需求背景：验证 `ContentMaster → ChannelVariant → Candidate v5 → 审批 → 人工本地包`，不把旧 V1 全渠道、真实账号发布或 F7 Provider 算作 F6E 已完成。
- 目录结构：规格在 `openspec/changes/fe-f6e-channel-variants-content-matrix/`；后端在 `apps/api/app/services/channel_variants.py`、`candidates_v5.py` 与相关路由；前端在 `apps/web/src/product/ChannelVariantsPanel.tsx`、`ProjectReviewCenter.tsx`；浏览器脚本在 `apps/web/scripts/fe-f6e-browser-acceptance.mjs`。
- 隔离方式：临时 SQLite `studio.db`、独立媒体目录、仅本机 API `127.0.0.1:18263` 和前端 `127.0.0.1:15663`；没有访问开发默认数据库、生产数据库或远端发布服务。
- 本轮可读证据：`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f6e-browser-evidence-7GTB0B/report.json` 及同目录五个实际下载的 ZIP。临时路径不是长期归档；可用脚本在新隔离库重跑。

## 实际闭环

| 验收门槛 | 结果 |
| --- | --- |
| Matrix 只读建议、仅勾选一项确认 | 页面读取建议不新增 Unit；明确确认后恰好新增一个 Unit，没有创建 DeliveryTarget |
| 同一 Text v2 Master → 公众号文章、X 推串、X 单条 | 三个目标各自经真实浏览器预览、显式保存、检查、v5 Freeze、人工 warning 处置、审批、授权、ZIP 下载；公众号从项目共享素材明确绑定精确封面字节 |
| Graphic v2 → 小红书图文 | 未确认最终渲染的来源被拒；绑定当前 render-input 的真实图片后，Variant、v5、Review、审批与本地包通过；ZIP 图片 SHA-256 等于 MaterialRevision |
| Video v2 → 抖音口播脚本 | Variant、v5、Review、审批与本地包通过；含 `estimated.srt`，没有 `.mp4`，清单明确 `finished_video=false`、`remote_call=false` |
| Master / Workflow 编辑隔离 | Text、Graphic、Video 本地未保存编辑在 Variant 预览后仍保留；Text Workflow 草稿仍显示未保存；Variant 只读取 durable Master |
| 安全与历史 | `unknown` 显示待对账且仅对应账号的下载被禁，另一账号仍可取包；Master 新修订使旧 Variant `stale`；图片公开权撤销阻止旧授权包；项目归档后历史可读、Variant 写操作禁用；页面无 JS error |

浏览器首次跑通时发现 v5 审批页漏列来源 Master 的三条 warning，后端正确拒绝了未处置审批。修正页面显示后重跑上述全链路，后端 Gate 未降低。另发现无封面 Text Master 无法在原前端完成公众号包，因此增加项目可见图片的显式精确封面选择；X 两形态继续使用同一无封面来源，不静默丢弃来源素材。异步候选读取和授权后刷新都以选中项为准，隔离脚本实际注入迟到响应并验证不会覆盖当前选择。

## 旧 V1 superseded change 的七项场景对照

旧 `complete-prd-v1-channel-deliverables` 保持 superseded 状态，只作验收来源，不重新激活或自动关闭 V1。

| 场景 | 当前证据和限制 |
| --- | --- |
| 历史抖音/小红书稿缺新审批证据 | 旧 Candidate 仍可读，v5 不能由 Draft/Master 隐式回填；后端历史和 sole-source 回归覆盖，旧稿不自动获得 F6E 就绪状态 |
| 已批准抖音脚本下载 | 隔离浏览器实得 script-only ZIP、估算 SRT，清单无成片/远端发布声明 |
| 小红书只有 Prompt、图片缺失 | 隔离浏览器与后端均拒绝无确认渲染的图文适配；不得以 Prompt 冒充图片 |
| 图片顺序或字节改变 | 后端清单/精确媒体与哈希回归；隔离浏览器校验实际 ZIP 图片 SHA-256，撤权后旧包不可下载。更细的多卡片重新排序与字节篡改已由 API 定向回归承担，不冒充本轮浏览器逐项覆盖 |
| 两账号独立交付 | 后端 `test_v5_local_targets_keep_account_identity_and_unknown_reconciliation_separate` 覆盖双账号、一方 unknown、另一方继续取包；浏览器验证 unknown 待对账，不宣称真实远端发布 |
| 素材/证据公开权撤销 | 后端证据和素材负例、浏览器图片撤权阻断已有本地包；冻结审批历史保持可读 |
| 查看 V1 总体状态 | 本记录只标记 F6E 五种首批受控形态的本地路径，不把旧 V1 整体或全部平台/形态标为达标 |

## PRD §15/§16 边界

PRD §15 的 15 项横跨 Source 导入、事实确认、旧 Topic 三渠道生成、模型/Prompt 血缘、Checker、Reviewer、资产库、导出、重试、数据库隔离。F6E 当前只直接证明新版项目路径中的受控适配、冻结、人工审核、精确导出和历史证据不被覆盖；不能由五种 Variant 推断其余旧 Topic 验收项已逐项通过。

PRD §16 的 **30 个真实 Topic（10 抖音、10 小红书、10 公众号）**、六项评测指标、真实账号发布、部署/恢复/备份门槛本轮均未执行。临时夹具不是“真实 Topic”。F6E 完成不等于 V1 发布门槛达标。

## 待完成与启动

- 本地门禁：后端 `1188 passed / 2 skipped / 7 warnings`；前端 TypeScript/Vite 与 FE-P1 通过，`/projects` 224.75 kB raw / 72.89 kB gzip，Channel Variants lazy closure 234.19 kB raw / 76.03 kB gzip；OpenSpec strict 30/30、Ruff、`git diff --check` 通过。隔离 SQLite 与临时 PostgreSQL 16 均验证迁移 up/down/up，后者仅使用本机临时容器，未触及生产库。独立 SPEC、backend/security、frontend/Review/package 定向复核均给出 APPROVE，问题已修复并回归。
- 待完成：F6E 主规格同步/归档仍须单独授权；push、deploy、生产迁移均未获授权，也不属于本地验收。本地功能提交见仓库历史，不把临时浏览器夹具视为长期业务数据。
- 依赖与启动：使用现有 API `.venv`、Node/Vite、Playwright、Chrome、ffmpeg 和 `unzip`。脚本要求 `F6E_ISOLATED_ACCEPTANCE=yes`、固定本机端口、`F6E_ACCEPTANCE_DB=sqlite:////tmp/aicontent-f6e-acceptance.<suffix>/studio.db`、匹配的 `AI_STUDIO_MEDIA_ROOT`；先对临时库执行 Alembic `upgrade head` 并种入 `seed_v1_channel_profiles`，再启动 API 与 Vite。脚本只在这些隔离条件全部匹配时运行。
- 关键设计决策：本地包不是平台已发布；`unknown` 不自动重发；项目只引用精确素材版本，实时撤权在包读取时仍生效；历史 v1/v3/v4 不向 v5 隐式迁移。
