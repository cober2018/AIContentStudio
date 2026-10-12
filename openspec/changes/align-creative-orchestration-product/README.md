# align-creative-orchestration-product

## 需求背景

以已批准的 `docs/AI_CONTENT_STUDIO_NORTH_STAR.md` 为产品方向，统一日常创作入口；复杂创作由可替换执行者完成，再回到项目、素材版本、审阅和交付链。旧功能必须先完成操作级承接，不能靠隐藏菜单实现迁移。

本机 SQLite＋本地素材库＋loopback API/Web 是正式使用环境，不因本轮设计新增服务器化部署要求。

## 当前状态（2026-10-05）

**原147项核心实施APPROVE，R1/R2实施和门禁已完成，当前153/154；只剩15.7最终closeout复核。** approved head/readiness与F8恢复契约已对齐aco/null-inert身份，新增四组108个持久回归；完整后端1768 passed/28 skipped、Web/FE-P1、strict35/35、app＋新测试Ruff及空白检查通过。归档、canonical同步和提交暂缓；日常九入口、十五个兼容入口和历史URL继续保留，新版继续运行。

本地 `main@341ead8` 仍有未提交实现；用户另行授权后，本机正式 SQLite 已升级到 `aco000000001`，原API/Worker及新版Web已启动，MCP联通已验证。当前可以从 `http://127.0.0.1:5173/` 使用新版。历史数据/素材hash保持一致；未提交、归档、push或公开发布。正式启用记录见 `docs/ALIGN_CREATIVE_LOCAL_ENABLEMENT.md`；下文阶段记录中的“不动正式库”均为当时历史。

## 目录

- `proposal.md`、`design.md`：已独立批准的范围与领域边界。
- `specs/`：12 份 capability delta；canonical 同步仍待另行授权。
- `tasks.md`：原147项实施验收＋7项post-enable收尾。
- `../../../apps/api/tests/test_aco_*.py`：四文件108项永久回归；执行域/MCP/方法库/迁移与默认schema，不使用正式数据库或供应商。
- `task_plan.md`、`progress.md`、`findings.md`：本 change 独立执行记录，避免覆盖 F8 拥有的根目录记录。
- `../../../docs/LEGACY_OPERATION_PARITY.md`：旧路由、操作真源和新入口盘点。
- `../../../docs/ALIGN_CREATIVE_PHASE_0_2_ACCEPTANCE.md`：第一批验证证据与限制。
- `../../../docs/ALIGN_CREATIVE_PHASE_3_7_BACKEND_ACCEPTANCE.md`：第二批后端验证、隔离迁移及复核证据。
- `../../../docs/ALIGN_CREATIVE_UI_MCP_ACCEPTANCE.md`：第三批页面、受限 MCP、Test Agent 与成果人工接受证据。
- `../../../docs/ALIGN_CREATIVE_CAPABILITY_MEMORY_ACCEPTANCE.md`：第四批方法库、Learning 桥接、MCP 复用与冲突恢复验收。
- `../../../docs/ALIGN_CREATIVE_DIRECTOR_VARIANTS_ACCEPTANCE.md`：第五批导演入口、五种 Variant 正文、素材绑定/暂存清理和冻结血缘验收。
- `../../../docs/ALIGN_CREATIVE_RECOVERY_PREFERENCES_ACCEPTANCE.md`：第六批真实 Codex MCP、受控执行恢复、人工编辑偏好候选、配套恢复及安全验收。
- `../../../docs/ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md`：整个change的可转交执行回执、最终状态、三类独立复核、导航收敛、门禁及各轮修正的完整记录；沿用文件名保留已有引用。
- `../../../docs/CREATIVE_EXECUTION_MCP.md`：本机 MCP 接入边界、配置方式与尚未验证范围。
- `../../../docs/ALIGN_CREATIVE_LOCAL_ENABLEMENT.md`：当前正式启动、停写、配套备份、MCP与历史保全验收。

## 已完成（阶段记录；旧进度是历史快照）

第一批阶段 0–2 的入口实现已完成：根地址进入 Home；Production 显示既有项目/单元和原生生成任务；Project 新增渠道变体/执行入口；Assets/Project 承接 Source、Fact、FactPack、Material 操作；Settings 按需打开既有 Connector/模板工具。

已完成隔离浏览器 15 组检查，使用真实本地 API 和临时 SQLite/素材目录。生成使用受控测试 Provider，签名任务使用隔离夹具，不等同真实供应商/prepare/dispatch 验收。旧 URL 和 `LEGACY_NAV` 仍保留。

第二批阶段 3–7 后端已实现 Creative Intent、不可变 Execution/Director Package、执行状态与私有工作目录、逐输出暂存/替换/人工接受。结果进入精确 MaterialRevision，可明确附加项目引用，不自动改正文或发布。

