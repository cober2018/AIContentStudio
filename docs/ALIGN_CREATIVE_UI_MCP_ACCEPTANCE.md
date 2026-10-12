# Creative Orchestration：第三批页面与本机 MCP 验收

日期：2026-10-04。范围：已批准 `align-creative-orchestration-product` 的创作意图、执行包/成果页面、内容优先工作台和受限本机 MCP。不是全 change 关闭验收。

本批新增完成 21 项，累计 **85/147，剩余 62 项**。状态：EXECUTED / REVIEW_PASSED。正式运行库仍未启用本 change。

## 基线与实际改动

基线为 `main@341ead8` 加前三批未提交工作，仍直接在 main 开发。正式库通过只读连接确认 head 为 `f7d000000001`，没有 CreativeExecution 表。隔离库为 `aco000000001`，本批没有新增表、迁移或依赖。

| 范围 | 文件与实现 | 明确边界 |
| --- | --- | --- |
| 意图 | `CreativeIntentEditor.tsx`、`ContentMasterPanel.tsx`、`ChannelVariantsPanel.tsx` | 有界表单，显式 append-only 保存；Workflow、正文、意图的编辑状态不互相替代 |
| 执行包/成果 | lazy `CreativeExecutionPanel.tsx` | 预览合同、准备任务、精确成果预览、逐项接受/拒绝；准备不执行，接受不改正文 |
| 工作台/队列 | `ProductionWorkspace.tsx`、`ProductionAutomationPanel.tsx`、`ProductionQueuePage.tsx`、`useProductionWorkflow.ts` | 内容优先，高级工作流按需打开；保留旧运行机制；viewer/归档只读；精确执行 deep link |
| MCP | `routers/creative_mcp.py`、`services/creative_mcp.py`、`main.py` | 同进程 loopback JSON Streamable HTTP，独立 token/既有 owner，白名单工具与受限资源 |
| 共同门禁 | `creative_executions.py`、`creative_packages.py`、`project_events.py`、`creative_intents.py`、Variant 服务/router | 同一 CAS/ProjectEvent/AuditLog；领取证据持久化；检查点/对账绑定；有界敏感内容检查；Variant profile CAS |
| 性能门禁 | `scripts/check-bundle.mjs` | Execution/Automation 动态边界可检查，不把 TipTap/XYFlow 放回默认工作台首包 |

```text
内容 Master / 渠道 Variant + 显式创作意图
                     ↓
      预览并冻结 Execution Package / 输出合同
                     ↓
           用户 prepare（不 dispatch）
                     ↓
     受限 MCP Agent claim → materialize → start
                     ↓
       progress / checkpoint / unknown → 明确对账
                     ↓
             immutable output attempts
                     ↓
       页面逐项审阅 / 拒绝后同槽位补交替换
                     ↓
        MaterialRevision + 明确的项目素材引用
                     ↓
     另行显式绑定并保存 Master / Variant（不自动）
```

## 隔离 API 与浏览器证据

实际 API/Web 使用 `127.0.0.1:15401/15402`，数据库/素材位于 `/tmp/aics-align-ui-mcp.cVc6Qr`。调用真实 FastAPI/domain/storage，输出为受控 PNG/文本夹具；不是真实模型、专业编辑器或公开发布验收。

| 检查 | 实际结果 |
| --- | --- |
| Master 意图 | 普通表单、显式保存、刷新持久化；双窗口 CAS 409 后输家本地内容仍保留 |
| Variant 意图 | 保存产生新 Variant，payload hash 和精确 refs 不变，Master 不变；刷新可读；不重新运行 adapter |
| 执行包 | 当前来源、冻结输入/权利、输出合同预览与 prepare；折叠再打开保留本地表单，不 dispatch |
| 图片成果接受 | 页面预览使用授权 API 的精确字节并验证 SHA256；MCP 实际 claim/materialize/checkpoint/start/submit 后人工接受为 MaterialRevision/项目引用；Master ID/hash 不变 |
| 多输出替换 | 合同为图片 1 份、字幕至少 2 份；单份字幕不能完成；拒绝必需槽位后 blocked，补交同 index 更高 attempt，旧 rejected 行保留；三个必需成果接受后整单 accepted |
| 同记录读取 | 重复点当前 Package/Execution 不清空详情；Variant 同 ID 保留 checks；明确确认“重新读取”则丢弃本地 dirty draft 并恢复当前版本 |
| 高级工作流 | 默认工作台不显示 Workflow；显式打开 Advanced 后原 Run/Inspector/保存控件仍可读，本次不执行真实 Run |
| 队列 | 仅 GET 读取，不创建或恢复任务；deep link 打开精确 Project/Unit/Execution，原生任务保留字符串 ID |
| viewer / 归档 | owned 历史可读，Master/意图/包/prepare/高级操作只读；读取角色失败也不允许写入 |
| MCP 安全 | token、Host、Origin、forwarded headers、外来 ID、参数/深度/体积/响应上限、错误脱敏通过；没有正文/审批/发布/SQL/任意路径工具 |
| 审计/领取 | prepare 幂等重放不新增事件；UI/API/MCP 同事务记录；隔离删除 AuditLog 后 durable ProjectEvent 领取证据仍允许合法进度写入 |
| 检查点/对账 | 未领取不能写实际 checkpoint；绑定 exact execution/package/hash/executor/revision；外来执行者对账 409；verified/succeeded 无观察证据 422；更换 checkpoint 不继承旧 verified 证据 |

