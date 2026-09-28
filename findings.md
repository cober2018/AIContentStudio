# 配置记录

## 2026-09-28：FE-F5B 本地main整合边界

- 最终本地整合为dd71a14→9e0ce04快进；主工作区合入后只剩用户原始包/ZIP未跟踪，无业务或暂存差异。可恢复审计备份stash756ed20保留，四份文档已有审计及实施历史，不需要恢复旧版覆盖新进度。

- main和实现分支同在dd71a14，主工作区仅四份本任务文档及标准change/计划重叠，用户原始包与ZIP是无关未跟踪资料。
- 已将主工作区独有SPEC审计/发现/计划段落补入实现分支；重叠工作区改动以限定路径stash可恢复备份，不删除原始资料，不使用reset/强制切换。
- 用户本次只授权代码并入本地main，隐含必要本地commit，不授权主规格同步/归档、推送、部署或生产数据库写入。

## 2026-09-28：FE-F5B apply边界

- 四份MODIFIED delta已逐块对照canonical：Product shell保留九工作区及F3B/F4/F5A入口；Memory旧占位场景明确限于pre-F5；项目事件原有事务约束保留；Home原有七级优先级及稳定去重保留。尚未同步canonical，避免未授权归档。
- 恢复声明幂等凭据存入PublishedContentRecord永久provenance，不依赖90天AuditLog留存；观察新增用owner+active条件写锁，归档竞态拒绝。generic context识别的scalar/list引用严格正整数校验，坏输入422而不是500。
- 服务端冻结promotable_claim和Memory写闸门共用推导；旧可信accepted读时派生且标记derived，不改变原checksum。声明、范围、局限不得借任意accepted候选扩张；不同声明需匹配的新accepted候选。

- 发布回收是同一事务：项目事件未注册会使Receipt/History全部回滚，不能只用legacy无Project夹具替代项目链路验收。已增加project-bound重复回收仅一条事件回归。
- 恢复幂等不是绕过当前约束的通行证：返回历史前仍核对unknown、冻结哈希及Receipt有效性。计算上限代表结果未知，不代表指标不存在。
- 晋升表单只能使用服务端冻结可提升声明；前后端字段契约必须一起验证，否则服务端限制正确也可能使浏览器无法提交。

- 持久化采用七个独立业务资源，共用现有用户、身份、Receipt、Candidate及AuditLog，不新增第二套Home/Delivery状态。
- 现有隔离工作树已包含可复用node_modules；Python运行使用主工作区虚拟环境，但代码和测试从隔离cwd导入。只使用临时数据库，避免访问正式开发/生产数据库。
- SQLite读取DateTime会省略时区，指标窗口口径比较必须统一UTC；旧Receipt delivered_at代表人工回填发生时间，默认保留published_at未知。
- 不可证明Candidate哈希的legacy Receipt不能伪造Studio血缘，应跳过历史回收并在同步结果显式报告；已证明但不一致的哈希拒绝写入。
- 指标超过安全分析界限时不能截断再称最新值，当前返回computed=false和明确缩小范围说明；正常分析的指标Coverage与cutoff/metric/key/unit/有效观察保持一致。
- 当前Memory需防止仅检查accepted状态就支持任意改写；冻结命题、适用范围和限制必须与实际新记忆匹配，锁顺序也需跨promotion/revision一致。独立SPEC复核正在关闭这些缺口。

## 2026-09-28：FE-F5B SPEC review发现

- 标准源包两份新增规格使用主规格格式，四份MODIFIED均为替换片段；已按OpenSpec delta格式归位并保留完整旧块，Identity旧占位场景标为pre-F5历史行为。
- `routers/delivery.py:add_receipt`和`routers/article_handoff.py:add_receipt`都将`delivered_at`写为回填时`utcnow()`；不能视为真实历史发布日期。保留确认真源，仅显式已核实时间进入published_at，否则未知。
- `services/delivery.py:reconcile_attempt`只改Target/Attempt并记录AuditLog/ProjectEvent，不创建Receipt；不能凭human_confirmed Target合成已发布历史或悄改对账语义。
- 同名metric也可能有不同unit/window或重复累计读数；补snapshot/interval粒度、effective correction、cutoff和不可直接求和规则。
- 原包直接POST Memory及revision缺验证门槛，accepted证据未冻结、晋升幂等未说明数据库约束；补服务端共用gate、冻结验证快照、candidate/revision冲突409和promotion唯一来源。
- 图谱MCP工具未提供，本轮仅按已知路径定向读取相关模型、Receipt入口、Identity/Home集成，不全仓代码扫描。
- 独立复核补充：不生成receipt是正确边界，但需可执行的人工恢复入口。已定义confirm-reconciled独立发布确认，原Receipt API状态闸门与reconciliation语义保持不变；需要人工确认真实发布，而非草稿创建。

## 2026-09-28：FE-F5A 主规格同步归档检查

- 六份同步结果：新增 Opportunity 7 条、Home 4 条要求；更新 FE-F0/F1 2 条、FE-F3A 4 条、FE-F3B 2 条、FE-F4 2 条。全部21个 delta requirement blocks 与归档逐块一致，四份既有主规格37个旧 requirement blocks（含场景正文）全部保留。
- 已替换两份新增主规格的 Purpose TBD；归档工具在四份旧主规格末尾增加空行，已去除。没有业务代码、API、依赖或迁移变更，因此收尾门禁限定为规格完整性、全量 strict 与 diff-check，不重复业务测试/浏览器验收。

## 2026-09-28：FE-F5A 本地 main 整合边界

- main 与 FE-F5A 分支共同基线为 `2f52053`，无需冲突合并或获取远端提交；主工作区未跟踪内容为用户原始规格包，不加入本次提交。
- 本次授权仅覆盖本地 main 整合；六份 delta 同步与归档保留待确认，不删除仍需用于归档的隔离工作树。
- 本地快进成功：`2f52053` → 功能提交 `3012fe5`；main 上重新验证 346 后端测试、前端构建与预算、OpenSpec strict 18/18。未跟踪的原始规格包未变，未访问生产数据库或更改远端。

