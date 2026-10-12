# Director-first、渠道变体与成果绑定实施计划

> **For agentic workers:** Use executing-plans / subagent-driven-development within the already approved align-creative-orchestration-product change. No new proposal, live migration, commit or external dispatch.

**Goal:** 把已接受成果明确接回内容，完成日常视频导演入口、五种渠道正文编辑及可审计暂存清理。

**Architecture:** 复用 F6D Video v2、F6E Variant revision、MaterialRevision、ProjectEvent；不新增表或新的内容真源。包/暂存/接受/正文保存/冻结/审批仍是不同动作。所有验证在一致备份的临时 SQLite 和本地素材副本中执行。

**Tech Stack:** FastAPI/SQLAlchemy/SQLite，React/TypeScript/Vite，既有本机 StorageProvider 和受限 MCP。

## 范围

本批目标任务 6.9、7.6、7.7、7.9、12.3–12.9、13.1、13.5；仅在实际验证完整时勾选。9.x executor recovery、真实 Codex/Claude client、重复编辑偏好、Legacy retirement、全 change final gate 保留后续，不能借用本批证据提前完成。

## 文件与责任

- Video worker：`apps/web/src/product/VideoStudioShell.tsx`；必要时相邻仅视频组件。导演日常脚本/镜头/配音/字幕/封面优先，旧时间线/叠字/最终渲染进入显式 advanced。所有既有控件保留，v1/upgrading/history rules 不变。项目素材显式刷新不改 dirty draft。
- Variant worker：`apps/web/src/product/ChannelVariantsPanel.tsx`，必要时新的仅 Variant 表单组件。五种已批准 schema 的有界文本字段编辑，稳定 IDs/顺序/精确 refs/citations/declarations 原样保留；沿既有 manual_edit CAS 保存新 revision。历史/外来/归档/漂移不写，409 保留本地正文和意图。
- Cleanup worker：`apps/api/app/services/creative_execution_files.py`、`creative_executions.py`、`routers/creative_orchestration.py`；必要时 `CreativeExecutionPanel.tsx` 的明确清理操作。无后台 TTL、无递归删除、无任意路径：仅明确选择本 execution 的已拒绝或终态非接受暂存副本；accepted 副本仅在验证正式 Material bytes 后清理。Unknown/未解决 blocked/staged 不能清理。历史输出行不删除，ProjectEvent 记录意图/结果，失败可重试且不假称完成。
- 主 agent：计划/记录、ProductionWorkspace 集成、Home projection、Candidate frozen external provenance/Review 展示、隔离夹具/API/浏览器/现有门禁。与 worker 写集不重叠。

## 步骤 ///

- [x] /// 1. 计划独立复核；固定 HEAD、F8 13 文件 hash、正式只读 schema。使用 `/tmp` RED 验证当前缺失的正文编辑/导演入口/清理，禁止新增永久测试。
- [x] /// 2. 并行完成 Video 与 Variant 的最小日常表单，Cleanup 受限服务；主 agent 完成 authoritative Home/action risk projection，不新增任务表。
- [x] /// 3. 清理只针对服务端解析的 exact staging key，O_NOFOLLOW/regular inode/hash 检查，拒绝路径逃逸；同一 CAS/并发保护内检查该 key 的全部 output/attempt 引用，任何待接受引用仍需 bytes 时禁止删除，覆盖已拒绝＋待接受及已接受＋待接受共用 key。数据库 CAS/审计先约束目标，磁盘失败明确记录，不删 Material storage。重复清理回读同一结果，历史接受/拒绝关系不变。
- [x] /// 4. 外部素材 provenance 仅从精确已接受 MaterialRevision 真源投影进冻结 v4/v5；Review 从 frozen manifest 展示安全 package/execution/output IDs/hash，不读取或审批 raw result_ready。保持旧 manifest 不变。
- [x] /// 5. 浏览器/API：五种 Variant 编辑+保存/刷新/409，Master 与 sibling hash 不变；image/audio 接受→明确绑定→保存；Video 无 render 保存→Director Package→Test Agent MP4→人工接受→刷新素材→绑定→保存→attestation→checks→Candidate v4→Review/Approval/local ZIP。生成受控真实可读 MP4/WAV/PNG，不是真实专业工具/付费模型。
- [x] /// 6. 对比重构前后历史 Video Candidate/ZIP bytes/hash；旧 v1/v2只读/升级、viewer/归档、Workflow 与 Master dirty 独立；原生 image/TTS/ASR 入口仍可达，不调用真实 provider。
- [x] /// 7. 临时拒绝/终态 cleanup、symlink/foreign/hash/drift/unknown/blocked/权限/accepted byte 保存负向断言；Home 风险优先级和精确 deep link，读取不 dispatch。
- [x] /// 8. SPEC 定向复核→实现/安全/TypeScript 复核→修正后重验；既有 full backend、TypeScript/Vite/FE-P1、OpenSpec strict、Ruff、tracked 与 owned-untracked whitespace/F8 hashes。
- [x] /// 9. 更新 change task_plan/progress/findings/README 和本批验收，报告准确任务数/限制；不改根 F8 文档，不移除旧导航，不归档未完成 change。

验收：本批 13 项完成，累计 122/147；详细证据及尚未执行边界见 `docs/ALIGN_CREATIVE_DIRECTOR_VARIANTS_ACCEPTANCE.md`。

## 边界

直接本地 main 开发为用户已授权。正式 SQLite 仍未升级，不重启正式 API/Web/Worker。清理的文件不可恢复，必须 UI 明确确认并保留历史审计；仅本次临时夹具可实际删除。输出接受不自动保存 Master，绑定只改本地 draft，用户另行明确保存。若需要新增 durable business object/削弱 rights 或 Candidate gates，按 0.6 停止。
