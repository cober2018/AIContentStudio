# Capability Memory / Learning 显式桥接验收

## 需求与范围

2026-10-04 开始，2026-10-05 完成本批。基线为本地 `main@341ead8` 加同 change 前三批未提交改动；没有创建新分支或工作树。

已批准 change：`align-creative-orchestration-product`。本批完成 8.5、10.1–10.16、11.1–11.4、11.6–11.7、14.1，共 24 项；累计 **109/147，38 项未完成**。这是第四批验收，不是整个 change 关单。

第一阶段已有 CapabilityArtifact / CapabilityArtifactRevision / CapabilityUse 表。本批只接服务、API、页面和 MCP，没有新增表、迁移或依赖。正式 SQLite 只读核验仍为 `f7d000000001`，未重启正式 API 或启用新 schema。

## 文件与入口

| 位置 | 本批责任 |
| --- | --- |
| `apps/api/app/services/capability_contracts.py` | NFC canonical document/hash、安全扫描、有界参数和纯文本渲染 |
| `apps/api/app/services/capability_memory.py` | owner/scope、不可变修订、生命周期 CAS、捕获、显式 use/outcome、导入导出 |
| `apps/api/app/routers/capability_memory.py` | 严格有界 API、拒绝重复 JSON 键/非有限值、安全错误 |
| `apps/api/app/main.py` | 注册同进程 router |
| `apps/api/app/services/creative_mcp.py` | `find_capabilities` / `use_capability` 委托同服务，不开放正文/审批/发布 |
| `apps/api/app/routers/creative_orchestration.py` | 成果接受提交成功后，独立捕获可复用方法；失败不撤销已接受素材 |
| `apps/web/src/product/CapabilityMemoryPanel.tsx` / `capabilityMemoryTypes.ts` | 候选/保存/固定/归档、历史、范围、显式复用、结果 CAS、学习桥接 |
| `ProductSettingsPage.tsx` / `ProductionWorkspace.tsx` / `LearningWorkspace.tsx` | 显式打开 lazy 方法库、当前任务适用方法、独立学习候选桥接 |
| `apps/web/scripts/check-bundle.mjs` | 验证三个入口不静态引入方法库，不带 TipTap/XYFlow |

正式启用后的入口为 Settings → 高级运行环境 → 能力方法库；Production → 查看适用方法；Learning 已接受候选 → 明确创建方法候选。本批使用隔离 API/Web 验收，不把代码接线当作正式库已启用。

## 长期边界与实际行为

```text
整单 Execution accepted + 明确可复用内容
    → Capability candidate
    → 人工保存/固定精确修订
    → 所有适用方法与范围同时返回
    → 明确选择 + 参数渲染 + CapabilityUse
    → 可另行回填结果（CAS）

Learning accepted + 已冻结支持证据
    → 独立人工桥接 → Capability candidate
```

- 六类方法使用同一生命周期；candidate 不会因为使用次数变成默认方法。排序不表示优先级，冲突不隐式合并。
- 整单 required-output 合同未接受完成不能捕获；相同内容来自不同 execution 不合并来源，重复同来源才去重。源成果接受与方法捕获分事务。
- Learning 接受不会自动创建方法或 ContentMemory。桥接冻结 accepted revision、决定和安全证据引用，不复制原文；不改变既有发布证据类型。
- owner/persona/account/series/project/channel/executor 范围由后端校验。project/sibling/foreign 边界实测；扩大或改变范围须明确确认。
- 方法修订 append-only；状态、范围和来源保持可追溯。历史修订可读，新使用须当前 saved/pinned 修订。
- use 是确定性返回方法及参数，不执行代码、不注入模型、不改正文/事实/Identity/Workflow/渠道策略。结果记录不是发布表现证据。
- 字符串最多 8192 UTF-8 字节；方法/参数及渲染 JSON 各最多 64 KiB。嵌套文本和键 NFC 后存储/哈希，规范化键冲突拒绝。秘密、凭据 URL、私有原文、执行代码和超界内容整体拒绝，不静默删字段。
- 导入创建新本地 candidate，不复制 owner/状态/来源，不自动固定。Installed Skills 是独立只读清单，不写技能目录或 `skills_enabled`。
- 结果 409 通过 owned `GET /uses/{id}` 回读同一 use/revision，人工核对后才更新 CAS 基线；保留本地选择。延迟回执按身份绑定，读取期间禁止新渲染。方法升级或归档禁止新使用，但原使用记录可继续回填结果。

## 实际隔离验收

API/Web：`127.0.0.1:15411/15412`。SQLite 与素材：`/tmp/aics-capability.lochl9`，实际素材根解析为 `/private/tmp/aics-capability.lochl9/media`。从前批 SQLite `.backup` 复制包含 WAL 的一致快照，未用不含 WAL 的单文件拷贝冒充完整复制。

