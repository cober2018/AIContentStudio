# 本地客户端、执行恢复与偏好候选实施计划

> **For agentic workers:** Use executing-plans / subagent-driven-development in the already authorized align-creative-orchestration-product change. Preserve F8 ownership. No commit, formal migration, paid generation or publication.

**Goal:** 完成剩余恢复/客户端/偏好/配套备份安全项目，不把受控 executor 当作专业工具。

**Architecture:** 复用 CreativeExecution 原状态/CAS/checkpoint、CapabilityArtifact 的候选与 provenance、既有 Master 显式保存及 SQLite/Material 配套备份。无新表/迁移/依赖，不自动应用偏好或调用执行器。

**Tech Stack:** FastAPI/SQLAlchemy/SQLite，React/TypeScript，已安装 Codex CLI app-server 与既有本机素材存储。

## 本批范围与写集

目标为 8.11、9.1、9.7、9.8、11.5、14.2、14.3、14.4、14.10；逐项有实际证据再勾选。9.8 只记录专业 pilot 在首批范围之外，不以本批夹具声称 pilot 成功。Legacy parity/导航退出和全 change 终验另保留后续。

- 恢复 worker：`apps/api/app/services/creative_executions.py`、`creative_contracts.py`、`apps/api/app/routers/creative_orchestration.py`、`creative_mcp.py` 及 `apps/web/src/product/CreativeExecutionPanel.tsx`。kind/key/version、checkpoint/revert/recover 声明和有界 output kinds 复用已有安全 metadata/投影；声明不是能力验证。旧未声明行为/历史原样兼容，checkpoint/recovery 仍需 exact identity/CAS/readback。
- 偏好 worker：`apps/api/app/services/capability_memory.py`、`apps/api/app/routers/capability_memory.py`、`apps/web/src/product/CapabilityMemoryPanel.tsx`、`capabilityMemoryTypes.ts`。显式选择同一 owned Project/Unit 至少两次已保存内容编辑，服务端核实精确 Master/parent/hash/actor/实际内容变化；首稿、升级、seed、仅 context/intent/attestation 变更和未保存 AI patch 不能当重复接受编辑。只存 project-scoped preference candidate + 安全 revision/hash 来源，不生成 saved/pinned，不改 Identity/事实/正文/其他方法或 Installed Skills。
- 主 agent：change 计划/记录、隔离运行与实际 Codex 本机客户端握手（不发模型 turn）、既有配套 backup/restore 演练、跨层浏览器和门禁。MCP 设置仅进隔离子进程，不改全局 Codex/runtime 配置。
- 独立 reviewer：只读复核计划/SPEC、恢复/偏好实现与 MCP/redaction 边界；不写以上 worker 文件或 F8。

## 步骤 ///

- [x] /// 1. 重新核定 122/147、HEAD、F8 13 文件与正式只读 head；独立复核计划，保持 main 和同一 change。
- [x] /// 2. 先验证现有 descriptor/偏好入口缺口，再在各自写集实施。按用户约束不新增永久测试；既有回归/API/临时受控断言验证。
- [x] /// 3. 隔离 executor 完成 checkpoint→实际临时文件变更→失败/unknown→读取观察→明确 revert/recover→新结果；确认无第二次 dispatch，证据保留新进程读取。
- [x] /// 4. 已安装 Codex app-server 的真实 MCP client initialize/list/read 连接本机隔离服务，不调用 turn/模型或执行域写操作；协议不兼容时修复最窄服务契约，不冒充自写 Test Agent 为 Codex。
- [x] /// 5. 偏好 API/页面显式选择重复保存编辑→candidate→另行人工保存；未保存/伪造/外来/归档/不重复/secret 拒绝，无其他业务状态改写。独立 SPEC 通过后实现复核。
- [x] /// 6. 按既有 backup/restore 路径复制新 durable 表及接受素材到新的隔离目标；对比行/hash/媒体与历史 ZIP，缺 staging 的 accepted 历史可读。不得恢复到用户正式目录。
- [x] /// 7. 汇总 read-only inventories 零 dispatch、合成 secret 拒绝/日志安全、MCP 工具白名单与错误投影。记录专业工具和质量未验证，不发真实外部请求。
- [x] /// 8. 修正后全量后端、前端/FE-P1、strict、Ruff/diff/F8 hash；更新本 change README/task_plan/progress/findings 和验收。停止仅隔离进程，不提前 canonical sync/archive 或本地提交。

第六批 EXECUTED / REVIEW_PASSED；新增 9 项，131/147。实际证据、独立复核、修正后门禁与限制见 `docs/ALIGN_CREATIVE_RECOVERY_PREFERENCES_ACCEPTANCE.md`。余下为 Legacy parity 与整 change 收尾，不执行 professional pilot 或正式启用。

## 停止条件

如需新 durable 对象、破坏历史/权利或任意后端代码执行，按 0.6 回规格层；不偷偷扩大范围。正式库 migration 与 compatibility 页面删除须后续单独授权。图示：保存编辑→显式偏好候选→独立人工晋升；unknown→观察→明确恢复，而非自动重发。
