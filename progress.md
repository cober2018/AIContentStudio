# 当前进度

## 2026-09-27：FE-F3B 审计与 apply 起点

- 用户明确授权四份 delta 全部同步。`openspec archive fe-f3b-content-identity --yes` 已更新 FE-F0/F1、FE-F2、FE-F3A 主规格并新增 FE-F3B 主规格；工具实际归档目录是 `openspec/changes/archive/2026-09-27-fe-f3b-content-identity/`。四份主规格的 Purpose 已校正；归档后主规格 strict、diff-check 和本地提交待完成。未推送、合并、部署或执行生产迁移。
- 归档后核验：四份主规格均包含各自 FE-F3B delta，`IdentitySnapshot`、Series > Account > Persona、`identity_unready` 和 Brief identity scope 均可检索；全体 14 份主规格 strict 校验 14 passed / 0 failed，`git diff --check` 通过，受影响主规格无 `Purpose: TBD`。提交前重新完整运行后端 310 passed / 5 既有 warnings、前端构建通过；现有主 JS bundle 1,079.36 kB 提醒未在本切片处理。
- 2026-09-28 独立复核修补：任何 Unit 身份/形态/工作流重绑均生成新快照；同层级纯身份刷新保留兼容的项目覆盖（含有 Run 后 fork 的新 Unit），旧 Run 仍固定旧快照。长期观点改为保留结构的 JSON 编辑；修订 409 后锁定旧草稿并要求显式加载最新版本；历史 Run 仅以冻结 ID/快照表示历史身份，当前名称明确标注为当前值。FE-F3B 定向回归 14 passed；全量门禁与二次复核待运行。
- 2026-09-28 修补后门禁：清除本机异常 `NO_PROXY/no_proxy`，用独立临时 SQLite 初始化 worker 数据库后，全量后端 310 passed / 5 既有 warnings；前端 `npm run build`、OpenSpec strict、`git diff --check` 通过。未改环境持久配置、未碰生产库；等待独立二次复核。
- 2026-09-28 独立二次复核 `REVIEW_PASSED`：五项收尾问题均闭合；复核者另跑 FE-F3B 14 项、FE-F2/F3A 27 项及 TypeScript/diff-check。OpenSpec 11.8 已完成，归档前等待四份 delta spec 同步选择；不将本地回归视为生产验收。