## 2026-09-28：FE-F5A apply 验收发现

- 独立复核后的最终修正：Brief identity_scope 不能用数字 ID join/map(Number) 读写层级对象；改为 JSON 保留 ID/层级对象，同时转换去除 null 键，兼容既有 Brand-only Brief 校验。浏览器和 API 回归通过。
- 普通 HTTP LAN 上不能假设 crypto.randomUUID 存在；使用功能探测和 getRandomValues v4 回退，幂等 key 按用户/机会/评估版本保存在 sessionStorage。实际 LAN 部署不在本次验收范围。
- 四份 MODIFIED delta 原本是片段，且 FE-F4 的 Unknown 标题与主规格不一致；已补为保留原契约与场景的完整 requirement blocks，尚未执行主规格同步或归档。

- SQLite 与 PostgreSQL 的评估/转换竞争共用机会行写锁，失败路径必须显式 rollback；否则复用 Session 时失败锁的 updated_at 可被后续 commit 写入。回归已验证。
- Opportunity 转换 scope 必须使用 typed schema，不能依赖现有 Brief 的任意数组；非法形态与字典元素返回 422，而不是 500 或生成项目。
- Home 必须先按 priority / sensitivity / expiry / recency / id 排序再 LIMIT；待决策扫描与近期项目卡片的 LIMIT 分离，避免老项目 unknown 被隐去。
- Home 回包不含 review 完整历史；近期活动来自 ProjectEvent，不以项目 updated_at 伪装排期。
- 全量 pytest 需使用隔离且已迁移 DATABASE_URL，worker.apply 使用独立 SessionLocal，不受 TestClient 内存 session override 影响；默认空数据库失败不能误判成 F5A 业务回归。

## 2026-09-28：FE-F5A-SPEC-R1 review 处理

- Review 指出的状态旁路确实存在：原规格允许普通 PATCH 直接写 `converted/archived`；现已限定为转换事务/归档路径专属状态，并拒绝非法回退。
- Assessment 原规格没有写明 `expected_revision`、409 和数据库竞争处理；现已补成 append-only 并发契约，要求失败不留下部分 revision/audit。
- Opportunity 预 Project 阶段不能使用 ProjectEvent；现采用已有 `AuditLog` 记录 Opportunity 生命周期，ProjectEvent 只从成功 conversion 开始，不新增 OpportunityEvent 表。
- 已删除单一 Opportunity `source_type` 作为真源，来源由 Signal 类型派生；转换只允许明确选择的 SourceDocument 进入普通 ProjectSourceBinding。
- Home 已固化 Today 排序、待决策优先级和稳定实体去重；核心投影失败不得伪装为空，需返回错误或 `incomplete=true` + `section_errors`。
- tasks 已改为要求 F5A 定向自动化回归，包括权限、状态旁路、并发、转换原子性/幂等/回滚、Fact Boundary 禁止、Home 优先级/去重和性能预算。

## 2026-09-28：FE-F5A Home + Opportunity 规格审计补充

- 源包包含 `proposal.md`、`design.md`、`tasks.md`、F5A 新规格，以及 FE-F0/F1、FE-F3A、FE-F3B、FE-F4 四份 delta；已放入标准 `openspec/changes/fe-f5a-home-opportunity/`。
- 不能直接用四份 delta 覆盖 canonical specs：它们是 MODIFIED 片段。归档时必须与现有完整主规格合并，否则会丢失既有项目、身份和审核契约。
- 源包的转换语义已采用：Opportunity → Project 可绑定用户明确选择的 SourceDocument；但不创建 FactPack、不冻结/绑定 Fact Boundary、不创建 IdentitySnapshot；新项目仍由 Overview 派生为 evidence-needed。
- Signal 只保存受控引用与版本/checksum/注释，不复制 SourceDocument、DataSnapshot 或 DeliveryFeedback 真源；权限在创建和转换时重新校验。
- Home 只做 Projection；没有排期实体时 `upcoming=[]`、`schedule=false`，不能从时间戳推导发布日期。
- 规格门禁：strict validation PASS；diff-check PASS。connector 基线在本地无法独立证明已从旧 main 刷新，故 apply 仍受外部 workspace reconciliation 前置约束。

## 2026-09-28：FE-F5A 规格审计

- `/home` 与 `/opportunities` 当前只是占位页；`project_overview()` 已经是可复用的确定性项目状态来源，Review/Delivery/Identity readiness 也已有项目投影，适合由 Home 聚合而不是再造状态表。
- F5A 的稳定边界是 `ContentOpportunity`（为什么现在做）、`ContentOpportunitySignal`（依据快照）和 `ContentOpportunityAssessment`（可追溯评估版本）。TopicBrief 仍是生产输入，不应接管 Opportunity。
- Opportunity 转 Project 必须显式、幂等、可回溯；建议值只能进入可编辑 Brief 草稿；只有用户明确选择的 SourceDocument signal 才能创建普通 ProjectSourceBinding，仍不能自动创建 Fact Boundary、IdentitySnapshot、Candidate 或 DeliveryTarget。
- 当前没有排期实体，因此 Home 的“近期计划”不能由更新时间伪装；规格将其收敛为近期项目活动/更新项目，等调度契约另开变更。

## 2026-09-28：FE-P1 前端加载边界审计

- 归档 CLI 使用宿主机日期 `2026-09-27` 命名，尽管当前任务日期是 2026-09-28；FE-P1 实际归档目录须以命令回执为准。五条 ADDED Requirement 已同步到新的主规格，无旧要求被替换；自动生成的 Purpose TBD 已修成正式描述。

