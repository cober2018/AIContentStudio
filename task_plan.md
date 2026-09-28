# Codex with ChatGPT 连接配置计划

## 2026-09-28：FE-F5A 六份主规格同步与归档（已授权）

- [x] /// 核对 main `682df71`、4/4 产物、17/17 任务和六份 delta
- [x] /// 同步新增两份与更新四份主规格，归档 FE-F5A 并补正式 Purpose
- [x] /// 逐块核对 delta 与历史要求保留，运行全量 strict、diff-check，更新记录并准备本地提交
- 不推送、部署或运行生产迁移；不开始 FE-F5B 业务实现。

## 2026-09-28：FE-F5A 本地 main 整合（已授权）

- [x] /// 核对 main 与隔离分支同源，保留主工作区未跟踪的原始规格包
- [x] /// 重新执行后端、前端、OpenSpec 和差异门禁，仅提交 FE-F5A 文件
- [x] /// 快进合入本地 main，在合并结果上复跑门禁并记录提交
- [x] /// 六份 delta 同步与归档已获单独授权并完成；不 push、deploy 或生产迁移

## 2026-09-28：FE-F5A apply（实施/复核通过，已同步归档）

- [x] /// 核实 main `2f52053` 含 FE-F4/FE-P1，隔离分支 `codex/fe-f5a-home-opportunity`
- [x] /// 四资源持久化、状态闸门、评估版本、信号权限、原子显式转换
- [x] /// Home / Opportunity 真实页面及 lazy 预算，项目来源回链
- [x] /// 临时库 upgrade → downgrade → upgrade，真实浏览器机会 → 评估 → 项目 → 刷新
- [x] /// 关闭独立复核问题，完成全项目待决策批量投影，再跑最终门禁
- [x] /// 完成规格同步归档；本地 main 整合已单独授权，不 push、deploy 或生产迁移

## 2026-09-28：FE-F5A-SPEC-R1 review 修订（SPEC_R1_READY）

- [x] /// 核对 review 反馈与当前 OpenSpec、AuditLog/ProjectEvent 模型和既有 Home/Review 投影
- [x] /// 补状态生命周期闸门、Assessment 并发、来源真源、Home 排序/失败语义和四个 Modified Capabilities
- [x] /// 将定向自动化回归要求写入 tasks，保留不新增独立测试框架的边界
- [x] /// 运行全量 OpenSpec strict 与 `git diff --check`
- [ ] /// 等待 SPEC_R1 确认后执行 `/opsx:apply`，不提前改业务代码

## 2026-09-28：FE-F5A Home + Opportunity 规格审计与归位（SPEC_READY）

目标：在 FE-P1 `85b8c08` 基线上，为内容生命周期补上 Opportunity 决策层和 Home 聚合工作台；本轮仅完成 OpenSpec 规格，不 apply 业务代码。

- [x] /// 核对 FE-P1 本地 commit、主规格、现有 Home/Opportunity placeholder、Project Overview/Review/Delivery 事实来源
- [x] /// 创建 `fe-f5a-home-opportunity` proposal/design/specs/tasks，写明 Opportunity 与 Topic、Home 与第二状态机的边界
- [x] /// OpenSpec strict 校验、diff 检查、记录 connector 基线前置
- [x] /// 审计用户解压标准包，补齐四份 FE-F0/F1、F3A、F3B、F4 delta，并统一 Source binding / Fact Boundary 语义
- [ ] /// 等待 connector 可读 FE-F4/FE-P1 最终基线后执行 `/opsx:apply`

## 2026-09-28：FE-P1 主规格同步与归档（已授权）

目标：将五条 ADDED Requirement 归入 canonical `openspec/specs/` 并归档已复核的 FE-P1；不推送、合并或部署。

- [x] /// 核对隔离工作树、4/4 OpenSpec 产物、10/10 任务与主规格未同步状态
- [x] /// 使用 OpenSpec 归档并同步 FE-P1 主规格，核对五条长期要求
- [x] /// 归档后运行 strict、前端构建预算与 diff-check，更新 README/progress/findings

## 2026-09-28：FE-P1 apply（已授权）

