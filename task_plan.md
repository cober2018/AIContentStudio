# Codex with ChatGPT 连接配置计划

## 2026-09-27：FE-F3A apply

目标：按已确认的 `fe-f3a-content-project-core-completion` 实现五类项目核心持久化、真实七标签与回归验收；不做生产迁移、推送或合并。详细步骤见 `docs/superpowers/plans/2026-09-27-fe-f3a-project-core.md`。

- [x] /// 五表迁移、模型、ProjectEvent 和项目归档权限边界
- [x] /// Brief、Source/Fact Boundary、共享素材和 Versions/Overview API
- [x] /// 七标签前端接真实 API，保留 FE-F2 Matrix/Production
- [x] /// 隔离库迁移、后端/前端回归、OpenSpec strict 与文档同步（296 后端测试通过）
- [x] /// 外部复核通过并归档；仅提交本地 FE-F3A 分支，不推送/合并/部署

## 2026-09-27：FE-F3A 规格复核与标准目录归位（不 apply）

目标：核对用户提供的 FE-F3A 包与 FE-F2 基线，纳入标准 OpenSpec 变更目录，修补实施前必须明确的边界；不修改业务代码、运行迁移或发布。

- [x] /// 核对 FE-F3A 来源包、FE-F2 基线、现有项目/Source/FactPack/Material 实体及路由
- [x] /// 从 `734990c` 创建 `codex/fe-f3a-project-core-completion`，将结构化提案归位到标准 `openspec/changes/`，保留原始包
- [x] /// 修补项目删除历史安全、事件事务、并发修订、重新绑定与素材字节回滚边界
- [x] /// 运行 OpenSpec strict 与 diff 检查，核对本轮仅文档变更，更新 README/progress/findings
- [x] 用户已确认进入 `/opsx:apply`；本轮按已校准规格实施

## 2026-09-27：FE-F2-R1 收尾补丁（待外部复核）

目标：按已核对的 review 缺口，恢复固定版本所见即所执行、矩阵安全 CRUD、可解析模板占位符与真实 Attempt 审计；不扩大到新插件或生产迁移。

- [x] /// 确认仅项目覆盖、无 Run/快照/产物的单元可原地修改；补 FE-F2 OpenSpec 场景
- [x] /// 先写固定版本、矩阵生命周期与模板 Gate 的定向回归，观察旧行为失败
- [x] /// 加 effective-workflow、原地修改/历史替换/归档和显式重绑，前端加载固定版本
- [x] /// 收紧占位符到 config，持久化节点 Kind，清理失败重跑的当前输出
- [x] /// 全量后端测试、前端构建、OpenSpec strict 与 diff 检查
- [x] /// 外部 R1 小补丁复核通过；完成 OpenSpec 6.3，归档后仅提交 FE-F2 分支，不推送或合并

## 2026-09-27：FE-F2 apply（codex 分支）

目标：按已确认的 `fe-f2-persistent-production-workflow` 实施真实持久化、权限、版本、Data Node、项目产物和生产工作台；不触碰生产迁移或发布。实施细目见 `docs/superpowers/plans/2026-09-27-fe-f2-persistent-production-workflow.md`。

- [x] /// 从当前干净 main 建立 `codex/fe-f2-persistent-production-workflow` 分支，核对 OpenSpec 0/21 与基线测试
- [x] /// 持久化项目/单元/角色/默认绑定及迁移，补定向回归测试（OpenSpec 1.1）
- [x] /// 统一项目权限覆盖新旧 Workflow API
- [x] /// 工作流校验、项目覆盖与角色默认版本双保存
- [x] /// Data Source Plugin、快照、stale 与项目产物
- [x] /// 三形态生产工作台与设计/调试器
- [ ] /// 完整回归、本地验收、文档及归档

## 2026-09-27：FE-F2 正式 review 的实施前边界（仅规范）

目标：封闭旧 Workflow API 旁路、角色默认模板的项目值泄漏与拖拽误改依赖，并把回归测试列为 FE-F2 实施任务；本轮不 apply。

- [x] 核对现有 Workflow 旧接口及 FE-F2 草案中的四项缺口
- [x] /// 将统一项目授权覆盖旧 run、attempt、retry、rerun、human、cancel、list 及定义入口
- [x] /// 将服务端模板可移植性 Gate 和视觉顺序/依赖图分离写入设计、规格与任务
- [x] /// 将定向回归测试纳入 FE-F2 任务与验收
- [x] 严格校验新版 OpenSpec 并核对差异；保持 apply 未执行

## 2026-09-27：FE-F2 V5 规格校准（仅规范）

目标：把现有 FE-F2 OpenSpec 与 V5 对齐；用户已确认角色 × 内容形态默认工作流新版本须真实持久化并供后续内容单元选择。本轮不执行 apply。

- [x] 对照 V5 契约与 FE-F2 proposal/design/specs/tasks，确认插件与角色默认模板边界
- [x] /// 订正 Data Source Plugin 注册/选择、断连失败闭合、Data Snapshot 与 stale 规格
- [x] /// 订正项目覆盖与角色默认版本双保存路径，以及六类节点、拖拽和项目共享产物规格
- [x] 严格校验 OpenSpec、差异检查；校准后的完整 FE-F2 提案待用户确认