- FE-F4 `2f3ced2` 的实际 Vite 产物只有一个 1,095.28 kB JS 文件，不能把“分成多个文件”或消除 500 kB 警告等同于首屏收益；预算应关注入口与默认路由的静态依赖闭包，并验证重型依赖不在其中。
- `App.tsx` 静态导入当前与旧页面；`Workspace` 静态引用 TipTap 编辑器，`Workflows` 静态引用 XYFlow。`PersistentProjectPages.tsx` 静态引用 `ProductionDesigner`、七个 Tab；因此仅将整个项目模块变为 lazy，不能隔离 `/projects` 与生产设计器。
- `vite.config.ts` 尚无分包配置，web package 只有 dev/build/preview，CI 当前只运行 build。首次切片优先路由级 lazy 与项目/生产边界；Tab 深拆、manualChunks、缓存策略和分页须以构建/运行数据再决定，不作为本次承诺。
- FE-P1 apply 的最新实测静态闭包为 214.45 kB raw / 69.98 kB gzip；旧 1,095.28 kB 单文件降幅 80.4%，但全站产物仍为 1,138.41 kB raw / 375.65 kB gzip。不能据此宣称所有页面更快或总 JS 更小；性能收益是按需加载边界，不是内容减少。Workspace 自身仍有 442.36 kB JS，Workflows 197.52 kB JS，仅在相应路由加载。Rollup module 归属表证实 TipTap 在 Workspace chunk、XYFlow 在 Workflows chunk，不依赖 chunk 名称猜测。
- Vite preview 不代理 `/api`，会显示 404，不能用 preview 的数字项目页证明真实操作。隔离 Vite dev + 临时 API 验证了真实项目、身份、内容单元、生产页保存项目覆盖 v1、Run succeeded 和刷新回读，随后清理唯一临时数据库；这仍不是生产环境时延或部署验收。
- Route error boundary 在加载失败时保留侧栏并支持重载；导航到另一条路由会重置错误。模拟慢网与 chunk 阻断的浏览器验收已观察到两种状态，未新增自动化测试框架。
- 独立复核指出以 `location.key` 重置错误边界会在同一路径 query 参数变化时重挂载页面，导致未保存 UI 状态丢失；根因是 React key 随每次 history entry 变化。已改用 `location.pathname`，仅实际路径变化才重置错误；需保留 query-only 导航的状态回归检查。

## 2026-09-28：FE-F4 apply 起点

- FE-F4 归档器采用宿主机日期 `2026-09-27` 生成目录，虽然当前任务日期显示 2026-09-28；README 必须引用实际路径。归档命令成功同步四份旧能力规格并新增 FE-F4 主规格（11 added / 9 modified），且自动生成的 FE-F4 Purpose 为 `TBD`，已修成正式说明。
- 独立复核把此前“项目 Draft 来源裸接口可能泄漏”的风险证实为实际旁路：`article_handoff` 的原始媒体可被其他用户读取/修改。当前已经使用 Project Run 所有权助手覆盖稿件、任务、素材、检查、文档与 Discoverability 入口；跨项目裸 ID 定向回归通过。Unknown 的普通回执与对账是两条不同路径，前者现在不能解除后者；项目历史 Candidate 也不能新建交付目标。
- FE-F4 旧裸 ID 审计发现，项目 Candidate 的大多数 Asset/Target 别名已共用所有者检查，但两个旧授权入口先返回资产状态再鉴权，可形成状态探测；现已把鉴权前置。通用 Draft/ContentJob 裸接口仍是 FE-F2 既有来源表面，需与 FE-F4 Candidate 边界分开评估，不把项目 Candidate 保密性等同于其来源 Draft 已完全隔离。
- 当前 `ProjectWorkflowOutput` 自动关联的可发布内容形态主要是 `draft`；纯媒体 `material_revision` 不构成完整可发布 Candidate。FE-F4 冻结适配器须基于持久化 Run/Output/Draft 链验证，不能把素材生成成功视为内容成品。
- FE-F3B `ContentAccount` 不包含已验证渠道、凭据或远端发布能力。自动交付必须依赖真实验证映射；没有映射时只允许明确标注能力未验证的人工包/复制交付，并拒绝远端自动动作。

## 2026-09-28：FE-F4 规格审计发现

- 后续主工作区本地 `main` 已快进至 FE-F3B `55eba02`；直接核实了四份 canonical 主规格、`ContentAccount`、`IdentitySnapshot`、身份 API 和 Alembic head `f3b000000001`。这解决了本地 apply 基线缺失；连接器端到端回读仍未单独验证。
- 初审时主工作区基线 `1fa4520` 与 FE-F3B 已归档提交 `55eba02` 分离；FE-F4 因而先在后者的隔离工作树做规格审计。该本地基线差异已由后续 `main` 快进解决。
- 来源包四份 `MODIFIED Requirements` 只有新增句子，没有主规格要求原文及既有场景。OpenSpec 归档会用 delta 替换同名 Requirement，必须把原约束和场景补全后才可标记 `SPEC_READY`。
- OpenSpec 的 delta JSON 读取只把同名 Requirement 的首段作为 `requirement.text`；把新增规范写成第二段虽然 strict 可通过，但合并后可能不成为规范正文。九个 MODIFIED 要求已将新增句子并入首段，并用 `openspec change show --json --deltas-only` 验证解析结果。
- 当前 `ContentAsset` 的 `draft_id`、`topic_brief_id`、`fact_pack_id/version`、`approved_revision` 非空，状态默认 `approved`；`Review.draft_id/revision_no` 非空。项目 Candidate 允许先冻结后批准，且 FE-F2 Unit 输出不保证有 TopicBrief/Draft；FE-F4 必须明确项目候选的真实来源与哪些旧必填列需变可空，禁止造假旧 Topic/Draft ID。
- `ContentAccount` 当前只有 Persona、名称和状态，没有渠道或平台凭据字段。新 DeliveryTarget 可以引用稳定账号 ID，但不能据此声称平台能力/渠道已验证；需界定显式账号映射与能力检查，保留 `account_ref` 历史快照。
- 独立规格审阅指出旧 `article_handoff` 手工包强依赖 Draft/v1 媒体字段；非 Draft 的 v3 Candidate 若沿用此路径会在交付时失败。已规定 v3 schema-aware 本地成品包适配器和真实字节/权利校验，v1 builder 仅处理真实 v1 资产。
- 现有 DeliveryTarget 唯一约束仅按 `account_ref`，两个不同 ContentAccount 若引用同一字符串会冲突。FE-F4 规格改为新增不可变 `authorization_account_key`：项目稳定 Account ID / 旧目标原 account_ref，替换唯一约束并统一幂等查询；不伪造旧行 ContentAccount 关联。