新增 `aco000000001` 迁移只在当前库副本演练，历史原始列哈希保持一致。真实隔离 API 已验证 Text/Variant/Director 包、多输出、unknown 核对、派生权利、并发冲突及新进程回读；最终后端 1660 passed / 28 skipped、构建/FE-P1、strict 35/35、Ruff 和 diff-check 通过。独立 SPEC/Python/数据安全复核全部 APPROVE，详细范围与证据见验收记录。

第三批完成创作意图表单、执行包预览/准备、成果合同/权利审阅、人工接受/拒绝替换、内容优先工作台及独立 Advanced 工作流。受限 MCP 与原服务共用 CAS/审计，Test Agent 已实际完成领取→精确输入→提交→页面人工接受；多必需成果可逐项接受，缺少或拒绝时不假完成。最后后端 1660 passed / 28 skipped，前端/性能和 strict 35/35 通过；复核及详细限制见第三批记录。

第四批完成六类 Capability Memory 的候选/保存/固定/归档、范围/历史 CAS、显式复用、结果回填、安全导入导出、独立 Installed Skills 清单与 Learning 显式桥接。成果捕获失败不撤销接受；所有适用方法并列返回，不执行代码或自动改正文。修正后后端 1660 passed / 28 skipped，页面闭环/冲突恢复、构建/性能和 SPEC/后端安全/TypeScript 复核通过。

第五批完成 Video Director-first 日常入口与原高级时间线/渲染、五种 Variant 正文修订及真实 409 保留本地编辑。实际隔离链路完成无 render 导演包→受控 MP4/WAV/PNG→人工接受→明确绑定保存→v4 审阅批准→本地 ZIP；历史 ZIP 字节保持一致。暂存清理只删除经明确确认的精确副本，正式 Material 字节/输出历史不变。Home 投影真实风险；v4/v5 只冻结已纳入正文的安全外部血缘，跨项目显式引用保留原来源。独立 SPEC/安全/前端复核通过，修正后完整后端、构建和性能通过。

第六批完成真实已安装 Codex 客户端 MCP 连接/资源读取、executor 自声明与受控文件 checkpoint/revert/recover、重复已保存人工编辑的显式偏好 candidate/独立晋升，以及 SQLite/素材配套恢复。秘密扫描缺口经独立复核发现后窄修，325 项临时边界检查及完整后端 1660 passed / 28 skipped 通过，前端/性能与独立复核通过；正式库/F8/Worker 不动，不以受控恢复声明专业工具已验证。

第七批完成日常新项目 Source→Fact→Pack→Text Master→Candidate v4→审批→本地 ZIP；旧 Topic/Draft/Mother/Candidate/Target/Receipt 原路由只读、全表哈希不变。补逐条证据公开授权、周期明确保存、撤权取消零请求、模板角色/草稿归档及 Settings 兼容目录。新鲜完整后端、构建/性能、strict/Ruff/diff 通过。最终独立复核因额度限制未完成，不记 APPROVE，旧导航仍保留。

## 待完成

- 原核心实施与R1/R2修正已经完成；只待15.7同工作区最终closeout复核。canonical同步/归档、本地提交未执行，不影响当前本机使用。
- 专业工具真实自动化 pilot 不在本 change 第一版范围；受控 executor、媒体夹具、文件恢复和本地 ZIP 不冒充生成质量或公开发布。
- 本轮已明确授权根README/F8 schema/恢复/当前状态8份文件的窄校准；旧验收与其他F8-owned片段保留，根进度文件和真实运行配置不动。

## 关键设计决策

新入口复用原 API/版本真源，不新增统一 Asset/Task 表。普通读取不生成、不发布、不接受结果；`unknown` 不自动重发。全局/旧临时预览接受只入 MaterialRevision；绑定项目的既有持久任务接受会同时建立该项目的精确素材引用，页面明确说明并回读。两者都不自动修改 Master，保存 Master 始终是独立明确动作。

此前实施批次不触碰F8已有13个dirty文件；本轮仅按R1明确授权校准其中8份schema/当前运维文档，其他文件和历史验收保留。新增执行域持久化符合已批准范围；服务与页面已验收并另行完成正式schema/MCP启用，未删除任何兼容页面或历史深链接。f8a身份字段存在不等于JWT启用。

## 依赖与运行

无新增依赖，沿用原本本机 API / Web / 必要 Worker 启动方式。正式启动说明仍由根 README 和现有 runbook 提供，本文件不建立第二套部署配置。

前端验证：在 `apps/web` 执行 `npm run build`（包含 TypeScript、Vite、bundle gate）。规格验证：仓库根执行 `openspec validate --all --strict`。隔离后端验证命令与临时库路径记录在验收文档；不要把正式数据库作为测试库。