- 用户确认 FE-F3B 整包进入 apply。工作树 `/Users/mshengran/.codex/worktrees/fe-f3b-content-identity/AIContentStudio` 从 FE-F3A 提交 `1fa4520` 建立，分支 `codex/fe-f3b-content-identity`；来源目录仍留在主工作区，未修改。
- 已将来源 proposal/design/specs/tasks 纳入标准 `openspec/changes/fe-f3b-content-identity/`；新能力规格改为 ADDED delta，三份旧能力规格补全 MODIFIED 原要求，OpenSpec strict 通过。
- 审计补强：现有 BrandVoiceVersion 是无 owner 字段的全局版本资源；brandless 历史 Persona 不补造 Brand/修订；归档祖先不得参与新生产；重绑父级时不得悄然丢弃不兼容子级；旧裸 Workflow API 仍须保护 Account/Series 默认定义。
- 基线第一次后端全套 295/296：唯一失败是新工作树默认 worker SQLite 文件缺表，`test_task_queue` 的 Celery task 不使用测试内存库。使用独立临时 SQLite 并初始化后，296 passed、5 warnings；前端 build 通过，现有主包 1,060.65 kB 提醒。未改代码、未触及生产库。
- 模型已加 Brand/Persona/Account/Series 的稳定实体与修订、IdentitySnapshot、两类新默认绑定，并为 Persona/Unit/Run 添可空引用。定向模型结构测试先按缺表/缺列失败、实现后 2 passed。隔离空库迁移初次因新增外键无名称而失败；显式命名后 `f3a→f3b→f3a→f3b` 通过。带历史样本的迁移回读仍待做。
- 内容身份服务和新路由已接入：四级层级所有权、Pydantic override 字段校验、追加修订与 409、缺失/显式 null/整体替换解析、全局 published BrandVoice 检查、快照构造与所有者读取。第一批 API 定向测试先 404 后 3 passed；Unit/Run 接线和跨所有者/归档回归仍待完成。
- 新 Unit 已持久化 IdentitySnapshot，Run 启动时复制精确 snapshot ID，并在归档身份祖先时拒绝新运行，历史 Run 仍可读取。相关测试先因序列化缺字段失败、修正后通过；现有工作仅完成此纵切片，重绑/默认/前端仍待实现。
- 显式身份重绑已接入 Unit PATCH：无 Run/Snapshot/Output 历史时原地生成新快照；有历史时创建替代 Unit、归档旧 Unit，旧 Run 固定旧快照。父级变化而未显式处理子级时返回 422；定向 FE-F3B/FE-F2 回归 25 passed。层级默认工作流尚未接入，当前重绑仍仅解析角色默认。
- 账号/栏目默认工作流的 GET/POST、乐观修订冲突、可移植性校验和有效优先级已接入；新 Unit 固定 Series > Account > Persona，旧 Unit 不自动重绑。旧裸 Workflow API 的 owner 检查覆盖账号/栏目 scope；定向 FE-F3B/FE-F2 回归 26 passed。
- FE-F3A 读模型已接入真实快照条目及 legacy 状态，Overview 对活动单元的缺失/空身份给 `identity_unready`；新 Brief 版本里的结构化身份 ID 会校验 owner 与层级，旧字符串标签保留。定向 FE-F3B/FE-F2 回归 27 passed。
- `/identities` 已换为后端持久层级工作区：树、四级修订字段、继承/覆盖/清空、历史、账号/栏目、工作流偏好和诚实的内容记忆空态；前端构建通过。项目版本页也显示真实身份快照及 Legacy 条目。浏览器交互与项目/生产上下文仍待验收。
- 在独立临时 SQLite 上，先由 FE-F3A 原代码建真实旧 schema 并插入 owner/Persona/Project/Unit/Workflow/Run，再由 FE-F3B 执行 upgrade→downgrade→upgrade；旧 Run checksum 原样、Unit/Run 快照仍 NULL、IdentitySnapshot 0 行，`foreign_key_check` 空。迁移有既存 workflow parent FK 的 SQLAlchemy 警告，非失败；未碰项目数据库或生产库。
- 项目矩阵账号/栏目选择、有效默认预览、显式身份刷新和生产页四级 Context Header/只读快照已接入；最新前端 build 通过，现有主 bundle >500 kB 提醒仍在。浏览器端到端验收尚未做。
- 全量后端首次 303 passed / 1 failed：旧 FE-F3A Overview 测试假设唯一风险为 `unit_blocked`，与 FE-F3B 新 `identity_unready` 合同冲突。按新合同加入确定性的身份下一步并更新该断言后，全量 304 passed / 5 既有 warnings。该调整仅涉及风险读模型与既有回归预期，不抹掉真实风险。
- 追加 FE-F3B 定向回归：身份归档后 project-scoped 与 legacy Run rerun、项目覆盖保存均拒绝；发布 BrandVoice 可入快照、草稿版本不可引用；身份新修订不改旧快照，显式重绑生成新 checksum。FE-F3B 定向 9 passed，最新前端改动后 build 通过；后续需重跑全量。
- 最新本地门禁：后端全量 305 passed / 5 warnings；前端 TypeScript/Vite build 通过（主包 1,078.53 kB 提醒）；OpenSpec strict、`git diff --check`、涉及后端文件 Ruff F 检查通过。独立代码审阅已发起，尚未归档/提交。
- 补充 Snapshot `readiness`/原因元数据，以及 Unit 创建、原地重绑、替换事件的结构化旧/新 snapshot ID。定向测试最初误把 Activity 分页对象当数组，按既有 `items` 契约修正测试后 9 passed；全量门禁需在审阅修订后再次运行。
- 扩充 FE-F3B 定向测试至 12 passed：跨层级/跨所有者、归档祖先、唯一键竞态回滚、数组/对象整体替换、BrandVoice 覆盖和账号默认模板可移植性。隔离浏览器与 API 共同验收：四级身份创建/刷新、栏目默认 v1 保存后旧 Unit 未自动改绑、新 Unit 固定 v1、品牌修订 v2 后旧快照仍 v1、无历史原地刷新到新快照、真实 Human Run 固定快照、再刷新创建替代 Unit 并归档旧 Unit。临时库读回旧 Run checksum 不变。
- 最新完整门禁：后端 308 passed / 5 warnings，前端 build 通过（主包 1,078.53 kB 警告），OpenSpec strict、diff-check、Ruff F 通过。独立审阅结论仍待回，未归档/提交。

## 2026-09-27：FE-F3A apply 起点