## 2026-09-27：FE-F0-F1 复核补丁与本地 main 提交

- [x] 核对主规格的异常状态解释缺口与脏工作树边界
- [x] 在异常项目总览/内容矩阵增加状态说明，不改后端
- [x] 前端构建与浏览器页面核对
- [x] 仅暂存 FE-F0-F1 所属文件/差异，审阅暂存快照并提交本地 main（1b8ef04）

## 2026-09-27：连接器故障检查

目标：判断当前项目的 ChatGPT 连接器是否异常；仅在诊断仍指向隧道故障时重启并复核。

- [x] 检查 C2C 更新、授权白名单、固定连接配置和协议配置
- [x] 运行项目连接诊断；诊断自动重新建立安全连接，当前检查全绿
- [x] /// 根据四项独立 `internal error` 复现定位到隧道外部连通异常，执行定向隧道重启
- [x] /// 复核 HTTP/2、健康连接数及公开 MCP 未授权响应
- [ ] /// 请用户重试 `workspace_info`，确认 ChatGPT 连接器调用恢复

复查（2026-09-27）：用户报告疑似再次断开。诊断仍全绿；外部 MCP 返回 401、HTTP/2 正确、HA 连接数大于 0。未重启，待 ChatGPT 端具体现象确认。

## 2026-09-27：FE-F2 真实执行与持久化提案

目标：用户明确 FE-F2 工作流调试器须接后端、真实执行并保存流程；先完成 OpenSpec 设计确认，再进入实施。

- [x] 核对 FE-F2 产品契约、现有前后端工作流与未提交改动
- [x] 提出复用既有引擎的项目级持久化方案，建立完整 OpenSpec 并严格校验
- [ ] 等待用户明确确认校准后的 `fe-f2-persistent-production-workflow` 完整范围（角色默认版本单项已确认）
- [ ] /// 确认后编写实施计划并执行 `/opsx:apply`
- [ ] /// 本地真实运行验收、文档同步与归档

## 2026-09-27：FE-F0-F1 前端实施

目标：按已批准的 V5 产品体验和 Frontend Product Contract V1，建立九个一级工作区、ContentProject 七标签、内容矩阵 CRUD、共享素材与生产入口。新项目数据仅在本地模拟，不改后端。

- [x] 核对交接材料、现有前端和未提交改动
- [x] 建立并严格校验 `implement-fe-f0-f1-product-shell` OpenSpec
- [x] /// 模拟项目数据与状态组件
- [x] /// 主导航、项目列表与七标签
- [x] /// 内容矩阵、共享素材与生产入口
- [x] /// 构建核验、文档与归档

- [x] 确认当前项目与连接方式
- [x] 为 `AIContentStudio` 配置固定连接
- [x] 在 ChatGPT 创建并完成当前项目连接器授权
- [x] 创建并绑定 ChatGPT 专属项目（账号切换后重新绑定）
- [x] 通过 `workspace_info` 验证当前工作区

## 2026-09-22：与产品蓝图对齐（仅规划）

目标：在现有系统上形成文章/图文 V1 的实施顺序与验收标准，不实施业务代码、不发布内容。

- [x] 找到并阅读指定对话「自媒体平台对比总结」，以用户最后明确的需求为准
- [x] 核对当前代码能力与蓝图差距，区分实现、文档声明与未验收项
- [x] 在原 ChatGPT 对话开展三轮讨论：范围对齐、最小改造、实施和验收收敛
- [x] 保存三轮规划建议与证据，更新进度、发现和 README（不是实施授权）
- [x] 独立复核本地草案，修正候选采纳顺序与单目标可靠性前置；不进入实现
- [x] 原对话恢复后完成三轮讨论，收敛首个待确认的提案范围与建议名称
- [x] 根据 ChatGPT 最终复核创建 `add-evidence-bound-article-handoff` OpenSpec，并通过严格校验
- [x] 读取原 ChatGPT 最终复核后归档；M1 实现和全部本地验收已完成

当前状态：首批 M1 已实现并完成本地验收：已有文章的公众号 + X 线程 ZIP 成品包、人工交付回执与反馈；公众号自动进入草稿箱不作为首批硬门槛。原 ChatGPT 最终代码复核已返回 DONE，OpenSpec 已归档。真实发布、排期与任何远端 API 副作用均不在本次范围。

## 2026-09-24：继续按 PRD 补齐 V1 全渠道

目标：以 `03_ai_content_studio_PRD.md` 为长期需求基线，补入原对话明确的 11 平台 V1 文章/图文范围，保留抖音脚本；分阶段推进受控成品与逐形态验收。

- [x] 核对 PRD 首选三渠道、原对话 11 平台目标及现有生成/受控交付差距
- [x] 建立 `complete-prd-v1-channel-deliverables` 的 OpenSpec 提案、设计、规格和任务
- [x] 完成严格提案校验（4/4 产物齐全）
- [ ] 等待用户确认此具体变更
- [ ] 用户确认后执行 `/opsx:apply`，按 `/// 迁移与契约 /// 渠道成品 /// 交付界面 /// 验证归档` 推进

当前状态：用户纠正后正在修订提案；尚未修改业务代码。PRD §15 的 15 项标准、§16 的 30 个真实 Topic 门槛及 §3.1 的全渠道逐形态验收分别跟踪。