## 2026-09-27：FE-F3B 规格审计发现

- FE-F3B 归档 CLI 使用宿主机日期生成 `2026-09-27-fe-f3b-content-identity`，尽管任务环境日期显示 2026-09-28；文档须引用实际目录。归档自动同步四份主规格：三份 MODIFIED、一份 ADDED。FE-F2、FE-F3A、FE-F3B 主规格原有或新生的 `Purpose: TBD` 及 FE-F0/F1 已过时的 mock Purpose 均需改为当前长期契约描述。

- 来源 `fe-f3b-content-identity/` 的新能力规格采用完整主规格格式，不能原样作为 OpenSpec change delta；三份 MODIFIED 规格也只写增量、会在归档时丢失原有场景。已改成 ADDED delta 并补回被修改主要求的完整旧场景。
- `BrandVoiceVersion` 当前没有 owner_user_id；FE-F3B 只能复用现有全局 published 版本，不能声称“按 owner 验证”却没有所有权字段。历史引用不因未来归档而被重写。
- 现有 `ContentPersona` 可能无 Brand、无身份修订。迁移不回填；显式新建单位可冻结真实 Persona ID 与空 profile/null revision，并显示身份资料不完整，而不是编造品牌、定位。
- Unit 变更父级时，省略 Account/Series 不能被解释为悄然清空不兼容子级；需要明确替换/清空，否则 422。归档祖先拒绝新单位、默认工作流和 Run。
- `test_worker_task_function_executes_locally` 的模块级 `SessionLocal` 依赖默认 SQLite 文件，和测试 fixture 的内存库不同。新工作树默认文件缺表导致基线失败；独立临时文件库初始化后全套 296 通过，未改测试或业务逻辑。

## 2026-09-27：FE-F3A 规格复核发现

- 用户提供的结构化包与合并 Markdown 内容属于同一 FE-F3A 草案；标准活跃变更采用 `fe-f3a-content-project-core-completion` 作为 change 名，能力名保留 `fe-f3a-content-project-core`。原始资料未删除或覆盖。
- FE-F2 基线 `734990c` 的 `ContentProject` 已有 `status` 和所有者；`DELETE /content-projects/{id}` 在无单元时物理删除。一旦 FE-F3A 为项目写入 append-only `ProjectEvent` 和 Brief 等子记录，原行为会丢失历史或触发 FK 错误。因此提案明确改为归档项目、历史可读、项目级写操作（含 legacy run）拒绝。
- `SourceDocument`、`FactPack`、`MaterialRevision` 没有项目所有权；项目绑定只能在现有全局资源权限内引用，不应把项目拥有者视为全局资源拥有者。Source/Material 引用表的唯一键要求 detach 后 reattach 复用原记录。
- `materials_service.create_revision` 在数据库提交前写入内容哈希字节；项目上传的数据库原子性不能自动涵盖文件系统。规范须要求失败后清理或跟踪未引用字节，不可误删已共享哈希对象。
- 修订表 `(project_id, revision_no)` 唯一约束能阻止重复版本，但并发抢写若不捕获完整性错误会 500；规范要求回滚并返回 409，且事件同一数据库事务提交。
- 这轮只复核/校准 OpenSpec，不声称 FE-F3A 功能已实现；源包中要求定向回归测试为未来 apply 范围，本轮没有生成测试代码。

## 2026-09-27：FE-F3A apply 核对

- 五表在隔离库可逆迁移；带 FE-F2 项目、单元、Run 和 checksum 的 e5→f3a→e5→f3a 均能回读历史。生产迁移未执行。
- Browser 端使用独立 SQLite 验证七标签刷新、Brief 两版、Source 绑定、事实边界 Clone 后返回并冻结、素材上传和版本/活动聚合；项目上传与系统引用同一 revision 仍由唯一项目引用幂等处理，不复制字节。工作流关联可另列为独立来源。
- 现有素材存储为哈希寻址。项目上传事务失败时回滚 Material/Revision/Reference 与事件；不删除可能被其他资源共享的同哈希文件。新哈希失败写 `material.upload_orphan_candidate` AuditLog（相对路径/哈希/项目，`entity_id` 只存 50 字符前缀以兼容 PostgreSQL）。已有 `run_retention` 现消费该候选：一日宽限、每批上限、路径验证、查询已提交的 MaterialRevision/DraftMedia/AssetMedia 引用，仅删无引用字节；未处理候选不受普通 90 天 AuditLog 过期清理影响。若数据库不可写导致记录也失败，则写错误日志，不掩盖原上传失败。保留流程按现有维护入口执行，不在请求或 API 启动时自动扫盘。
- 清理计划原来指向未注册的 `retention_sweep`，已补对应 Celery task。仅做“检查引用后 unlink”仍会与复用同哈希文件的未提交写入竞态；现在写入方持有按哈希前缀划分的跨进程文件锁直至提交/回滚，清理方在引用核查和 unlink 期间持同一把锁。清理每个候选立即提交，避免持数据库写锁再等待下一把文件锁。
- 普通 Project/Unit PATCH 若允许直接设置 archived，会绕过专用归档事件及单元历史语义；已改为拒绝，要求走专用归档/删除入口。
- 非阻塞债务：前端主包约 1,058 kB，仍有 >500 kB 构建提醒；旧全局 FactPack 页面关于冻结条件的提示与当前类型化观点条目规则不完全一致，未在本切片重做该页面。
- 独立审阅还验证了三个领域缺口：归档项目的项目页面创建 Source 会先在全局 Source 库写成功、随后关联失败；旧项目 PATCH 可绕过 Brief 修订改目标；显式素材未向共享读模型传来源字段。现分别通过归档只读/创建前状态检查、目标 PATCH 拒绝、MaterialRevision provenance 回传收口。Evidence 补独立冻结条目区，Brief 历史可展开全部字段。