- 用户已明确授权进入 apply；使用标准变更 `fe-f3a-content-project-core-completion`，spec-driven 产物 4/4，任务 2/54 完成。
- 当前分支 `codex/fe-f3a-project-core-completion` 基于 FE-F2 `734990c`，存在上一轮尚未提交的规格/README/记录改动和用户原始 FE-F3A 包；这些均保留，不新建丢失规格的工作树。
- 实施顺序记录于 `docs/superpowers/plans/2026-09-27-fe-f3a-project-core.md`。尚未运行生产迁移，也不推送/合并。
- 1.1/1.2：五个模型和增量迁移文件已加入；FE-F3A 表结构测试先因缺表失败，新增模型后单测通过。下一步在隔离库验证迁移 up/down/up，并实施事件/归档语义。
- 1.3 部分：隔离临时 SQLite 已完成 `e5fef2000001 → f3a000000001 → e5fef2000001 → f3a000000001`；仓库初始迁移会按当前模型预建新表，因此 FE-F3A 迁移使用既有的表/索引存在性防御。尚未在该迁移链路里插入并回读 FE-F2 历史行。
- 2.x 部分：项目创建/编辑/归档、单元创建/编辑/替换/删除、项目工作流保存、项目来源角色默认保存、快照与关联产物写入 ProjectEvent；当前事件/项目及 FE-F2 Data/Output 定向测试 11 passed。项目归档后新旧 Run 修改权限加了保护，后续仍需更完整回归。`project_events.py` 的稳定常量与 2.5 全路径验证尚未完成。
- 3.1/3.2：Brief 已有当前/历史/详情/追加版本 API；保存按 expected_revision 对比，唯一键并发冲突回滚为 409，事件同事务写入。先验证无路由 404，再实现后定向 4 passed；前端尚未接入，完整字段校验和并发双会话验证待做。
- 4.1/4.2/4.4：项目 Source 引用可附加、幂等重复、解除并重新激活，旧全局 Source 保持可读；Fact Boundary 可读取当前/历史并只绑定有 checksum 的冻结 FactPack，revision 冲突返回 409。相关测试先 404 失败后定向 6 passed。项目级 Clone/Freeze-and-bind、全局 FactPack 服务共用规则、前端 Evidence 仍待实现。
- 4.3/4.5：全局与项目级 FactPack Clone/Freeze 现复用 `factpack_service`，项目级 freeze-and-bind 要求当前边界的直接草稿子版本，冻结、审计和边界修订同一数据库事务。克隆→冻结→新边界→旧历史可读的定向测试先失败后通过；FE-F3A+FE-F2 项目定向 13 passed。前端 Evidence 仍未接入。
- 后续实现已接入 Brief、Evidence、Assets、Overview、Versions、Activity 后端与项目七标签前端；此前后端全套 289 passed、前端 build 通过，最终门禁待重跑。新归档项目回归证明历史 Run 可读、旧裸 Run mutation 与项目 mutation 均拒绝。
- 收尾修正：项目 PATCH 不允许绕过专用归档接口直接设置 archived；生产工作台共享素材按项目上传/系统引用/工作流产物区分，图文与视频“已生成”列表只显示工作流产物。
- 定向补测通过：项目 PATCH 直接归档返回 422；注入上传事务内事件失败时 Material、MaterialRevision、项目引用均回滚，预先存在的同哈希共享字节保持不删。FE-F3A 定向测试 12 passed；此前全套 290 passed，最终变更后需再跑。
- Evidence 返回项目页后可从 FactPack 列表恢复当前边界的最新草稿，避免“编辑后无法冻结并绑定”；Matrix 已提取为独立 Tab 组件并隐藏已归档项目的矩阵写入按钮。前端构建再次通过（主 bundle 1,057.94 kB，原有体积提醒）。
- 隔离迁移库带真实 FE-F2 ContentProject、ContentUnit、WorkflowRun(checksum) 完成 e5→f3a→e5→f3a；三条历史行与 checksum 回读一致。未触及生产库。
- 隔离浏览器验收：创建项目、Brief v1/v2、文本 Source 创建并关联、冻结 FactPack 绑定、项目边界 Clone→跳转编辑→返回恢复草稿→冻结并绑定、PNG 项目上传、同版本再次引用幂等、Overview/Versions/Activity 真读模型、七标签逐一刷新均成功。验收使用独立临时 SQLite 与 127.0.0.1:18081/15174。
- 归档状态的普通 PATCH 旁路已同步堵住：Project 必须走 DELETE→archive，ContentUnit 必须走已有删除/归档语义；避免写成通用 updated 事件或绕过历史保护。
- 新定向用例先发现 Overview 把 `waiting_human` 单元误归为普通生产；已补待人工聚合，并区分最新 Run 的 stale/failed/waiting_input 节点状态。Brief 同内容显式保存会形成新修订、checksum 相同。FE-F3A 定向现为 13 passed。
- Overview 前端将风险/人工状态代码翻成用户可读中文，并显示待处理项对应单元；不在 React 重算阶段。
- 新增跨所有项目核心读模型的归档/跨所有者回归：归档后 Brief、Boundary、Assets、Versions、Activity、Overview 可读，Source 解绑不改已冻结边界；另一用户均 404，归档项目的新写入均 409。FE-F3A 定向现为 14 passed。
- 当前最终本地门禁：后端全套 293 passed / 5 warnings；前端 `npm run build`（含 TypeScript）通过，主 JS 1,058.31 kB 非阻塞提醒；OpenSpec strict、`git diff --check`、本次后端文件 Ruff F 检查通过。独立代码复核已发起，OpenSpec 归档与提交保持等待。
- 定向回归进一步验证 Clone 后编辑草稿再冻结会产生不同 checksum 且旧 FactPack item 数不变；重复 Source/Material 关联不重复写项目事件。新增断言后 FE-F3A 定向 14 passed；全套门禁仍需最终复跑。
- 在 FE-F2 素材真实字节/Attempt 回归上增加 FE-F3A 并集断言：同一 MaterialRevision 同时由 workflow 与 system_reference 合法展示，两个稳定 key，数据库仍只有一条 Revision；定向测试通过。
- 独立审阅首次结论为不准归档/提交，指出 5 个重要缺口。已逐项修：新哈希上传失败单独记录可核对的 `material.upload_orphan_candidate` AuditLog，不删除共享字节；归档 Evidence 隐藏创建/绑定并在全局 Source 创建前再次核对项目状态；项目 PATCH 不能修改 objective；显式素材回传 MaterialRevision 来源信息；Evidence 增加当前冻结 FactPack 条目区，Brief 历史可展开全文。定向单测与前端 build 已针对相关修改通过，最终全套和复审待跑。
- 隔离浏览器归档后复验：Evidence 的 Source 创建/解绑和边界绑定控件均不出现，事实条目和边界历史仍可读；Brief/Assets/Matrix 的项目级写入控件不出现。
- 二次复审又发现 orphan candidate 的 `AuditLog.entity_id` 超过 PostgreSQL 的 50 字符限制、且未被清理消费。现只在该列存 50 字符哈希前缀，完整哈希留在 detail；既有 `run_retention` 以一日宽限、每批上限处理候选，先检验路径与已提交 MaterialRevision/DraftMedia/AssetMedia 引用，再删除无引用字节或保留共享字节。未处理候选不受普通 90 天 AuditLog 清理影响。新增新文件删除/共享文件保留/过期候选保留测试均通过，复审待重跑。
- 最新本地门禁：后端全套 294 passed / 5 warnings，前端 TypeScript/Vite build 通过（主包 1,060.65 kB 非阻塞提醒），OpenSpec strict、`git diff --check`、涉及后端文件 Ruff F 检查通过。独立审阅正在复核最后两个上传清理边界，9.6 尚未完成。
- 第三轮审阅指出清理任务未注册、同哈希上传与清理可能竞态。已注册现有 beat 配置的 `retention_sweep`；MaterialRevision 写入持有哈希分片文件锁到外层事务结束，保留流程在引用检查与 unlink 期间持同锁，并逐候选提交。新增任务注册与跨线程锁释放回归；清除本机异常 `NO_PROXY/no_proxy` 后后端全套 296 passed / 5 warnings，前端 build、OpenSpec strict、diff-check、Ruff F 通过。最终独立复核进行中，仍未归档/提交。
- 独立复核最终 PASS、无剩余 blocker；9.6 已勾选。用户确认同步主规格后，OpenSpec 已归档至 `openspec/changes/archive/2026-09-27-fe-f3a-content-project-core-completion/`，同步两项旧能力规格并新增 FE-F3A 主规格（9 added / 3 modified）；三份主规格 strict 均通过。待核对暂存快照并提交本地分支；不推送、合并或部署。