目标：按已确认 OpenSpec 限定前端加载边界和首包预算；实施计划见 `docs/superpowers/plans/2026-09-28-fe-p1-frontend-bundle-performance.md`。

- [x] /// 复跑 FE-F4 基线与直接访问，确认隔离工作树
- [x] /// 拆分项目列表、详情、生产与共享类型
- [x] /// 路由级 lazy、加载/错误恢复，不改原有路径和业务动作
- [x] /// 生成 manifest，检查 `/projects` 初始 JS 静态闭包与重型依赖
- [x] /// 构建、预算、OpenSpec、浏览器冒烟、文档回填与独立复核；归档需同步主规格后执行

## 2026-09-28：FE-P1 前端首包性能规格审计（不 apply）

目标：以 FE-F4 `2f3ced2` 为基线，核实加载依赖并提出独立 OpenSpec；用户确认前不修改前端实现。

- [x] /// 核对 FE-F4 工作树、入口路由、项目/生产模块和真实构建产物
- [x] /// 写出 FE-P1 proposal、design、spec 与 tasks，限定首轮范围
- [x] /// 运行 OpenSpec strict、差异检查，记录基线和待确认边界
- [ ] /// 等待用户明确确认；本轮不 apply、不归档、不推送

## 2026-09-28：FE-F4 apply（已授权）

目标：按 `openspec/changes/fe-f4-project-review-distribution/` 实施项目优先审核与分发，保持旧 Topic 链兼容；详细步骤见 `docs/superpowers/plans/2026-09-28-fe-f4-project-review-distribution.md`。

- [x] /// 确认 FE-F3B 本地 `main` 基线、OpenSpec 57 项任务（3 项已完成）和隔离分支 `codex/fe-f4-project-review-distribution`
- [x] /// 模型与可逆迁移：ContentAsset / Review / DeliveryTarget
- [x] /// Candidate v3 冻结、精确审批与不可变血缘
- [x] /// 交付授权、v3 人工包、legacy raw-ID 权限、unknown 对账
- [x] /// 项目 Review 投影、Overview/Versions/Activity 与 `/review` 前端
- [x] /// 回归、隔离迁移、浏览器验收、独立复核与五份主规格同步归档
- [x] /// 归档后五份主规格及全部主规格严格校验、差异检查；准备本地提交，不推送/合并/部署

## 2026-09-28：FE-F4 Project-first Review & Distribution 规格审计（不 apply）

目标：以本地 FE-F3B 提交 `55eba02` 为基线，审计用户提供的 FE-F4 包，将校准后的提案放入标准 OpenSpec；主工作区本地 `main` 后续已快进到该提交，但 FE-F4 仍需单独确认才能 apply、推送、合并或部署。

- [x] /// 核对主工作区与 FE-F3B 隔离工作树、canonical specs、模型和迁移前置
- [x] /// 审计来源 proposal/design/specs/tasks 对现有 Candidate/Review/Delivery 结构与权限的适配
- [x] /// 创建标准 `openspec/changes/fe-f4-project-review-distribution/` 并补全五份 delta 的归档安全边界
- [x] /// OpenSpec strict、`git diff --check`、文档与独立规格复核；保持业务代码未改动
- [x] /// 复核主工作区 FE-F3B 主规格、身份实现、迁移 head 与隔离库测试/前端构建基线

## 2026-09-27：FE-F3B Content Identity apply

目标：在隔离工作树审计并实施 `fe-f3b-content-identity`，交付身份层级、不可变快照、工作流偏好和真实工作区；不做生产迁移、推送或合并。详细步骤见 `docs/superpowers/plans/2026-09-27-fe-f3b-content-identity.md`。

- [x] /// 将来源提案归入标准 OpenSpec，校准四份 delta 规格和历史安全边界
- [x] /// 核对 296 项后端和前端构建基线，隔离初始化 worker 数据库
- [x] /// 模型/迁移、版本化身份解析与授权 API
- [x] /// Unit/Run 快照固定、层级默认工作流与项目读模型
- [x] /// 身份工作区、矩阵/生产 UI 与隔离浏览器验收
- [x] /// 全量门禁、独立复核、OpenSpec 归档；不推送/合并/部署

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
