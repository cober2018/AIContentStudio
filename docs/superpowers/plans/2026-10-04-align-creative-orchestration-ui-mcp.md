# Creative Orchestration 页面与本机 MCP 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development / superpowers:executing-plans。按独立文件分组并行，不逐项向用户确认。

**Goal:** 从 64/147 基线完成创作意图、冻结执行包、逐成果人工接受的页面及受限本机 MCP。Capability Memory 服务和最终正式库启用不在本批。

**Architecture:** UI 复用已有 Master/Variant save 与 CreativeExecution domain；MCP 与 FastAPI 同进程，仅 loopback、独立环境 bearer token 与明确既有 owner ID。接受成果只进入 MaterialRevision/明确项目引用，正文仍另行保存。无新表、迁移、依赖、正式配置变更。

**Tech Stack:** 现有 React/TypeScript、FastAPI/SQLAlchemy、SQLite、本地素材；有界无会话 JSON Streamable HTTP，先验证现有 MCP 2025-11-25 协议兼容，不引入通用 Agent 平台。

## /// 1. 意图编辑（独立前端组）

- [x] 新建 `apps/web/src/product/CreativeIntentEditor.tsx`，普通表单编辑 objective/audience/must_keep/must_avoid/freedom/rationale；未知扩展字段不能静默丢弃。
- [x] 修改 `ContentMasterPanel.tsx` 与 `ChannelVariantsPanel.tsx`：随正常显式 save 提交 intent，dirty/409/history 和归档只读一致；意图修改不隐式升级 v1。
- [x] 运行 TypeScript/现有构建与隔离实际页面验证；不新增永久测试。

## /// 2. 执行包与成果审阅（独立前端组）

- [x] 新建 lazy `CreativeExecutionPanel.tsx`：当前 Master/Variant 来源、输出 role/min-max/MIME/bytes 表单、冻结包预览、明确 prepare；不 dispatch。
- [x] 展示执行历史、精确包 hash/状态/缺少与替换槽位/checkpoint/输入权利；逐成果 rights/license 接受或拒绝，接入原 decision API。
- [x] 只读刷新保留未提交表单；viewer/archived/stale/unknown fail closed；接受不自动绑定正文或冻结 Candidate。

## /// 3. 本机 MCP（独立后端组）

- [x] 新建 `apps/api/app/services/creative_mcp.py` 和 `routers/creative_mcp.py`：同进程 POST JSON Streamable HTTP，initialize/ping/tools/resources，无会话/GET SSE 时返回 405。
- [x] 使用 `AICS_CREATIVE_MCP_TOKEN` 与 `AICS_CREATIVE_MCP_OWNER_USER_ID`，拒绝非 loopback、伪造 Host/Origin、错误 token、未激活/非 editor owner；不从 X-Studio-User 或 email 建号。
- [x] 严格工具白名单：读取有界上下文/包/状态、claim/start/materialize/report/checkpoint/submit/unknown/reconcile/request-review，均调用原 domain/CAS；不暴露 prepare、accept、正文、审批、发布、SQL 或任意路径工具。
- [x] 限制请求/响应大小，稳定脱敏错误与 trace；Capability 服务未实施时不伪装为空的已接通能力。
- [x] 新建 `docs/CREATIVE_EXECUTION_MCP.md`，说明 ignored 环境配置及限制；不得读取/写入真实 bearer token。

## /// 4. 主线整合与共同审计（主 Agent）

- [x] 修改 `ProductionWorkspace.tsx`：内容优先，外部执行 lazy 面板，自动化/工作流显式 Advanced；不改变 Workflow dirty/save/run。
- [x] `ProductionQueuePage.tsx` 精确 execution deep link；复用有界既有项目/单元读取，不新增任务表。
- [x] 在 `main.py` 注册 MCP；为共用 execution 原子写入补齐现有 ProjectEvent/AuditLog，避免 MCP 与 UI 两套审计。
- [x] 收口 claimed 后 checkpoint 的精确 execution/package/executor 绑定与可信观察要求；不增加任意专业工具执行。

## /// 5. 验收与记录

- [x] 在明确临时 SQLite/素材目录运行 Test Agent MCP → 成果 → 人工接受；外来 ID、token/Host/Origin、禁止工具、stale/CAS/秘密与数量合同负向验证。
- [x] 隔离浏览器验证意图保存/刷新/409、包创建/预览/prepare、结果合同/权利表单/接受与拒绝、只读与深链接；新素材绑定正文保留显式 save。
- [x] 后端全量、TypeScript/Vite/FE-P1、OpenSpec strict、Ruff、tracked + owned untracked diff-check；F8 13 文件哈希不变。
- [x] 先独立 SPEC 再代码/安全复核，修正后重新验证。只勾选实际完成项，8.5 Capability 和 8.11 真实 Codex/Claude 客户端未验证时保持未勾。
- [x] 更新 change 自有 README/task_plan/progress/findings 与本批验收文档；正式库仍 f7d000000001，不重启正式 API，不 commit/push/deploy/canonical sync/archive。