## 2026-09-27：FE-F3A 规格复核与归位（仅文档）

- 以 `734990c` 为基线创建 `codex/fe-f3a-project-core-completion`，把用户提供的结构化 FE-F3A proposal/design/tasks/三份 spec 归入 `openspec/changes/fe-f3a-content-project-core-completion/`。原始目录、ZIP 与合并文档保持原状，便于追溯。
- 对照 FE-F2 实际项目、单元、Source、FactPack、MaterialRevision 和迁移头复核；旧 Source/FactPack/Material 为全局资源，项目引用不等于获得资源所有权。现有项目 DELETE 可物理删除无单元项目，与新增 append-only 活动/子表冲突，已在规范中改为归档语义。
- 已补强事件同库事务、Brief/Fact Boundary 并发冲突转 409、Source/Material 唯一绑定重新激活、素材字节写入后的失败清理边界。业务代码和数据库未改动；`openspec validate fe-f3a-content-project-core-completion --strict` 通过，纳入新增规格文件后的 `git diff --check` 通过。
- `tasks.md` 仅将分支/规格门禁 0.1–0.2 标记完成；所有实施任务仍待明确 apply 授权，不因 4/4 规格产物齐全而视为功能已完成。

## 2026-09-27：FE-F2-R1 复核通过，归档与本地提交

- 外部复核已明确给出 `REVIEW_PASSED`，范围仅限 R1 五项收尾问题，不把结论外推为完整 PRD/V1 或生产验收。
- 已勾选 OpenSpec 6.3；按用户授权归档 `fe-f2-persistent-production-workflow` 并提交当前 `codex/fe-f2-persistent-production-workflow` 分支。最终命令输出及 commit hash 以本轮实际执行结果为准；不推送、不合并、不部署、不运行生产迁移。
- 归档命令完成：`openspec/changes/archive/2026-09-27-fe-f2-persistent-production-workflow/`；主规格更新 `fe-f0-f1-project-experience` 一项、新建 `fe-f2-persistent-production-workflow` 八项。归档后重新验证：后端全量 279 passed、前端 build 通过、12 份主规格 strict 校验通过、`git diff --check` 通过。归档工具给 FE-F0-F1 主规格增加的末尾空行已修正；待暂存快照核对及本地提交。

## 2026-09-27：FE-F2-R1 review 收尾

