# FE-F6A 最终验收与交付边界

日期：2026-09-28。最后实施基线：本地 `main@703d6c5`；最终提交以 `git log -1` 为准。本轮只完成已批准的 FE-F6A，不开始 F6B 或后续切片。

## 需求背景与完成范围

生产核心从旧 Draft/MotherRevision 中心扩展为不可变 ContentMasterRevision，保留原工作流、审核、授权与交付链路。最终实施任务为 214/214；规格尚未同步主规格或归档，按任务 21.9 等待单独授权。

已验证完整链路：

```text
固定 Identity / Brief / Fact Boundary
  → append-only Master + 精确素材/证据引用
  → 当前输入绑定的检查 + 真实 render
  → Candidate manifest v4
  → exact-hash Content Approval
  → Delivery Authorization
  → 本地成品 ZIP
```

手工 Text Master 不需要 Draft、TopicBrief、MotherRevision 或 WorkflowRun。Graphic/Video 只在真实文件、精确输入和显式人工 render attestation 验证后可冻结，不伪造生成器成功。

## 目录结构与关键决策

- 标准 change：`openspec/changes/fe-f6a-production-core-content-master/`。
- 后端：`services/content_masters.py`、`production_modalities.py`、`candidates_v4.py`、`production_validation.py`、`production_packages.py`；既有 Project Review、Outputs、Overview、Versions 继续作为真源或投影。
- 前端：ProductionWorkspace / ContextHeader / WorkflowMiniCanvas / NodeInspector / AssetDrawer / ContentMasterPanel；三个 lazy StudioShell 仅是最小 Master 编辑壳，不是 F6B/C/D 专业编辑器。
- 回归：沿用 `apps/api/tests/test_f6a_*.py`；浏览器脚本为 `apps/web/scripts/fe-f6a-browser-acceptance.mjs`。

Workflow 与 Master 的 dirty/save 独立；图文、视频 diff 不计算假文本相似度。新审批/新授权要求当前 Master；已有授权只交付原冻结历史，并继续受实时权利、精确字节和检查约束。v4 失败不得回退 v3/v1。Unknown/reconciliation 保持最高异常优先级。

## 最终门禁：实际运行结果

| 门禁 | 结果 |
|---|---|
| 全量后端 | 753 passed，6 项既有 warnings，32.06 秒 |
| F6A 定向覆盖 | 206 项已收集，全部包含在上述全量运行中 |
| 真实 PostgreSQL | 两项约束/非破坏回退及并发撤权锁测试执行通过，非 skip |
| TypeScript / Vite / FE-P1 | PASS |
| OpenSpec 全量 strict | 24/24 PASS |
| 相关 Ruff / diff-check | PASS |
| SQLite 迁移 | 新临时库 head → f5c000000001 → head PASS |
| PostgreSQL 16 迁移 | 独立临时库 head → f5c000000001 → head PASS |
| 独立 SPEC / backend / frontend-review-package | 全部 APPROVE；发现项已修正并复核 |

初始 JS 预算结果（raw / gzip kB）：

| 路由 | raw | gzip |
|---|---:|---:|
| /projects | 224.68 | 72.86 |
| /assets | 257.70 | 82.41 |
| /settings | 229.76 | 74.96 |
| /learning | 252.10 | 81.79 |
| Production | 254.44 | 82.27 |

Production 与上述轻工作区无 TipTap/XYFlow 首包依赖；没有新增运行依赖，也没有把这些实测数值改成未经授权的永久预算。

## 浏览器验收：20.1–20.14

实际浏览器点击保存、刷新、检查、冻结、审批、授权、下载 ZIP；API 仅用于隔离环境准备及结果回读。

| 任务 | 已验证行为 |
|---|---|
| 20.1–20.3 | Text / Graphic / Video 保存 revision、刷新后准确回读 |
| 20.4 | 并发保存 409；保留未保存编辑，显式加载当前版本 |
| 20.5 | Brief 前进后旧 Master stale；显式另存新上下文版本 |
| 20.6 | 真实持久化 Workflow Draft Output → 浏览器 seed；Run/Attempt/Output 精确血缘 |
| 20.7–20.9 | 三形态检查与 v4 Freeze；图文/视频需要精确真实 render |
| 20.10–20.11 | 三形态 Preview / Changes / Checks、Approval、授权、本地 ZIP 下载和清单核对 |
| 20.12 | 新 v4 创建后，历史 v3 正文、manifest、hash 不变且只读 |
| 20.13 | 真正启动 Run、Human 完成、单节点/从这里重跑、刷新后 Attempt 历史仍在 |
| 20.14 | 三形态导航；Master 保存不清 Workflow dirty，Workflow 保存不清 Master dirty |
| 额外只读回归 | 归档项目的 Master、设计、覆盖、默认、Run、rerun 控件禁用；历史可读 |

最终浏览器报告（本机临时证据，未提交生成物）：
`/var/folders/g6/h9g70y1957s6_qn5hx6480nm0000gn/T/aicontent-f6a-browser-evidence-KFiSr7/report.json`。
报告包含 13 个 gate，`consoleErrors = []`，并保留截图、实际下载 ZIP、真实 PNG/MP4 文件。

Workflow AI provider 显式使用 mock；验证的是实际引擎执行与持久化，不代表真实 AI 服务或远端发布验收。图文/视频使用真实编码媒体及明确人工确认，不宣称自动渲染能力。

## 审计修正与回归对应

- 精确 live Material/Evidence 行锁：真实 PG 两会话证明撤权写入会等待；避免批准/打包窗口竞态。
- 嵌入引用、路径与存储 bounds：只能引用已声明的精确资源；标题/role/slot/order 进入存储前校验。
- Warning：处置绑定准确 latest Check ID、input hash 和 report；W1 处置不能沿用于 W2。
- content_form：旧 form live context CAS 与新 form context 冻结分开，正常修改不误报 409，也不绕过上游漂移。
- Review：schema 先分派，旧 v3 各形态仍显示原冻结正文。
- Stale checks：过期 Master 不能追加检查；历史包按冻结输入查 latest，同输入新 blocker 仍阻断。
- 归档 UI：先新增浏览器断言，实际复现“另存默认”按钮未禁用，再统一 readOnly 并通过完整回归。

任务 19/22 的对应回归包括 persistence/CAS、Draft mapping、modality adapters、manifest、freeze、v4 delivery、Project outputs/read models、warning dispositions、PostgreSQL constraints；既有 F2–F5 测试也在全量运行中通过。

四份 MODIFIED delta 的旧要求/场景均保留：F2 2/4、F3A 2/11、F3B 1/5、F4 5/13（要求数/旧场景数）。仅明确扩展实际 v4 Master 来源，不删除原历史契约；canonical 本轮保持原状。

## 待完成与明确禁止

- 待单独授权后同步五份 delta 并归档；本次只达到 ARCHIVE_READY，不擅自执行。
- F6B 及以后必须先出具体方案并确认；本轮不设计或实现专业编辑器、真实 Connector、新 Publisher。
- 未 push、deploy 或运行生产 migration；本地验收不等于生产就绪。
- 依赖及启动沿用根 README。浏览器脚本仅允许指定 loopback 端口及显式隔离标记，必须先启动迁移后的临时库 API/Vite；不要指向开发或生产库。