| 验证 | 最后结果 |
| --- | --- |
| 父层 API 12 组 | 六类生命周期、CAS/history、参数/use/outcome、项目/角色/账号范围、viewer/foreign、秘密、accepted capture、归档、导入、Learning 桥接、不改业务对象均通过 |
| 成果接受接线 | 新执行完成后候选捕获通过；不安全方法捕获失败，已接受 MaterialRevision/执行状态仍保留 |
| 来源去重 | 相同 hash、不同 accepted execution 返回不同 artifact，并保留各自 source FK；同来源重复返回同 artifact |
| 修正后纯契约 | Google/Stripe 合成凭据及 schema 描述拒绝；8192 字节正文正常渲染；等价 Unicode hash 一致；键规范化冲突拒绝 |
| MCP | 实际 HTTP initialize → initialized → exact find/use、foreign scope 拒绝，owned use 回执/foreign404，通过；仍是受控客户端而非真实 Codex/Claude 配置验收 |
| 页面 5 组 | Settings 新建/保存/固定；Production 选择/参数/结果/opt-out 不改 Master；409 保留本地编辑及折叠状态；Learning 显式桥接；viewer 只读 |
| 使用结果追加回归 | 延迟回读期间禁止新使用；409 读取/确认后保留本地选择继续 CAS；归档后旧结果可回填、新 use 禁止；零 page error |

临时断言脚本：`acceptance.py`、`capture_hook.py`、`browser.cjs`、`outcome-green.cjs`；截图 `capability-conflict.png`、`outcome-recovery.png` 均保存在上述隔离目录。它们不是正式素材、永久测试文件或真实生成质量证据。

浏览器外部请求全部阻断。早期 harness 的错误 Settings 查询参数、Master URL、select 标签匹配已按现有实际入口修正；并行创建时的全局计数断言改为 exact source execution 计数。上述失败不通过业务改动绕过。

独立后端执行者另在各自 SQLite 副本做跨进程 lifecycle CAS、同来源 capture 去重、缺表 503、输入/篡改拒绝检查；最后窄修正报告 155 项临时断言和 Ruff 通过。这是执行者证据，不与父层 12 组或全量 suite 混算测试总数。

## 独立复核及最终门禁

计划与 SPEC 复核 APPROVE。独立后端/安全、TypeScript 首轮发现凭据格式、Unicode canonical、渲染预算、结果冲突/历史回填、迟到回执串记录问题；父层先做临时 RED 复现，再窄修正，最后定向源码复核全部 APPROVE。复核不是独立重复运行全部门禁，命令结果由父层实际执行。

| 门禁 | 修正后结果 |
| --- | --- |
| 全量后端 | **1660 passed / 28 skipped / 8 existing warnings，89.87 秒** |
| TypeScript / Vite / bundle | PASS |
| Projects initial JS | 225.02 kB raw / 72.99 kB gzip，保持 250/80 预算 |
| Home / Learning / Assets / Settings | raw 231.86 / 253.53 / 262.14 / 240.65 kB，均无 TipTap/XYFlow |
| 通用 Production | 279.51 kB raw / 89.40 kB gzip，无 TipTap/XYFlow |
| Capability lazy closure | 260.21 kB raw / 83.78 kB gzip；不进入通用或其他一级入口首包 |
| OpenSpec strict | 35/35 PASS，文档收尾后再核对 |
| Ruff | 本批六个 Python 文件 PASS |
| diff-check | tracked 与 owned-untracked 文件均检查；新增文件的 no-index 正常差异返回 1 不视为校验失败 |
| F8 ownership | 13/13 SHA256 不变，包括根 README/task_plan/progress/findings |

全量命令（`apps/api`）：

```bash
APP_ENV=test DATABASE_URL=sqlite:////tmp/aco-stage3-HRe8tT/final-suite.db AI_STUDIO_MEDIA_ROOT=/tmp/aco-stage3-HRe8tT/final-media .venv/bin/python -m pytest -q
```

没有新增永久测试文件或测试用例。最终记录使用本轮新鲜 stdout，不以旧 build 或 progress 记录代替运行结果。

## 未完成与未执行

- 11.5 重复接受编辑的偏好候选仍未实施；不会用 execution 接受冒充编辑证据。
- 真实 Codex/Claude 客户端、专业恢复、Director-first Video、Variant 日常编辑、成果绑定 Master、显式 cleanup、Legacy parity 退场、备份恢复和全 change 验收仍后续推进。
- 旧菜单/URL 保留，canonical sync/archive 未执行。本地 commit、push、deploy、正式 migration、凭据配置、正式 API/Web/Worker 重启均未执行；没有模型/公众号真实调用。
- 仅停止本批隔离 API/Web，保留隔离证据。正式数据库和正式素材不被测试写入。

本轮实际使用 using-superpowers、openspec-apply-change、writing-plans、executing-plans、brainstorming（复用批准设计）、subagent-driven-development、dispatching-parallel-agents、test-driven-development、systematic-debugging、receiving-code-review、requesting-code-review、verification-before-completion。测试限制优先，红绿验证仅用临时断言和既有 suite。