- 用户确认：仅保存项目覆盖但尚无 Run、快照、产物的单元，身份/形态/工作流可原地修改；一旦有执行历史，替换为新单元并归档旧单元。
- 已补 OpenSpec 场景并落地：unit-scoped effective-workflow 保持 Designer 与 pinned version 一致；矩阵恢复身份/形态/工作流重绑编辑，历史单元归档且可回读；模板可移植性仅在运行时解析的 config 中参数化；Step 保存 Kind；失败 rerun 不携带旧输出。
- 定向测试先红后绿；全量后端 279 passed，前端 `npm run build` 通过。首次全量出现 1 个新增测试夹具不符合模板 config allow-list，修正夹具后复测通过。OpenSpec strict 与 `git diff --check` 通过；主 JS 包体积警告仍在。归档、提交、推送和生产迁移均未执行，等待 R1 小补丁外部复核。

## 2026-09-27：FE-F2 apply

- 当前分支 `codex/fe-f2-persistent-production-workflow` 从干净的 `main@c044085` 创建；先前脏工作树已由其他提交收敛，本轮不搬运旧改动。
- OpenSpec `fe-f2-persistent-production-workflow` 是 spec-driven，0/21 任务完成；已建立实施计划，先处理持久化与旧 API 权限。
- 基线：`test_workflows.py` 10 passed，前端 `npm run build` 通过（主包体积警告）；Alembic head 为 `d4audit00004`。没有执行生产迁移或发布。
- OpenSpec 1.1：新增项目/单元/内容 Persona、两类工作流绑定、DataSnapshot、项目产物关联与可空 `WorkflowRun.content_unit_id`；定向模型测试先红后绿。隔离临时 SQLite 上从旧版本升级到 `e5fef2000001`、回退到 `d4audit00004`、再升级均成功。未修改已有正式数据库。
- OpenSpec 1.2/1.3：项目、角色、单元 CRUD 与创建者隔离已接 API；旧 Workflow 的 run/attempt/重跑/人工完成/取消/列表和 definition 列表、clone/publish/raw create-run 均接统一项目权限。项目工作流版本增加持久 owner/scope，阻断绑定变更后的遗留旁路。`test_fe_f2_projects.py` 与 `test_workflows.py` 共 14 passed；隔离 SQLite 全量迁移至新 head 成功。下一步补工作流校验和双保存。
- OpenSpec 2.2：项目覆盖另存生成不可变 Workflow 新版本，绑定修订号比较并在失配时返回 409；旧 Run 保留版本/checksum。角色默认另存入口已有初版，但可移植性 allow-list 仍须收严，2.3/2.4 暂不勾选。
- OpenSpec 3.1–3.3：Data Source 六类描述符及断连状态已接服务端；Studio Source 只读快照限制 20k 字、保留 source/version/lineage/checksum。项目 Run 经原引擎记录 Attempt；相同快照不使下游 stale，变化只标记依赖后代；断连插件在启动前被拒绝。快照可按所属单元读取。当前项目/工作流/Data 定向回归与旧工作流回归共 21 passed。
- OpenSpec 2.1/2.3–2.5、4.1：六类节点校验、条件/失败策略及映射参与真实执行；角色默认对同项目/单元 ID 使用上下文占位，对数据 source_ref 用运行参数占位，其他绑定值拒绝。已有 Draft、批准 Candidate 和真实 MaterialRevision 才能被关联项目。定向测试包含生成图实际字节落 MaterialRevision→共享池、历史 checksum、旧 API 旁路和副作用重跑。
- 前端当前接入真实项目 CRUD、角色默认版本选择、单条画布、Inspector、双保存和实际 Run；Mock 单独保留在 `/projects/demo`。隔离 SQLite `e5fef2000001` + 本地 18080/15173 联动浏览器实测：创建项目/身份/单元 → 保存 System 工作流 → Run succeeded/Attempt 输出 → 刷新后仍可读取。没有触碰原 8000 端口上的进程或已有数据库。
- 2026-09-27 续作：隔离 API 旧进程导致 `/outputs` 404，重启后为 200；文字/图文/视频三形态工作台均在浏览器读到持久单元。AI Provider/Model 只允许绑定后端当前执行路由，保存和启动均验证，不暴露密钥；UI 已选中 mock/mocked model 并显示在 Inspector。素材关联增加真实文件与哈希复核，缺失字节不入池。定向后端 30 passed、前端构建通过（包体积警告仍在）。
- FE-F2 最终本地验收：角色默认 v1 另存后，后续单元固定新版本，原单元仍固定项目覆盖；带 snapshot_id 的默认模板保存 422 且绑定不变；Notion 断连启动 409，隔离库对应 Run/Snapshot 均为 0；非所有者走遗留裸 run API 为 404。浏览器验证文字/图文/视频壳层及项目共享素材抽屉。后端 274 passed（需清除本机异常 NO_PROXY/no_proxy）、前端 build 通过、OpenSpec strict 与 diff-check 通过；待规格同步/归档。
- 最终双保存按钮复核：已保存项目覆盖且页面无未保存修改时，“另存为角色默认”现在仍可点击；服务端可移植性 Gate 继续决定能否成功，项目绑定不会被此操作改写。待最新前端构建复核。
- 隔离库保存项目 v2 后发现 Run #1 的冻结定义与当前草稿不同；已修正画布为运行模式显示 Run #1 原节点/成功状态，设计模式显示项目 v2 新节点且不混用旧状态。最新前端 build 通过。
- 全量后端测试 253 passed / 12 failed；12 项均是旧 DSH 代理端口 `:1` 导致的 `httpx.InvalidURL`，与本轮定向链路一致未扩大。前端 `npm run build` 和 OpenSpec strict 通过，主 JS bundle >500 kB 警告仍在。FE-F2 尚有专属三形态界面、Provider/Model/Tool 选择语义及最终本地验收，不可归档。