页面关键链路零 page error。截图位于上述临时目录，文件名包括 `intent-browser.png`、`execution-browser.png`、`replacement-browser.png`；仅作为本次隔离证据，不是正式素材。

验收结束后已停止仅本批启动的 15401 API 与 15402 Web；保留隔离库/素材/截图证据，正式 API/Web/Worker 未停止或重启。

共享敏感文本检查曾在连续字母和 `token` 后大量空格上出现回溯耗时。现用明确 scheme 边界及有条件引号空白组，保留 credential URL/API key/Bearer 等拒绝语义；31×8192 字符空白扫描从 4.564 秒降至 0.0126 秒，254119 字节真实认证 ping 为 0.1458 秒。解析/检查也放在线程池，不阻塞 API 事件循环。

## 最终门禁

| 门禁 | 结果 |
| --- | --- |
| 全量后端 | 最后安全修正后 1660 passed / 28 skipped / 8 existing warnings，88.63 秒 |
| TypeScript / Vite / FE-P1 | PASS |
| `/projects` initial JS | 225.02 kB raw / 73.00 kB gzip，低于 250/80 预算 |
| 通用 Production | 278.49 kB raw / 89.18 kB gzip，无 TipTap/XYFlow |
| Execution / Automation lazy closure | 261.32/84.59 kB、294.69/94.83 kB（raw/gzip）；均不进入通用首包 |
| Text / Variant lazy closure | 605.24/189.39 kB、294.92/95.05 kB；Text 独占 TipTap |
| OpenSpec strict | 35/35 PASS |
| Ruff | PASS |
| tracked / owned-untracked diff-check | PASS，覆盖本 change 新增文件 |
| F8 ownership | 13/13 SHA256 一致，根 README/progress/findings/task_plan 未覆盖 |
| 独立 SPEC / Python / TypeScript | APPROVE，限定本批实施范围；不冒充复跑全量命令 |
| 独立安全复核 | APPROVE，执行者对账与两个回溯模式修正均已定向复核 |

最终后端命令在 `apps/api` 执行，使用预先初始化的隔离测试库：

```bash
APP_ENV=test DATABASE_URL=sqlite:////tmp/aco-stage3-HRe8tT/final-suite.db AI_STUDIO_MEDIA_ROOT=/tmp/aics-align-ui-mcp.cVc6Qr/final-test-media .venv/bin/python -m pytest -q
```

沿用既有 suite 和临时内联 API/浏览器红绿断言，没有新增永久测试文件或测试用例。安全复核发现的外来执行者对账、检查点证据继承和慢正则均以临时实际断言先复现再修正。既有模块级 Worker 测试要求独立数据库已有 schema，因此先在该隔离库执行现有 head，不改测试或正式数据库来绕过。

## 未完成与未执行

- Capability Memory 服务/页面/发现复用、Learning bridge、Director-first Video 全链路、接受图片/音频/MP4 后显式保存 Master 的跨层终验、清理策略、Legacy retirement、备份恢复和全 change 最终验收仍未完成。
- MCP 实际 Test Agent 已通过；真实 Codex/Claude 客户端连接、专业 executor descriptor 及真实工具恢复仍待验收。`find_capabilities` 明确 unavailable，不伪装已经实施。
- 正式 SQLite migration、正式 API 启用、凭据配置、本地 commit、push/deploy、canonical sync/archive 均未执行。F8 文件及 F6E 生命周期保持原样。
- 不将受控文件或契约测试描述为 Premiere/AE/Resolve/Photoshop 自动化或生成质量证明。

本轮实际使用 using-superpowers、openspec-apply-change、writing-plans、executing-plans、brainstorming（复用已批准设计）、subagent-driven-development、dispatching-parallel-agents、test-driven-development、systematic-debugging、requesting-code-review、receiving-code-review、verification-before-completion。测试编写限制优先，红绿验证仅临时断言与既有 suite。