## 2026-09-27：FE-F2-R1 最终复核边界

- 用户提供的外部复核只覆盖 R1 五项补丁，结论为 `REVIEW_PASSED`，允许归档及本地提交；连接器未保存 pytest/build 原始 execution artifact。本轮须直接复跑门禁，不把复核文字当作命令执行证据。
- 归档同步会把 FE-F0-F1 的内容矩阵修订写入主规格，并建立 FE-F2 主规格；不使用 `--skip-specs`。归档与本地 commit 不等于 push、merge、部署或生产数据迁移。

## 2026-09-27：FE-F2-R1 复核发现与决策

- `pinned_workflow_id` 决定 Run 的实际版本；设计器以前在无项目覆盖时读最新角色默认，形成所见与执行版本错位。新增按单元固定版本读取，不自动改绑旧单元。
- 单独存在 `ProjectWorkflowBinding` 不构成不可改写的执行历史；Run、DataSnapshot、ProjectWorkflowOutput 才构成。历史身份变化通过新单元与旧单元归档保留，而不是篡改旧行；归档历史可读、项目及旧裸 Run 入口都禁止再执行。
- `resolve_placeholders()` 只应用于节点 config；角色默认模板中其余字段的项目/单元绑定必须拒绝，不能存一个运行时不解析的占位符。
- 失败重跑开始前必须持久化清空 current output/hash；旧成功结果由不可变 Attempt 保留。六类节点的 `kind` 优先写入 Step.node_type。

## 2026-09-27：FE-F2 apply 起点

- 工作流定义缺少持久 owner/scope 时，旧绑定切走会让历史定义失去归属；本轮迁移补可空 `Workflow.owner_user_id/scope`，仅新项目/角色默认版本使用，旧 Topic 定义保持兼容。
- 现有引擎将完整节点输出哈希用于 stale；DataSnapshot 每次刷新都会生成新 ID，即使内容不变。Data Node 的 stale 判断现改按 `data_checksum`，仍保留每次快照和 Attempt 审计。
- 现有素材版本实体是 `MaterialRevision`，而非名为 `AssetRevision` 的表；项目共享素材需要对这个真实版本做引用，不能凭节点返回路径或成功状态伪造素材。
- FE-F2 隔离验收中的 `/outputs` 404 来自无 reload 的旧 API 进程；新进程中同一路由 200，之前保存的 Run 可读回。Provider/Model 当前由全局模型路由选择，节点配置不可独立切换，因此设计器只暴露当前真实组合，并在保存/启动时拒绝不匹配值，避免“可选但被执行器忽略”。
- `ProjectWorkflowOutput` 对媒体版本原仅检查数据库路径/哈希字段，文件丢失仍可进入素材池；现增加字节存在与哈希匹配检查。图文/视频壳层对未生成素材和片段保持空状态。
- 全量测试默认继承本机异常 `NO_PROXY/no_proxy` 时，旧 DSH 探测链路的 12 项在 httpx URL 解析处失败（非法端口 `:1`）；仅对测试命令移除这两个环境变量后 274 项全过，未改 DSH 代码或全局环境。前端主包约 1.04 MB 是既有性能债。
- 最终 UI 复核发现“另存为角色默认”原与未保存状态绑定，导致先保存项目覆盖后无法再显式另存；现只在定义为空或请求忙时禁用，已保存项目版本也能另存，两个保存出口继续互不改绑。
- 历史 Run 画布原误用当前项目覆盖定义：项目 v2 出现新节点而 Run #1 的 checksum/step 仍属 v1。现运行模式读取 `run.definition`，设计模式读取当前项目草稿；隔离库浏览器在同一页面切换两模式已分别显示旧/新节点。

- 本轮开始时 `main@c044085` 已干净；用户同意在当前目录创建 `codex/fe-f2-persistent-production-workflow` 分支，因此不使用缺少旧本地改动的独立 worktree。
- Alembic 当前唯一 head 为 `d4audit00004`；FE-F2 迁移应从该版本增量接续，验证只用隔离本地测试库。
- 现有 `User.role` 是鉴权角色，不能代替内容 Persona；需要单独持久化内容身份归属。项目权限不能仅依赖请求中的 project_id。

## 2026-09-27：FE-F2 正式 review 的代码核对

- `apps/api/app/routers/workflows.py` 的旧 run detail、complete、retry、rerun、rerun-from-here、attempts 与 cancel 仍按裸 `run_id` 读取；`list_runs` 列出运行记录，`list_workflows` 的序列化还嵌入最近运行。只保护新 project-scoped URL 会留下读写旁路。
- 同文件的 clone/publish 使用裸 Workflow ID，raw create-run 也按 workflow ID 启动；若 FE-F2 把项目版本写入现有 Workflow 表，这些定义入口亦须授权或明确拒绝。统一检查必须以持久化项目/单元归属为准，不能相信请求携带的项目 ID。
- `workflow_engine.advance` 根据 `definition_json.edges` 判断依赖，`ready[0]` 从待执行节点取下一项；因此视觉顺序可以作为独立节点的稳定排序，但拖拽不能隐式改写 edges 或映射。
- Persona 默认模板从项目流程派生时必须服务端只保留通用结构与可共享 profile；项目、运行、快照、素材、稿件、候选、attempt 和实际输出要参数化或拒绝，不能直接复制 definition/context。
- FE-F2 回归测试现经用户明确要求；测试旧 API 权限、模板隔离、冲突、快照 stale、断连插件、副作用重跑、素材归属和历史 checksum 是该变更本身的验收，不是额外功能。