## 2026-09-27：FE-F2 正式 review 补强（未 apply）

- 已核对旧 Workflow API：除裸 run 详情、attempt、retry、节点重跑和人工完成，运行列表、取消、定义列表/clone/publish 及 raw create-run 也需要纳入同一项目权限边界。
- 已在 FE-F2 proposal/design/spec/tasks 补入统一授权、角色默认模板服务端可移植性 Gate、视觉顺序与依赖图分离、以及现有测试基础上的定向回归覆盖。
- 用户明确要求 FE-F2 新增回归测试，因此旧任务中“不新增测试代码”的限制已在该变更任务条款中替换；本轮只订正规范，尚未新增或运行测试、业务代码和迁移。
- 新版 `openspec validate fe-f2-persistent-production-workflow --strict` 和 `git diff --check` 均通过；未将规范校验误当成功能验收。

## 2026-09-27：FE-F2 V5 规格校准（未 apply）

- 用户确认 FE-F2 须真实持久化“角色 × 内容形态”默认工作流新版本，并供后续 Content Unit 选择；项目覆盖与角色默认保存须分离。
- 已订正 FE-F2 proposal/design/specs/tasks：六类节点、拖拽排序、可扩展 Data Source Plugin 六类来源及断连不可执行、快照 stale、项目共享素材产物关联。
- `openspec validate fe-f2-persistent-production-workflow --strict` 与 `git diff --check` 均通过；本轮未运行应用构建，因没有改业务代码。
- 仅修改规范和记录；没有业务代码、迁移、真实 Connector 或远端动作。校准后的完整提案仍待用户确认后才可 apply。

## 2026-09-27：FE-F0-F1 复核补丁

- 主规格缺口已补：异常项目的总览与内容矩阵显示五种状态说明；生产页原有说明仍保留。
- 本轮 `npm run build` 成功；浏览器已看到异常项目矩阵和总览的状态说明。正在隔离 FE-F0-F1 暂存范围，历史 API/迁移和 FE-F2 提案不纳入本次提交。

## 2026-09-27：FE-F2 提案（未实施）

- 用户明确工作流调试器须后端持久化并真实执行，不能只做前端 mock。
- 已核对现有 Workflow/Run/Step/Attempt 与重跑接口；它们仍以 Topic/渠道组织，FE-F0-F1 项目数据仍在浏览器 `localStorage`。
- 已建立 `fe-f2-persistent-production-workflow` 的 proposal/design/specs/tasks，`openspec validate --strict` 通过；等待用户确认，未运行 apply、未改业务代码或数据库。
- 建议以新增项目/内容单元持久化和项目级不可变工作流版本复用现有引擎；此处原“首个 Data Source Plugin”表述已被上面的 V5 校准覆盖：契约可扩展，首个可执行适配器才是 Studio Source。

## 2026-09-27：FE-F0-F1

- 已确认当前工作区为 AIContentStudio；North Star V2、V5 原型、前端契约和 HANDOFF 均已核对本切片范围。
- OpenSpec `implement-fe-f0-f1-product-shell` 的提案、设计、规格和任务齐全，严格校验通过并已实施、归档。
- 当前工作树已有大量用户改动，本切片只改前端相关文件和本任务文档。
- 已建立类型化本地模拟项目、内容单元和素材版本数据；含健康、异常两类项目，扩展状态徽标且沿用已有弹窗/抽屉。
- 已实现九入口主导航、项目列表、七个 URL 标签、内容单元增删改、本地持久化、共享素材抽屉和生产入口；`npm run build` 已通过，Vite 提示现有主包较大。
- 浏览器实测：项目列表、七标签、内容单元新增/编辑/删除、生产入口、共享素材来源筛选和异常样本的受阻/已过期/待核对区分可见；删除改为站内确认弹窗，验收样本已清理。
- 最新核验：`apps/web` 的 `npm run build` 成功；`openspec validate implement-fe-f0-f1-product-shell --strict` 和 `git diff --check` 成功。前端无单独 lint/test 脚本，本轮未新增测试代码。
- 交付边界：项目数据只在浏览器本地演示，未接后端、未增加迁移、未实现 FE-F2 工作流调试器；旧审核/素材页改用 `/legacy/review`、`/legacy/assets` 别名访问。
- OpenSpec 已归档到 `openspec/changes/archive/2026-09-27-implement-fe-f0-f1-product-shell/`，新增主规格 `openspec/specs/fe-f0-f1-project-experience/spec.md`。

## 2026-09-24：PRD 三渠道补齐提案

- 用户明确 `03_ai_content_studio_PRD.md` 是产品长期目标，并纠正三渠道误读：完整 V1 还包括百家号等 11 个文章/图文/社交平台，另保留抖音脚本。
- 已核对抖音和小红书具备旧生成/导出入口，但缺 M1 受控成品交付；其余长文/问答/社交平台缺原生适配。已把完整范围补入 PRD §3.1，正在修订 OpenSpec `complete-prd-v1-channel-deliverables`；当前仅规划文档，未改业务代码。
- OpenSpec 严格校验通过，4/4 产物齐全；`git diff --check` 通过。下一步是用户确认具体提案，然后按 OpenSpec 流程实施与归档。

- 已配置固定域名连接：`kayoyo.top`
- 已创建连接器：`Codex with ChatGPT · AIContentStudio`
- 已完成 ChatGPT 授权与安全配对
- 已为新 ChatGPT 账号 `Austin` 重新完成同一连接器授权
- 已绑定项目「AIContentStudio」，记忆为「仅限项目记忆」
- 已完成工作区读取验证，返回当前工作区 `AIContentStudio`

## 2026-09-22：V1 蓝图对齐

- 已找到指定原对话及用户最新需求；当前阶段仅做规划。
- 本地连接检查通过，复用原连接与浏览器，不重新配置。
- 正在核对代码并准备三轮讨论；尚未修改业务代码或运行对外发布。
- 源码核对完成，证据已记录到 findings.md；生成/审核/素材/工作流的可复用点及缺口已区分。
- 已形成 `docs/AI_CONTENT_STUDIO_V1_ALIGNMENT_PLAN.md` 讨论草案，等待 ChatGPT 回复及用户分发验收选择；正在做独立文档复核。
- 已补读原对话 R2 完整附件，并将需求编号映射到实施阶段；本轮尚未执行业务能力验收。
- 独立复核指出候选采纳及 Topic 创建顺序遗漏，已修正文档；ChatGPT 第一轮仍在生成，未重复发送。
- README 已增加下一版规划入口、当前未实现项及静态核对边界，原有用户改动保留。
- 文档二次复核要求将单目标交付可靠性前置；已补为自动建稿启用门槛，阶段 C 只做多目标扩展，待最终复核。
- 独立文档最终复核通过；两项问题已闭合。ChatGPT 三轮讨论尚未完成，不能据此宣称共同结论。
- 后续刷新发现首条 INIT 未保存；此前“正在生成”仅为页面提示，不构成有效讨论证据。恢复聊天模式后重新请求工作区/README 读取，页面再次报错，单次重试仍失败。当前连接检查全部通过，未重建连接器，正在核对原会话是否可继续。
- 经已保存会话及项目列表恢复原对话后，仍未取得新答复。已保留原对话和协作检查点，草案明确标为未完成 ChatGPT 讨论；本轮仅修改规划文档及 README，未运行生成/发布、未新增测试、未执行 OpenSpec 实施或提交推送。
- 用户确认可以回复后继续：原对话可见用户新消息“1”；已点击发送简短的当前工作区/README 核验请求，页面显示思考中。尚未取得实际文件读取结果，不将用户可发送消息等同于连接器核验成功。
- 本次核验成功：ChatGPT 返回工作区 AIContentStudio，并引用 README 第 3 行当前三渠道链及第 9–13 行新增 V1 草案说明；原会话恢复文件读取。已将本任务协作地址绑定到指定蓝图对话，开始三轮规划讨论。
- 第一轮规划请求已发送并可见；ChatGPT 已确认只规划，页面出现事实冻结、素材、选题及审批源码核对进展，尚未形成最终方案。
- 第一轮完整 PLAN 已收到并读完，新增源码观察已定点复核；第二轮设计挑战已发送。拟前置双渠道受控复用与最小反馈，尚待第二轮收敛及最终文档审阅。
- 对齐草案已补录第一轮结论与第二轮讨论问题，阶段正文待第二轮完整答复后统一修订；依旧未获得实施授权。
- 第二轮完整 PLAN 已收到并读完；已将首批 M1 与后续 A/B/C/D 分开，补类型化证据、语义检查覆盖、稿件期素材、双层审批、公开包隔离和旧调用入口防绕过。远端建稿独立准入，本轮不启用或停用任何业务功能。准备第三轮及新版独立复核。
- 新版独立复核指出 X Articles 范围及逐形态验收不够明确，已修正为按“平台 × 内容形态”验收，M1 仍仅做 X 线程，不以线程成功替代 X 全覆盖。ChatGPT 第三轮审阅进行中。
- 第三轮完成：ChatGPT 完整读取修订方案和 findings.md，判定规划 DONE，无严重修正；仅提醒历史类型迁移、M1 边界及重复/中断/未知结果验收。已补录这些提醒，明确本地防重不承诺人工或平台端绝对仅执行一次。
- 新版独立复审 Approved；三轮规划已形成建议共识，首批渠道与自动化下限仍待用户确认。没有创建 OpenSpec 提案，没有修改业务代码、生成测试代码、调用模型生成/发布、提交或推送。
- 收尾核对：已跟踪变更的差异检查通过；新增规划文件逐项检查未报告空白格式问题（与空文件比较的退出码 1 表示新增差异）。用户原有 PRD、澄清稿和 docs/superpowers/ 保留，未暂存或提交。本轮验证仅限文档和连接读取，不构成功能验收。
- ChatGPT 最终复核已确认规划层面 DONE：M1 采用类型化证据冻结、母稿版本、公众号 + X 线程成品包、人工交付回执与反馈；不把公众号自动草稿作为首批硬门槛。
- 已创建 OpenSpec 变更 `add-evidence-bound-article-handoff`，完成 proposal/design/specs/tasks 四类产物；严格校验通过，apply 前任务为 0/24。
- 当前执行边界：只实现本地成品包与人工回填，不调用远端发布 API；尚未修改业务代码、运行功能验收或归档 OpenSpec。
- 已开始执行 OpenSpec：完成数据模型扩展、X Thread 最小形态、增量迁移、类型化证据快照写入、母稿导入/适配、候选哈希、人工目标/本地包/回执/反馈接口，以及 M1 旧公众号远程副作用的部分工作流闸门。
- 本地迁移已执行到 `d31415926535`；API 模块语法检查、OpenAPI 路由读取、`git diff --check` 通过。新增人工交付包明确不调用平台 API，也不上传对象存储。
- 现有测试：项目虚拟环境中 129 通过、12 失败；失败集中在既有 DSH 配置值 `:1` 被 httpx 当成非法端口，未经过本次新增链路。系统 Python 的 `make test` 另因缺少 `pypdf` 在收集阶段失败。
- M1 本地实现与验收完成：类型化快照、母稿/适配稿、DraftMedia、完整候选批准、人工目标、ZIP 成品包、回填、反馈和旧工作流远端调用闸门均已落地。公众号实际封面字节被写入 ZIP 并按批准哈希校验；X Thread 路径已单独验证。
- 独立复核提出的四项问题已修复：ZIP 包含实际媒体、终态不因重新取包回退、目标与回执在并发重复请求下回读、目标只能由授权操作人处理；迁移先回填可关联历史 hash，无法关联的历史行保持 legacy/ineligible。
- 公开使用权限可以只撤销不能恢复；素材或冻结证据撤销会使未完成目标进入 `blocked`，已人工确认历史不被改写。
- 验证通过：空 SQLite 迁移到 `g31415926535`、`test_core_pipeline.py` + `test_workflows.py`（23 passed）、前端生产构建、严格 OpenSpec 校验、空白差异检查，以及临时本地数据的公众号实际媒体 ZIP / 账号隔离 / 终态保护 / 权限撤销链路。
- 全量测试仍为 129 passed / 12 failed；12 项均为既有 DSH 状态探测把环境代理地址 `:1` 传给 httpx 的非法端口，未扩大本次范围修复。
- ChatGPT 最终代码复核请求已发送到原对话；浏览器调试连接当前无法附着，因此暂未能读取其回复。OpenSpec archive 因此保持未归档。
- 已补完陈旧候选拒绝与人工结果未知（`reconciliation_needed`）的独立本地验收；同一未知回填重复提交不会新增第二条回执。
- ChatGPT 最终代码复核指出旧工作流默认仍生成公众号草稿节点；已将模板默认改为本地导出，并为遗留远端草稿增加显式开关与服务端闸门，M1 母稿仍不可进入该路径。
- ChatGPT 对上述修复返回 DONE；已完成 `add-evidence-bound-article-handoff` 的 OpenSpec 归档，归档目录为 `openspec/changes/archive/2026-09-22-add-evidence-bound-article-handoff/`。
# 2026-09-27：连接器故障检查

- C2C 更新检查无新版本；授权白名单已配置。
- 固定域名配置正常；`C2C_TUNNEL_PROTOCOL=http2` 已在当前环境及 `~/.zprofile` 配置。
- 用户确认四种独立读取均返回 `internal error`。进一步外部复核发现公开连接返回 530，且该工作区的健康连接数为 0；协议配置正确。
- 已执行 `c2c restart --tunnel`。复核通过：HTTP/2 正确、健康连接数大于 0、公开 MCP 未授权请求返回预期 401。
- 待用户在 ChatGPT 中重试 `workspace_info`，确认连接器端到端恢复。
- 2026-09-27 再次复查：本地诊断无修复项，外部探测仍返回 401，HTTP/2 与健康连接数正常；未重复重启。状态输出含一条 Cloudflare edge 地址警告，但当前传输探测通过。