## 2026-09-27：FE-F2 V5 校准依据

- `AIContentStudio_Frontend_Product_Contract_V1_2026-09-27.md` §10–11 明确六类节点、拖拽与键盘替代、项目覆盖和显式另存角色默认版本，以及可扩展 Data Source Plugin 的六类起始来源。
- 旧 FE-F2 proposal/design 把角色默认版本推至 F3，并将首个 Data Source Plugin 描述得过于接近 Studio Source 专用适配；用户已明确要求前者在 FE-F2 真实持久化。
- 当前 `Workflow` 已有 key/version/checksum，`WorkflowRun` 可冻结版本，`WorkflowStepAttempt` 记录审计；可扩展绑定和输出关联而不新造引擎。当前模型未见持久化的内容 Persona/Role，FE-F2 需最小身份归属；鉴权角色 editor/reviewer 不能代替内容角色。
- 插件“已注册”不等于“已连接/可执行”。Notion、Obsidian、媒体数据、API、SQL 可以先有描述符和配置体验，但执行结果必须由服务端真实连接能力决定；缺连接时不得生成成功 Attempt、Snapshot 或素材。
- 用户只确认了角色默认版本这一边界；完整校准后的 FE-F2 OpenSpec 尚未被批准 apply。

## 2026-09-27：FE-F0-F1 复核补丁范围

- 反馈属实：`STATUS_EXPLANATION` 原先只在 ProductionShellPage 读出；项目默认总览和矩阵缺解释。
- 已在异常项目的总览/矩阵复用说明；非异常项目不增加图例。前端构建和浏览器观察通过，未新增测试代码。
- 本地 `main` 仍包含更早未提交的 API、迁移、Materials/ReviewPublish 路由等改动；提交必须精确暂存本切片，不能 `git add -A`。

## 2026-09-27：FE-F2 真实工作流提案核对

- `apps/api/app/models.py` 已有 Workflow、WorkflowRun、WorkflowStep、WorkflowStepAttempt；现有运行通过 `topic_id`/channel/content_form 追踪，尚无持久化 ContentProject/ContentUnit 归属。
- `apps/api/app/routers/workflows.py` 已提供版本 clone/publish、启动、人工节点完成、节点重跑、从节点重跑和 attempt 查询，但没有项目覆盖保存/设计编辑接口。
- `workflow_engine.rerun_node` 对 side-effect plugin 禁止泛化重跑，`rerun_from_here` 也检查受影响节点；FE-F2 必须沿用闸门，不能为 UI 绕过。
- FE-F0-F1 的项目模型还在 `apps/web/src/product/mockProjects.ts` 的 `localStorage`；要实现跨会话持久化，需要显式后端项目/单元迁移与 UI 切换，不能把浏览器 mock 当真实记录。
- 原变更提案把角色默认模板发布留给 F3；这一历史观察已由上面的用户确认和 V5 校准取代。

## 2026-09-27：FE-F0-F1 前端基线

- 当前 `apps/web/src/App.tsx` 以旧 Source/Topic/Workflow 导航为主，已存在用户未提交的 Materials 与 ReviewPublish 路由；实施时保留它们。
- 前端为 React Router + TanStack Query + Tailwind；已有 Button、StatusBadge、Modal、Drawer、EmptyState、Spinner、ErrorBanner 可复用；`apps/web/package.json` 仅提供 build，无独立 lint/test 脚本。
- FE-F0-F1 只做本地 mock 的 ContentProject/Unit/AssetRevision 视图与交互；FE-F2 工作流设计器和后端结构均不在本切片。
- 浏览器已核对项目列表、七标签、矩阵增删改、共享素材抽屉/筛选和选中单元生产入口；异常样本同时显示受阻、已过期、待核对，状态不合并成“失败”。
- `/review` 与 `/assets` 用作新一级工作区占位页；旧页面仍在 `/legacy/review` 与 `/legacy/assets`，其他旧路由保持不变。前端 mock 由 `localStorage` 保存；已存在的浏览器数据优先于最新初始样本，因此素材数可能与新会话初始值不同。
- `npm run build` 成功，Vite 提示主 JS 包约 1.0 MB、超过 500 kB 建议值；这是性能待办，不影响本切片构建。仓库前端没有独立 lint/test 脚本，未声称完整自动化测试通过。

## 2026-09-24：PRD 作为产品长期目标

- 用户确认 `03_ai_content_studio_PRD.md` 是指导项目开发的最终产品需求基线，并纠正“三渠道就是全部”的误解。PRD 原文称三项为“首选渠道”；原对话的 V1 目标包含 11 个文章/图文/社交平台，另保留抖音脚本。已把此范围以 §3.1 补入 PRD，避免文件本身继续遗漏完整目标。
- 当前静态核对：`models.py:Channel`、生成 renderer、工作台已有抖音/小红书/公众号；旧导出支持抖音 MD/TXT/JSON/SRT、小红书 MD/TXT/JSON。`article_handoff.py` 的新候选/交付目标只接受公众号与 X Thread；小红书 renderer 当前输出图片 Prompt，未证明有序实际图片组成品。
- PRD §15 的 15 项验收与 §16 的 30 个真实 Topic 门槛尚未在本轮完成运行核对；M1 成果不能直接等同整个 V1 达标。

- 当前工作区：`AIContentStudio`
- 连接方式：固定域名
- 连接器名称：`Codex with ChatGPT · AIContentStudio`
- 当前本地连接检查：通过
- 新账号连接状态：已授权，账号显示为 `Austin`
- 新账号项目状态：已绑定正确的 `AIContentStudio` 项目合集
- 工作区读取验证：通过

## 2026-09-22：V1 范围基线

- 指定原对话：自媒体平台对比总结（6ab23aa1-ce20-83e9-9acb-c6ffeda87191）。
- 用户最新明确需求：内容中心服务量化平台、媒体采集分析工具及其建设过程；V1 文章/图文，V2 视频。内容中心不重做上游量化与采集。
- 对话整理的 V1 渠道清单：公众号、头条、百家号、知乎、小红书、X、微博、B站专栏/图文、搜狐号、企鹅号、网易号。具体账号可用性和自动分发权限仍须核验。
- 本地 `docs/AI_CONTENT_STUDIO_REQUIREMENTS_REFINED.md` 仍以抖音、小红书、公众号三渠道为主，与最新文章全渠道目标存在差异，不可直接作为本轮实施基线。
- 页面旧架构回答和最新需求整理同时存在；以用户最后说明与三产品矩阵定位优先，不把未来架构全部塞入 V1。

### 本地源码核对（静态证据，非本轮运行验收）

- `models.py:Channel`、`routers/topics.py:VALID_CHANNELS`、`generation/renderers.py:render_body`、`pages/Topics.tsx` 均为抖音/小红书/公众号三渠道。不能仅加菜单便算全渠道完成。
- `generation/orchestrator.py:run_generation_for_job` 直接从 Topic + FactPack 各自生成平台 Draft；尚无中立母稿和平台稿之间的版本依赖。已有 TopicBrief、ContentJob、Draft、Review、ContentAsset 可复用，不宜重建一套同义实体。
- `routers/generate.py:update_draft` 新建 revision，但保留旧 `structured_json`；正文编辑后的结构、图片文案和引用可能脱节，需要定义统一内容真源及重校验机制。
- `routers/fact_packs.py:freeze_fact_pack` 只固化状态/checksum，FactPackItem 仍引用可变 Fact；`routers/facts.py:update_fact` 未检查冻结包引用；生成时读取当前 Fact。冻结事实包不等于冻结事实值，必须补不可变证据快照或等价保护。
- `routers/reviews.py:approve` 检查事实校验、包状态、最新稿件版本，复制批准正文至 ContentAsset；这是可复用的文字审批基线，尚非完整的账号/素材/规则/声明发布快照。
- `services/asset_media.py` 是图片说明占位及上传入口；上传追加数据库行却可能按原 media.id 写同一路径，不能把记录追加直接当成素材字节不可变保证。小红书最终图片组未见完整生产和打包链路。
- `workflow_templates.py:build_gen_export` 当前公众号封面节点位于批准之后；`workflow_engine.py:_h_publish_wechat` 还会截断标题、选择动态封面/占位封面，再调用 wewrite 建草稿。批准内容与最终交付内容必须先统一。
- `workflow_engine.py:advance` 保存步骤状态且可人工暂停，但自动节点在调用内串行推进；任一失败/人工等待均会返回整次运行。`retry_run` 将失败节点直接重置，因此对外建稿结果未知时存在重做风险。代码尚非持久化可靠的独立发布任务系统。
- `tasks/worker_tasks.py` 已有 Celery 生成与拉取任务，保留该技术栈；`dispatch_generation` 在外层生成请求 commit 前 `.delay()`，任务投递与数据库持久化需要可靠衔接，不能只把函数改成异步。
- `routers/external.py` 外部内容目前是独立 ExternalContent 汇聚入口，可直接人工改 published；它没有自动进入事实/母稿/审核链，不能等同候选池及可信发布回执。
- `services/writing_pipeline.py` 已有风格、润色和安全扫描薄封装，但依赖本机其他目录；缺失可降为黄词扫描。`routers/reviews.py:approve` 未统一强制安全扫描，所以不能声明已有全入口安全阻断。
- `routers/dashboard.py` 聚合生成/审核/导出内部计数，未实现平台效果与产品反馈闭环。`deps.py:get_current_user` 是开发身份头，不能用于对外商业服务验收。

### 讨论状态

- 第一轮 INIT（任务 c2c_a173）曾显示思考中，但刷新后消息未保存；不能视为实际完成讨论。恢复聊天模式后再次请求当前工作区及 README 读取，出现生成错误，单次重试仍报错。经已保存会话 → 项目列表 → 原蓝图对话重新进入，仍只保留旧对话内容。
- 本轮最后一次本地连接检查全部通过，无需重新授权/重建的指示；原聊天的新文件读取未得到成功答复，未证明端到端可用。未删除连接器、另开对话或向其他工作区发送请求。协作检查点已标记阻塞，需原会话恢复回复后继续。
- 后续恢复：用户确认能回复后，本轮在同一原对话点击发送最小读取核验，约 1 分 25 秒后返回 AIContentStudio 及 README 第 3、9–13 行两项具体事实；端到端读取验证现已通过，未重建连接器。此前报错的根因未查明。
- 第一轮 ChatGPT 完整 PLAN 已收到：认可保留现有栈与 Topic 聚合，建议首批缩为“已有满意文章 → 公众号 + 一个新增渠道 → 可核实交付”，独立目标、人工凭证和最小反馈必须提前；内容审批与目标交付授权分开记录，界面可一次确认。建议 X 线程作为新渠道样本，但尚非用户选定。
- 第一轮新增源码观察已由本地定点复核：REST 接入指纹只哈希排序后的 statement，需防日期/单位/来源版本变化被误去重；默认抽取器只提取数字及日期类候选，纯观点/建设经验需显式类型化入口；AssetMedia 强制关联批准后才创建的 ContentAsset，最终成品审批需补稿件期素材关系。
- 第二轮已提出设计挑战：不扩建通用证据平台；在现有冻结边界补值快照；保留 Markdown 主数据并失效派生物；明确非数值文章的证据门槛，以及内容审核/账号授权的分工。首批可用人工交付证明价值，自动草稿需独立准入，旧路径不得绕过新门槛。
- 第二轮完成：M1 采用类型化 FactPackItem（事实/事件、引述、作者观点）及冻结值，不把非数值文章伪造为数值事实；审核严重程度和是否完整覆盖分开。已定点复核 factchecker.py：只取前 50 条事实/前 4000 字，模型不可用或失败透传确定性结果；不能据此声称全篇语义审查完成。
- 已定点复核 assets.py：素材删除可直接移除关联记录；导出仅按渠道格式检查。后续需保护批准清单引用、区分存档下载与正式交付包，且不得把内部证据默认放进公开包。所有建议仍为规划，未修改这些源文件。
- 已在原对话文档预览中补读完整附件 `AI_Content_Center_Requirements_R2.md`。与摘要相比，还需显式保留版本比较/锁定、定时栏目数据就绪、来源公开及模型使用权限、排期首发冲突、发布后勘误、收益资格/收入状态和四类样本验收。已加入对齐草案的 A01–A64 分组追溯表，不把附件建议自动视作用户逐项确认。
- 第三轮已完成，工具输出确认方案全文读取且未截断、findings.md 全文读取；ChatGPT 判定规划 DONE，无严重修正，OpenSpec 未创建且实施 HOLD。提醒历史证据显式 legacy_untyped、可空 fact_id 的相关读取路径兼容，以及 M1 重复/中断/未知结果验收；这些是实施约束，不是现有功能结论。
- 本轮新版独立复审通过：X 单帖/线程/长帖/Articles 均保留 V1 成品适配，逐“平台 × 形态”验收；M1 仅取公众号 + X 线程作为建议样本。自动化下限和首批渠道尚待用户确认，账号分发能力未验收。
- ChatGPT 最终复核结论：规划 DONE，无严重修正。必须保留三类门槛：证据一致性、交付安全、失败/重复安全；内容审批与目标账号/动作授权分离；Markdown 是母稿真源，结构化内容、引用、检查和包均为可失效派生物。
- 用户已确认按该思路继续落地：首批接受“完整成品包 + 人工发布回填”，公众号自动进入草稿箱不作为同时完成条件。
- OpenSpec 已落地为 `openspec/changes/add-evidence-bound-article-handoff/`，严格校验通过。实现前提是新 M1 目标不调用远端平台 API，旧入口不能绕过新快照、审批和目标授权边界；历史记录保持可读，不通过迁移伪造新批准。
- 执行中新增 API：`/api/v1/article-handoff/...`，覆盖母稿导入、公众号/X Thread 适配、目标授权、本地成品包、人工回执和反馈；人工确认状态不会写成 `published` 或平台已验证。
- 迁移实测：`alembic upgrade head` 已成功到 `d31415926535`。第一次迁移尝试暴露 SQLite 不支持直接 `ALTER COLUMN`，已改为兼容增量迁移并复跑通过；仍需在 PostgreSQL 路径复核约束差异。
- 测试实测：虚拟环境 129 passed / 12 failed；失败共同原因为既有插件状态地址 `:1` 触发 `httpx.InvalidURL`，不属于本次链路。该问题未修复，避免扩大范围。

## 2026-09-22：M1 实施复核与验收

- 成品包不能只返回受登录保护的下载路径；现已提供受目标授权保护的 ZIP，包含 Markdown、HTML 或 Thread JSON、manifest、说明和按批准哈希复核的媒体字节。
- 已人工确认、失败或待核对的目标重新读取成品包时不再回退到等待回填。相同授权目标和相同回执请求在并发冲突后回读既有记录。
- 授权操作人是 M1 账号边界：非授权 editor 不能取包、下载 ZIP 或写回执。该边界不等同于未来的组织/多账号权限模型，后者须单独设计。
- 冻结快照、母稿、候选 manifest 与资产记录保留历史；公开使用权限撤销另存控制记录，并阻止未完成目标，而非篡改已批准历史。
- Alembic 迁移优先回填可从关联资产/目标恢复的 hash；无从恢复的旧记录保留为不具 M1 资格的 legacy 行，避免迁移伪造审批或丢失数据。
- 旧工作流边界已收口：`gen_export` 默认不再生成 `publish_wechat`，仅显式遗留配置才保留；执行器还要求节点带遗留开关，并继续拒绝绑定 `MotherRevision` 的 M1 资产。
- ChatGPT 对最终修复返回 `DONE`；OpenSpec 变更已归档，未同步 delta spec，因为当前仓库没有对应的主 specs 目录。
# 2026-09-27：连接器故障检查

- 用户提供四项独立调用均为 `internal error`。再次核验发现公开 MCP 返回 530、该工作区 cloudflared 的 HA 连接数为 0，虽然 `doctor` 显示绿灯且协议为 HTTP/2。
- 对 AIContentStudio 定向执行 `c2c restart --tunnel` 后，工作区 cloudflared 使用 HTTP/2，HA 连接数大于 0，公开未授权 MCP 请求返回 401；这确认传输链路现已恢复。
- ChatGPT 连接器的端到端调用尚未由当前会话复验；需要在 ChatGPT 中重试 `workspace_info`。未重建或重新授权连接器。
- 2026-09-27 后续复查：bridge、MCP、OAuth、named tunnel 均为 green；公开 MCP 返回 401、对应 cloudflared 使用 HTTP/2 且 HA 连接数大于 0。状态详情出现“no free edge addresses”警告，但不足以推翻当前健康探测，故未重启。ChatGPT 端如仍失败，需按具体工具错误继续定位。
