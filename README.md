# AI Content Studio（AI 内容生产中心）

事实驱动的内容生产系统：把结构化数据、研究笔记、文件、URL、人工观点整理成 **FactPack**，面向抖音 / 小红书 / 公众号生成内容，经事实校验与人工审核后导出；公众号可进一步自动写入官方草稿箱。

长期产品目标以 [`03_ai_content_studio_PRD.md`](03_ai_content_studio_PRD.md) 为准；其中 §3 的三渠道是首选样本，§3.1 已补入原对话整理的 11 平台文章/图文 V1 目标，并保留抖音脚本。`04_ai_content_studio_execution_plan.md` 是旧版执行参考，边界澄清稿见 [`docs/AI_CONTENT_STUDIO_REQUIREMENTS_REFINED.md`](docs/AI_CONTENT_STUDIO_REQUIREMENTS_REFINED.md)。

### FE-F6E 渠道变体检查（进行中）

- 需求背景：一个已保存的渠道变体只有在来源 Master 当前、必要检查有效，且目标形态/素材/证据检查通过时，才可能进入后续 Candidate v5 冻结。
- 目录结构：`apps/api/app/services/channel_variants.py` 负责项目授权后的 Variant 历史、只读来源门槛和追加式检查；`channel_adapters.py` 负责五种受控形态的确定性成品投影；`candidates_v5.py` 装载并构建 v5 清单，`project_review.py` 提供冻结；规格位于 `openspec/changes/fe-f6e-channel-variants-content-matrix/`。
- 已完成：来源 Master 的上下文与检查状态进入 Variant `ready` 投影；`variant_package` 验证受控 Adapter 的确定性成品投影并记录哈希。v5 manifest builder 已接服务端 DB 快照和项目级 Freeze；仅当前且已通过检查的 Variant 可冻结，重复请求幂等，旧 Draft/Master/Workflow 来源列保持空。v5 内容审批按 Variant 系列判定当前性；交付授权仅允许本地包/人工交接，ZIP 从冻结 v5 内容和实时验证的精确素材字节生成，不回退旧 schema。已有授权可读取历史包，但仍须通过实时公开权利与来源完整性验证。
- 待完成/TODO：冻结全面并发锁、跨形态与历史/安全回归、v5 Review 预览/差异/检查、Matrix 和前端/浏览器验收仍在 F6E 后续任务；F7 远端 Provider 不在本阶段。
- 关键设计决策：channel-neutral Master 的目标平台检查由 Variant 承担，不以 v4 直接冻结资格替代来源门槛；检查结果追加保存，读取时仍进行实时来源与权限漂移判断。v5 清单只接受服务端提供的有界 canonical 快照，绝不沿用 Draft/Master 作为 Candidate 来源指针。
- 依赖与启动：沿用现有 FastAPI/SQLAlchemy 环境；在 `apps/api` 运行 `PYTHONPATH=. .venv/bin/pytest -q tests/test_f6e_freeze_v5.py tests/test_f6e_candidate_manifest_v5.py` 进行定向回归。本切片不增加依赖或迁移。

### FE-F0-F1 前端产品骨架（2026-09-27）

- 需求背景：以 [`AIContentStudio_产品战略与总体架构蓝图_NorthStar_V2_2026-09-26.md`](AIContentStudio_产品战略与总体架构蓝图_NorthStar_V2_2026-09-26.md)、[`AIContentStudio_Frontend_Product_Contract_V1_2026-09-27.md`](AIContentStudio_Frontend_Product_Contract_V1_2026-09-27.md) 和 V5 原型为方向，本切片按 [`AIContentStudio_WORK_HANDOFF_FE-F0-F1_2026-09-27.md`](AIContentStudio_WORK_HANDOFF_FE-F0-F1_2026-09-27.md) 建立项目驱动的前端入口；不表示 PRD 全部完成。
- 目录结构：`apps/web/src/product/` 包含本地模拟项目数据、项目页面、共享素材抽屉和其余工作区的占位页；`apps/web/src/App.tsx` 负责九个一级工作区路由与旧功能入口。
- 已完成：九个一级入口、项目列表与七标签、内容矩阵增删改、文字/图片/视频单元、共享素材来源筛选、单元生产入口、健康和异常项目样本及受阻/过期/待核对状态区分。旧功能仍可从“现有功能入口”访问。
- FE-F0-F1 复核补丁：异常项目的总览和内容矩阵现直接说明受阻、已过期、待核对、等待人工、就绪五种状态的含义。
- 待完成/TODO：本切片原定的工作流设计器与真实 API/权限/持久化已由下方 FE-F2 承接；FE-F0-F1 自身不包含真实素材上传、发布或后端模型迁移。
- 关键设计决策：新项目数据只保存在浏览器 `localStorage`，与现有后端业务数据隔离；首次访问加载演示样本，浏览器已有本地数据不会被新样本覆盖。生产页仅提供入口与上下文，不伪装为可用生产流程。
- 依赖与启动：沿用下方前端启动命令 `cd apps/web && npm install && npm run dev`；静态构建用 `npm run build`。本切片未增加依赖。
- 规范记录：[`openspec/specs/fe-f0-f1-project-experience/spec.md`](openspec/specs/fe-f0-f1-project-experience/spec.md)；实施归档见 `openspec/changes/archive/2026-09-27-implement-fe-f0-f1-product-shell/`。

### FE-F2 本地实现与 R1 复核通过：真实工作流执行与持久化

- 需求背景：用户明确下一步须让生产工作台接后端，保存并真实执行工作流；仅前端模拟不满足目标。
- 目录结构：`apps/api/app/routers/content_projects.py` 提供持久化项目、单元、流程与快照 API；`apps/api/app/services/project_*` 和 `data_source_plugins.py` 承接授权、版本、产物和数据来源；`apps/web/src/product/PersistentProjectsPage.tsx`、`PersistentProjectPage.tsx`、`PersistentProductionPage.tsx` 与 `ProductionDesigner.tsx` 是真实项目入口。原 `ProjectPages.tsx` 和 `mockProjects.ts` 留在 `/projects/demo` 作本地演示。规格见 [`openspec/changes/archive/2026-09-27-fe-f2-persistent-production-workflow/proposal.md`](openspec/changes/archive/2026-09-27-fe-f2-persistent-production-workflow/proposal.md) 与同目录 design/specs/tasks。
- 已完成：新增可逆增量迁移；项目/单元/内容身份 CRUD 与旧 Workflow API 的项目归属闸门；项目覆盖和角色默认的独立不可变版本保存；Data Source 六类描述符、只读 Studio Source 快照、变化传播 stale；项目 Run/Attempt 回读及真实素材字节校验后的项目关联。真实项目页、三形态生产区和设计/调试画布已接后端；隔离库浏览器验收了创建、保存、真实执行、刷新回读、双保存、后续单元默认绑定、断连阻断和素材抽屉。Provider/Model 只可绑定后端当前可执行路由，保存、启动与节点重跑均防止配置漂移。R1 收尾修正设计器读取单元固定版本、无执行历史原地编辑/显式重绑、有历史替换归档、模板占位符解析边界、节点 Kind 审计和失败重跑输出隔离。后端全量测试在清除本机异常 `NO_PROXY/no_proxy` 后为 279 passed；前端构建和 OpenSpec strict 通过。
- 待完成/TODO：未执行生产迁移、发布或真实第三方 Connector 验收。当前可执行 Data Source 仅只读 Studio Source，其余来源明确“未连接”；视频生成器未验证时不展示片段。既有前端主包 >500 kB 是性能债，不阻塞 FE-F2 本地切片，也不代表完整 PRD/V1 已达标。已归档单元的部分设计控件仍可本地进入编辑态，但服务端拒绝保存和重跑；后续可做只读 UX 打磨。
- 关键设计决策：复用既有 Workflow/Run/Step/Attempt 与副作用闸门；所有项目绑定运行通过新旧 API 均按同一项目权限校验；角色默认模板保存须通过服务端项目值可移植性 Gate；拖拽只改视觉顺序，依赖和映射须显式编辑；运行模式显示 Run 冻结的历史定义，设计模式编辑当前项目草稿；Data Source Plugin 契约覆盖内部数据、媒体数据、Notion、Obsidian、API、SQL/Database，首个可执行适配器只读 Studio Source，未连接者明确不可执行；项目覆盖与显式另存角色默认版本是两个独立持久化动作；现有浏览器演示数据不自动导入后端。
- 依赖与启动：沿用现有 FastAPI/React/SQLAlchemy，无新增运行依赖。先在隔离开发库执行 `cd apps/api && .venv/bin/python -m alembic upgrade head`，再按下方命令启动；若本机 8000 端口已占用，可用 `AI_STUDIO_API_TARGET=http://127.0.0.1:<端口> npm run dev` 指向另一个本地 API。没有执行生产迁移或部署。

### FE-F3A 项目核心完成（本地归档）

- 需求背景：FE-F2 已使项目与生产工作台持久化，但 Brief、Evidence、Versions、Activity 仍是占位；FE-F3A 提案完成七标签的真实项目核心，不改变长期 PRD 和 FE-F2 工作流历史。
- 目录结构：已归档变更在 [`openspec/changes/archive/2026-09-27-fe-f3a-content-project-core-completion/`](openspec/changes/archive/2026-09-27-fe-f3a-content-project-core-completion/)；主规格在 [`openspec/specs/fe-f3a-content-project-core/spec.md`](openspec/specs/fe-f3a-content-project-core/spec.md)。`apps/api/app/routers/project_{evidence,assets,read_models}.py` 与 `apps/api/app/services/project_{brief,evidence,assets,events,versions,overview}.py` 提供后端核心，`apps/web/src/product/project/` 按标签拆分真实项目界面。用户原始包、ZIP 与合并稿保持原状。
- 已完成：五表增量迁移、项目事件与归档、追加式 Brief、Source 引用、冻结 Fact Boundary、显式 MaterialRevision 引用与工作流素材并集、Overview/Versions/Activity 派生读模型及七标签前端。隔离 SQLite 中已验证带 FE-F2 Run 历史的升级→回退→再升级；隔离浏览器完成项目、Brief 两版、Source、边界克隆/冻结、素材与七标签刷新。当前后端全套 296 passed、前端 build、OpenSpec strict 与 diff 检查通过。
- 待完成/TODO：FE-F3B Identity、FE-F4 Review、FE-F5 Opportunity/Learning、真实外部连接器及生产部署不在本切片范围；本次未推送、合并或执行生产迁移。
- 关键设计决策：复用现有 SourceDocument、冻结 FactPack、MaterialRevision 与 FE-F2 Run/Output，不另造平行资源库；项目引用不扩大全局资源权限，项目历史用归档而非物理删除保护，Overview/Versions 是后端派生读模型。新哈希素材上传若数据库回滚，字节候选写入 AuditLog，由已注册的定时 `retention_sweep` 在一日宽限后按批核实引用再清理；同哈希的写入与清理用文件锁协调，未处理候选不因普通审计日志过期而丢失。
- 依赖与启动：无新增运行依赖。沿用上节 FastAPI/React 启动方式；先在隔离开发库执行 `cd apps/api && .venv/bin/alembic upgrade head`，再启动 API 与前端。生产数据库未执行迁移。

### FE-F3B 内容身份（本地归档）

- PRD/需求背景：按 [`openspec/specs/fe-f3b-content-identity/spec.md`](openspec/specs/fe-f3b-content-identity/spec.md) 把品牌、角色、账号、栏目作为可修订的长期身份，并让新内容单元与运行固定实际身份快照；不自动回填旧运行，也不改变长期 PRD。实施记录归档于 [`openspec/changes/archive/2026-09-27-fe-f3b-content-identity/`](openspec/changes/archive/2026-09-27-fe-f3b-content-identity/)；另三份 FE-F0/F1、FE-F2、FE-F3A 主规格已同步。
- 目录结构：`apps/api/app/services/content_identity.py` 负责层级、修订和快照；`apps/api/app/routers/content_identities.py` 提供身份 API，`content_projects.py` 承接单元重绑和分层默认工作流；`apps/api/alembic/versions/f3b000000001_content_identity.py` 是增量迁移；`apps/web/src/product/IdentityWorkspace.tsx` 为真实身份工作区，项目与生产页读取冻结身份。
- 已完成：四级实体/修订、继承与显式清空、发布版 BrandVoice 引用、IdentitySnapshot、Run 精确固定、无历史原地重绑/有历史替换归档、栏目 > 账号 > 角色默认工作流、旧 API 所有权闸门、项目 Versions/Overview/Brief 集成和前端身份入口。隔离 SQLite 的 FE-F3A 历史行已验证升级→回退→再升级，旧 Run 校验和与 NULL 快照保持不变；隔离浏览器已验证四级创建/刷新、项目单元关联和生产 Context Header。独立二次复核通过；后端 310 项测试和前端构建通过。
- 待完成/TODO：真实外部账号与连接器不在本切片，Content Memory 只如实显示未实现；未推送/合并/部署或运行生产迁移。
- 关键设计决策：旧 brandless Persona 不伪造品牌或画像，旧 Unit/Run 不伪造快照；身份新修订不回写历史快照；默认工作流新版本不悄然改绑已有单元；项目 Run 的新旧 API 共用权限闸门，归档祖先不参与新生产。
- 依赖与启动方式：无新增运行依赖。仅对隔离开发库执行 `cd apps/api && .venv/bin/alembic upgrade head`，再按下方 FastAPI/Vite 命令启动；生产数据库迁移须另行决策。

### FE-F4 项目优先审核与分发（本地实现并归档）

- PRD/需求背景：[`openspec/specs/fe-f4-project-review-distribution/spec.md`](openspec/specs/fe-f4-project-review-distribution/spec.md) 定义 ContentProject → ContentUnit → Freeze Candidate → Content Approval → Delivery Authorization → Delivery；Review Center 是现有业务事实的投影，不新建平行审核状态表。
- 目录结构：实施记录归档于 [`openspec/changes/archive/2026-09-27-fe-f4-project-review-distribution/`](openspec/changes/archive/2026-09-27-fe-f4-project-review-distribution/)；另四份 FE-F0/F1、FE-F2、FE-F3A、FE-F3B 主规格已同步。`apps/api/app/services/project_review*.py`、`apps/api/app/routers/project_review.py` 承接 Candidate 与投影，`apps/api/app/services/delivery.py` 承接授权和本地成品包，`apps/web/src/product/ProjectReviewCenter.tsx` 是真实 `/review`；增量迁移是 `apps/api/alembic/versions/f4a000000001_project_review_distribution.py`。原始来源包不改动。
- 已完成：项目级 Draft 工作流输出可冻结 v3 Candidate，内容审批与交付授权独立；项目/单元/身份/事实边界/运行/检查/渲染/素材血缘进入冻结清单。`/review` 按项目展示当前候选、历史、检查、交付与对账，旧 `/review-publish` 保留。项目人工包和复制包经 v3 清单校验后包含真实媒体字节；旧裸 Candidate/Target 与项目稿件素材入口按项目所有者校验。隔离库升级→回退→升级、后端全量 318 项与前端构建已通过；独立代码复核已关闭发现的问题。五份规格已同步并归档。
- 待完成/TODO：五份主规格同步及全体 15 份主规格 strict 校验已完成；本地提交待执行，尚未推送、合并、部署或运行生产迁移。自动发布仍缺已验证账号/渠道映射；非 Draft 工作流输出缺可发布渲染适配器，冻结时明确阻断。前端主包超过 500 kB 仍为性能债，不能当作完整 PRD/V1 验收。
- 关键设计决策：复用 ContentAsset、Review、DeliveryTarget/Attempt/Receipt，不新增第二套 Review Center 状态表；只批准精确 Candidate ID/hash，历史候选只读且不能新授权。`unknown` 仅可经对账解除，不能用普通回执或自动重发绕过。项目身份和证据事实不由迁移伪造。
- 依赖与启动方式：无新增运行依赖；仅在隔离开发库可用 `cd apps/api && .venv/bin/alembic upgrade head` 验证，再按既有 FastAPI/Vite 命令启动。生产迁移须另行授权。

### FE-P1 前端首包性能（本地实现并归档）

- PRD/需求背景：FE-F4 基线只有一个 1,095.28 kB JS 文件（gzip 351.06 kB），旧页面与项目生产模块均被入口静态加载。本变更只调整前端加载边界，不改变产品、API 或持久化契约；长期规范见 [`openspec/specs/fe-p1-frontend-bundle-performance/spec.md`](openspec/specs/fe-p1-frontend-bundle-performance/spec.md)，实施记录见 [`openspec/changes/archive/2026-09-27-fe-p1-frontend-bundle-performance/`](openspec/changes/archive/2026-09-27-fe-p1-frontend-bundle-performance/)。
- 目录结构：`apps/web/src/App.tsx` 管理路由级 lazy、加载与失败恢复；`apps/web/src/product/Persistent{Projects,Project,Production}Page.tsx` 分别承载真实项目列表、详情、生产入口；`apps/web/src/product/project/projectTypes.ts` 保存仅类型依赖；`apps/web/vite.config.ts` 输出重型模块归属，`apps/web/scripts/check-bundle.mjs` 读取构建 manifest 并检查首包预算。变更的 design/spec/tasks 在上述 OpenSpec 目录。
- 已完成：按路由拆包并保留现有 URL、导航、数字项目与演示回退；`npm run build` 已输出 manifest 且预算检查通过。`/projects` 入口加静态闭包共 214.45 kB 原始 JS、69.98 kB gzip，较 FE-F4 基线原始 JS 减少 80.4%；全站生成 JS 共 1,138.41 kB，不能当作首包。隔离浏览器已核验直接访问、路由切换、加载提示、chunk 失败后的导航恢复；临时后端已核验项目→内容单元→保存覆盖→真实 Run→刷新回读。
- 待完成/TODO：Tab 深拆、手工 vendor 分包、缓存与分页未纳入首轮；尚未在真实网络环境测量用户体感时延，也未推送、合并或部署。
- 关键设计决策：预算依据 Vite manifest 的入口与 `/projects` 静态依赖闭包，阈值为原始 JS 低于 500,000 字节；gzip 与全站 JS 单独报告。TipTap/XYFlow 所在旧页面、项目详情与生产页不进入 `/projects` 初始图；Vite 警告消失本身不算验收。
- 依赖与启动方式：无新增运行依赖。`cd apps/web && npm run build` 同时执行 TypeScript、Vite manifest 构建和预算门禁；也可对已有构建运行 `npm run check:bundle`。本地开发仍用 `npm run dev` 与原有 API 代理。

### FE-F5A Home + Opportunity（已合入本地 main，六份主规格同步并归档）

- PRD/需求背景：补全生产前的“为什么现在做”决策层和日常工作台。Opportunity 不是 Topic；Home 是现有业务事实的 Projection。长期契约见 [Opportunity 主规格](openspec/specs/content-opportunities/spec.md) 与 [Home 主规格](openspec/specs/content-home-workspace/spec.md)，另四份 FE-F0/F1、FE-F3A、FE-F3B、FE-F4 主规格已同步。实施记录见 [FE-F5A 归档](openspec/changes/archive/2026-09-28-fe-f5a-home-opportunity/proposal.md)，完整步骤见 [实施计划](docs/superpowers/plans/2026-09-28-fe-f5a-home-opportunity.md)。
- 目录结构：`apps/api/app/routers/{opportunities,home}.py`、`services/{opportunities,home_projection,project_projection_context}.py`；四资源复用既有 models，增量迁移 `f5a000000001`；`apps/web/src/product/{OpportunityPages,HomePage}.tsx` 是独立 lazy 工作区，ProjectBriefTab 保留层级身份引用。
- 已完成：持久化 CRUD/triage/archive、引用式信号、append-only Assessment、版本冲突与 AuditLog、qualified 显式原子转换、项目来源回链；Home 全部自有项目批量扫描待决策、真实 ProjectEvent 活动与 identity readiness，不被最近20张卡片限制。信号解除引用不删除历史；unknown 不自动重发，分析不可用不会伪造结果。
- 验收：隔离 SQLite upgrade→downgrade→upgrade、346 后端测试、前端 TypeScript/Vite/build budget、OpenSpec all strict 18 项、定向 Ruff 和 diff-check 全部通过；真实浏览器创建机会→信号→评估→转换→刷新，以及带身份对象 Brief v1→v2 编辑/刷新通过。前后端独立复核 APPROVE。`/projects` 初始 JS 215.09 kB raw / 70.12 kB gzip，Home 231.11 kB、Opportunity 247.32 kB raw，均不含 TipTap/XYFlow。
- 待完成/TODO：OpenSpec 17/17 apply 任务完成，全部六份 delta 已同步并归档；功能提交 `3012fe5` 已合入本地 main，合入后 346 后端测试、前端 build/bundle、OpenSpec strict 18 项通过（归档后的校验见 progress.md）。未推送、部署或运行生产迁移，用户原始规格包保持未跟踪且未改动。PostgreSQL 并发和真实 LAN 部署未实测，真实 Connector、排期、自动分析、F5B/F5C 不在范围内。
- 关键设计决策：推荐始终是 suggested；转换只创建普通 Brief v1 与用户明确选择的 Source bindings，不创建 Topic / FactPack / Fact Boundary / IdentitySnapshot / Candidate / DeliveryTarget。Assessment 与 Conversion 保留历史；Home 不建立第二套状态表，近期活动不冒充排期。
- 依赖与启动方式：无新增运行依赖。隔离库先 `DATABASE_URL=sqlite:////tmp/<isolated>/studio.db python -m alembic upgrade head`，API 使用 uvicorn，Vite 通过 `AI_STUDIO_API_TARGET` 指向该 API；前端 `npm run build` 同时检查三个入口预算。全量 pytest 需指向已迁移隔离 DATABASE_URL，worker SessionLocal 不使用 TestClient 的内存依赖替换。本轮未运行生产迁移。

### FE-F6A Production Core / ContentMaster / Candidate v4（历史规格审计记录）

- PRD/需求背景：建立文字/图像/视频共用的不可变生产版本核心，不实现F6B/C/D专业编辑器；标准change已归档至 `openspec/changes/archive/2026-09-29-fe-f6a-production-core-content-master/`，计划在 `docs/superpowers/plans/2026-09-28-fe-f6a-production-core-content-master.md`。
- 目录结构：proposal/design/tasks及五份delta；新增production-content-master，完整更新FE-F2、FE-F3A、FE-F3B、FE-F4要求块。原始目录和ZIP不覆盖、不移动。
- 已完成：本地post-F5C基线main661e30a及code head f5c000000001核对，原稿审计与标准归位；补并发/幂等、固定身份、Master-only历史、render输入绑定、旧API/schema边界及安全回退。独立完整SPEC/plan复核APPROVE，strict24/24、diff-check及旧契约保留检查通过。
- 后续状态：用户已授权apply/定向回归，并提供post-F5C连接器实际读取证据；实施与规格归档均已完成，最终状态见下方F6A小节。此段仅保留历史规格审计记录。
- 关键设计决策：Master保存与Workflow保存分离；v4不伪造Draft；真实媒体存在不代表它渲染当前Master；身份层级变化不自动替换单元固定快照。
- 依赖与启动方式：复用现有技术栈，无新依赖；归档后的规格校验为 `openspec validate --all --strict`；历史实施与回归使用隔离环境，后续按用户授权在本地main完成，不发布。

### FE-F5C System Assets + Knowledge + Settings（已合入本地main，五份主规格已同步归档）

- PRD/需求背景：统一系统素材/知识展示和设置产品入口，不新增平行Asset或Registry真源；长期规范在 `openspec/specs/system-assets-knowledge/spec.md` 与 `openspec/specs/product-settings/spec.md`，并同步FE-F0/F1、FE-F2、FE-F3A三份主规格。实施记录归档于 `openspec/changes/archive/2026-09-28-fe-f5c-system-assets-knowledge-settings/`。
- 目录结构：services/system_library、library_usage、knowledge_collections、product_settings，KnowledgeCollection两表及f5c000000001迁移；前端product/SystemAssetsKnowledgePage五标签、ProductSettingsPage六分区，保留legacy入口。
- 已完成：标准规格95/95、引用式集合与项目精确资源复用、有界授权使用情况、安全设置投影及lazy工作区；547后端测试、构建/预算、strict22/22、独立SPEC/QUALITY、SQLite迁移往返与隔离浏览器验收通过。projects224.68kB raw/72.86kB gzip；Assets257.70kB、Settings229.76kB initial均无重型画布/编辑器。
- 待完成/TODO：功能提交 `7956273` 已快进合入本地main，合入后547测试、build/bundle、strict22/22、Ruff/diff门禁通过；五份canonical同步及change归档已完成，归档后全量strict23/23、规格保留核对和diff-check通过。原始包/ZIP保持不变；真实PostgreSQL并发、第三方Connector和生产准入未验收。
- 关键设计决策：库资源system_shared但使用情况遵循Project/Opportunity授权；Collection引用不成为Fact Boundary；Settings安全投影不新增Registry，断连不假成功。
- 依赖与启动方式：复用FastAPI/React与现有隔离API/Vite流程；业务验收迁移仅临时数据库，本轮归档不运行迁移。无push/deploy/生产迁移。

```text
系统资源 → 有界Library → 明确的项目引用 / Frozen FactPack事实边界
集合成员快照修订 → CAS写入 → 409时显式刷新；归档只读
固定MaterialRevision ID → 精确权限回读 → 撤销后禁止新增引用
Registry / 安全配置 → 六设置分区；危险旧库存仅admin显式进入
```

### FE-F5B Performance + Learning + Memory（已合入本地main，六份主规格已同步归档）

- PRD/需求背景：把已发布/外部历史内容的表现，经可追溯观察、Insight、学习候选和明确验证闭环到内容记忆；高表现不代表自动修改身份或策略。变更已归档至 `openspec/changes/archive/2026-09-28-fe-f5b-performance-learning-memory/`；新增主规格为 `openspec/specs/content-performance-history/` 和 `openspec/specs/content-learning-memory/`，同时更新产品入口、身份、审核交付与Home四份主规格。步骤见 `docs/superpowers/plans/2026-09-28-fe-f5b-performance-learning-memory.md`。
- 目录结构：七个资源沿用 `apps/api/app/models.py`，迁移 `f5b000000001`；历史与学习分为 `routers/{performance_history,learning}.py` 和 `services/{published_history,content_learning}.py`，前端独立 `product/LearningWorkspace.tsx` 与 Home/Identity 投影衔接。
- 已完成：七资源持久化、Receipt兼容回收、外部历史导入、同口径分析、Insight、候选验证、显式Memory晋升/版本、四标签Learning和Home/Identity投影。457后端测试、前端build/bundle、独立规格及质量复核、隔离浏览器闭环通过；完整证据见 `progress.md`。
- 待完成/TODO：功能提交 `9e0ce04` 已快进合入本地main，合入后457后端测试、前端build/bundle通过；六份delta同步归档完成，归档后strict21/21、要求保留检查与diff-check通过。PostgreSQL真实并发、真实指标Connector/模型分析器、生产迁移及部署未验收，不用本地测试代替生产准入。
- 关键设计决策：仅明确人工确认且血缘可核实的 Receipt 进入 Studio 历史；回执提交时间不是发布时间。外部导入有独立来源；指标按 namespace/key/unit/window/mode 保留口径，最新累计快照不相加；Memory 不等于 Identity，不自动改 Workflow/渠道策略。
- 依赖与启动方式：无新增运行依赖；隔离库执行 Alembic，API/Vite 使用上述启动方式。全量 pytest 指向已迁移隔离 DATABASE_URL；不得运行生产迁移、push、merge 或 deploy。

```text
Confirmed Receipt / External Import → PublishedContentRecord
  → PerformanceObservation → ContentInsight → LearningCandidate
  → 明确验证并冻结声明、范围及限制 → 显式Promote → ContentMemoryRevision
Home ← ready_for_review；Identity Memory ← 同一ContentMemory投影（不改身份修订）
```

```text
SourceDocument / DataSnapshot / Feedback / Manual reference
  → Opportunity → AssessmentRevision → 用户确认转换
  → ContentProject + Brief v1 + 选中 Source bindings + Origin Event
  → 明确建立 Fact Boundary → 既有 Identity / Production / Review / Delivery
Home ← Opportunity + Project Overview + Review decisions + ProjectEvent
```

### FE-F6B Text Production Studio（实现与本地验收完成 162/162，规格仍 active）

- 需求背景：基于已归档 F6A 的 Production Core，将文字最小 JSON 壳升级为专业结构化编辑；`text.master.v2` 的 Studio Document 是唯一可编辑真源，Markdown 只由服务端确定性生成。
- 目录结构：标准提案见 [F6B proposal](openspec/changes/fe-f6b-text-production-studio/proposal.md)，设计与实施计划在同目录；新增 Text spec，附 Production Core / Review / FE-P1 三份 delta。审计记录见 [F6B review](openspec/changes/fe-f6b-text-production-studio/review.md)。用户原始包及 ZIP 保留。
- 已完成：规格审计与归位、fresh 基线；新增 `services/text_documents.py` 实现十类 blocks、marks、Unicode/list/citation 定位、精确 refs 和确定性 Markdown；v2 append-only save / 读回 / 幂等 / context-CAS 接通，持久化 schema 分派覆盖 readiness/checks/Candidate/package，v1/Graphic/Video 兼容回归通过。普通保存拒绝 schema 跨越；新 Studio Document 默认 v2，旧 Markdown/文档调用保持 v1。
- 本批已完成：唯一 legacy Text converter 供升级和 Draft seed 共用；显式升级预览/提交保留旧 v1，验证最新非 stale 父版本与 payload/context CAS，并先幂等回放；新 seed 输出 v2，保留原 Run/Step/Attempt 血缘、exact refs 与未映射警告。矛盾的旧 document 不覆盖 Markdown，不能证明等价的语法保留字面内容并告警。
- Backend Milestone A：共用检查要求解析按 v2 精确 schema、adapter、renderer、实现、profile 与模型使用权限计算每类输入哈希；v1 继续沿用原检查语义。结构、事实、固定身份、精确渠道以及条件性可发现性检查已落 `ContentMasterCheckRun`；模型未配置或禁用证据时不假称语义通过，空白身份也不假称已验证，默认老 SEO profile 未覆盖字段显示 partial warning 并留给审批人工处置。新增 profile 只使对应检查过期，历史授权包仍按冻结要求校验，同输入的新 blocker 会阻断。本批最终后端 892 passed / 2 skipped，strict 与 Ruff 通过。
- Backend Milestone B：项目内五种文字 AI 建议只返回服务端验证过的 patch 和 LLMRun receipt，不写 Master；显式保存验证连续 hash 血缘，拒绝客户端伪造。结构化版本 diff、v2 精确引文/证据冻结、不可变 Review 预览与无 Draft 的本地 ZIP 闭环已通过后端回归；冻结正文篡改会拒绝展示，被改写的引文会明确失效，未受影响的引文及证据 locator 会重定位。全量后端 913 passed / 2 skipped，OpenSpec strict 25/25、Ruff、diff-check 均通过。
- Frontend milestone：Text-only lazy TipTap、结构化 blocks/marks、精确素材/证据引用、AI 建议本地接受、固定身份与检查面板、v1 升级及 revision diff 已接入；15–20 共 38 项完成。隔离浏览器已核 v2 保存回读、AI receipt 修订、双窗口 409、历史只读及缺上下文时不可冻结。最新前端构建、FE-P1 与全后端 913 passed / 2 skipped 通过，具体包体和验收范围见 `progress.md`。
- 最终浏览器与回归：隔离项目已完成真实素材和冻结 FactPack 精确引用、边界漂移、五种 AI 建议、显式 v1 升级、验证过的 Draft seed、结构化差异，以及百家号 article Text v2 → Candidate v4 → Review/Approval → 本地 ZIP；ZIP 正文与素材哈希和冻结清单一致。微信 article 缺精确 `cover` 角色时仍被 Registry 正确阻断，不用 inline 图片冒充封面。legacy `/workspace`、Graphic/Video 最小壳与归档只读、动态模块失败后重试恢复均已验收；F6A/F6B 三形态定向回归 130 passed。完整证据和包体数据见 `progress.md`。
- 待完成/TODO：实现任务 162/162、独立 SPEC/后端/前端复核均通过，格式按钮无障碍缺口已在浏览器核验。最终新跑全后端 913 passed / 2 skipped、构建/FE-P1、OpenSpec strict 25/25、相关 Ruff 与 diff-check；零新 migration。本地 main 提交后仍须另行授权 canonical 同步/归档；不推送、部署或运行生产迁移，不启动 F6C/F6D。
- 关键设计决策：显式 v1→v2 upgrade；Workflow 与 Master 保存独立；AI 仅建议→预览→明确接受到本地→明确保存，服务端验证 output match，不冒充点击或全篇 AI 作者证明；warnings 在 Approval 处置而非 Freeze 前。目标零新表/零迁移，若实际需要持久化扩展必须停止修订。
- 依赖与启动：继续复用现有 Master/refs/checks/LLMRun 和已有 TipTap；无新增依赖、表或 migration，现有服务启动方式不变。测试使用独立临时 SQLite；阶段门禁和未完成边界见 `progress.md`，不把基础测试当作完整 F6B/browser 验收。

```text
持久化 payload_schema
├─ text.master.v1 → 既有 Markdown / legacy 流程不变
│                   → 显式升级预览 + 当前父版本/CAS/幂等 → v2 新 revision（不改历史）
├─ verified Draft WorkflowOutput → 同一 converter + exact refs / warnings → v2 seed
└─ text.master.v2 → Studio Document + exact refs → append-only Master
                  → 确定性 Markdown / schema-aware projection
                  → 专业 checks + 每类 currentness（Backend A 已通过）
                  → warning 可冻结、审批须按检查 ID/输入哈希处置
```

### FE-F6D Video Production Studio（标准 OpenSpec apply 进行中）

- PRD/需求背景：North Star 要求 Video 从 F6A 的 `video.master.v1` JSON 壳升级为可追溯的脚本、镜头、时间线、字幕、配音与最终视频生产体验；F6C 独立复核和 F6D 规格审阅已通过，F6D 正按标准 change 实施。
- 目录结构：`openspec/changes/fe-f6d-video-production-studio/` 已有 proposal、design、tasks 和 Video Studio、Production Core、Review、FE-P1 四份 delta；用户总包源文件保持原样。
- 已完成：标准 OpenSpec 与独立 SPEC review；Video v2 canonical 文档、精确媒体位置/权利、published profile、显式 v1→v2 追加式升级、专业 CheckRun 与 profile/source/context 新鲜度。Project-scoped Master diff 和冻结 Candidate Review 按稳定 ID 对比，不计算整片文字相似度。已用无 Draft/Topic/Mother 的手工 Video v2 Master 实际跑通手工输入绑定 MP4、checks、Candidate v4、Review、Approval、Delivery Authorization 与本地 ZIP；撤权/字节篡改/候选篡改及新 Master 后旧授权均拒绝。专用 Video v2 派生 API 以具体用户编辑结果创建长转短/画幅转换/镜头替换子修订，来源 hash/context/head/幂等指纹和服务端 `derived_video` 血缘已验证。项目级 Video/TTS/ASR 能力状态及请求入口均诚实显示未验证、不可执行且无写入。手工成片的伪造 renderer、wrong-kind、缺字节及 hash 不符均被阻断；v4 本地 ZIP 固定条目元数据，跨不同时钟重复构建字节一致。正常 Video 编辑已从 raw JSON 改为 Video-only lazy typed v2 草稿，含稳定脚本/镜头、精确项目素材、轨道/片段、配音、字幕/SRT、叠字与最终 MP4。隔离浏览器已验证保存/刷新、409、v1 显式升级、稳定差异、派生子修订历史、真实成片检查→Candidate→Review→审批→本地 ZIP、撤权后打包阻断和归档只读。当前实施 77/79，零新表/迁移。
- 待完成/TODO：F6D 4.5 已核销为“真实 Provider/许可/血缘/脱敏义务移交 F7”，不代表 F7 实现或验证；独立实施复核已于 `main@a51efe0` 给出 APPROVE，8.4 已关闭，F6D 为 79/79。隔离浏览器与全量门禁证据见 `docs/FE_F6D_ISOLATED_ACCEPTANCE.md`；独立复核未重跑原始测试命令。本地包不等于远端发布。主规格同步/归档须单独授权。
- 独立复核补丁：`main@364a49a` 的外部复核指出 Review 漏显冻结 Video v2 结构、跨轨道重复媒体槽位可保存、非法枚举类型可抛出 TypeError；现已定向修复并新增 API/隔离浏览器回归。记录中的本地门禁为 1026 passed / 2 skipped、前端构建/FE-P1、OpenSpec strict 30/30、隔离浏览器 12 项通过。修复后独立复核已 APPROVE，未重新运行这些命令。
- 关键设计决策：`video.master.v2` 是唯一可编辑真源；派生剪辑只有在存在明确编辑或确定性本地变换产生的有效 v2 内容时才生成追加式子修订，不能只记转换意图或把未验证 Provider 当成功。现有 MaterialRevision/ContentMasterRevision/Candidate v4 继续是真源。未验证 Video/TTS/ASR 不制造成功或公开使用权，真实 Provider 接收归 F7。
- 本批目录：`apps/api/app/services/video_documents.py` 保存 Video v2 canonical 文档与精确 profile 规则，`content_harness/channel_registry.py` 提供 published `video_requirements` 投影；`video_derivations.py` 实现专用派生 API 的服务端血缘/来源闸门，`video_master_checks.py` 复用既有 Master CheckRun，`video_master_diff.py` 提供 v2 稳定 ID 差异，`production_modalities.py` 与 `project_review_projection.py` 承接冻结输入哈希和 Review 完整性闸门；`apps/api/app/routers/project_assets.py` 暴露不可用的项目级 Video/TTS/ASR 能力，`apps/api/tests/test_f6d_video_{documents,capabilities}.py` 验证边界。`apps/web/src/product/VideoStudioModel.ts` 和 `VideoStudioShell.tsx` 承接 Video-only 类型化草稿，`apps/web/scripts/check-bundle.mjs` 验证按需加载。没有新增表或依赖。
- 依赖与启动：沿用本 README 现有 API/Vite 启动方式，目标零新表/零迁移；隔离验收 API 须同时指定临时 `DATABASE_URL` 和绝对路径 `AI_STUDIO_MEDIA_ROOT`（与临时数据库同一父目录下的 `media`），浏览器脚本校验二者并核对实际字节。若实施证明需新持久化结构，应先暂停修订规格，不直接建表。不 push/deploy/运行生产迁移。

### FE-F6E Channel Variants + Content Matrix（独立规格复核通过，backend-first apply 进行中）

- PRD/需求背景：North Star 要求在可复用 ContentMaster 与审批候选之间形成真正的渠道适配层；原先缺少持久 ChannelVariant，Project Matrix 只能直接管理 ContentUnit。F6D 门禁与 F6E 独立规格复核已通过，F6E 正按标准 change 做 backend-first 实施。
- 目录结构：`openspec/changes/fe-f6e-channel-variants-content-matrix/` 包含 proposal、design、tasks、新 ChannelVariant 规格及 Matrix、Production Core、Project 读模型、Review、FE-P1 五份 delta；`apps/api/app/models.py` 与 `apps/api/alembic/versions/f6e000000001_channel_variants.py` 承接四表及 Candidate 链接，`apps/api/app/services/channel_adapters.py` 和 `channel_variant_documents.py` 承接 Profile 能力边界与五种 canonical payload，`apps/api/app/services/channel_variants.py` 与 `apps/api/app/routers/channel_variants.py` 承接项目级历史读取、非持久化适配预览、Variant 写入和检查。用户原总包不改。
- 已完成：规格界定非写入 Matrix 建议、追加式 Variant/精确引用/检查、Candidate v5、Review/Approval/本地包分派与旧 v3/v4 保留；已标记 superseded 的 V1 交付变更只作为七个历史场景和 PRD §15/§16 的保留验收来源，不重新激活、不冒充已验收。2026-09-29 独立 SPEC 反馈后补定五个边界：版本化 canonical Variant payload、首批 v2 Master→form/`artifact_kind` 兼容矩阵、v5 唯一 Variant source pointer 与缓存投影列校验、复用成功 `LLMRun` 的安全血缘，以及 superseded 状态。旧 `x_thread/thread` 保持 v3/v4 行为但不作为 v5 目标。v5 跨渠道授权比较冻结 Variant 目标而非来源 Unit 渠道，仍保留身份/账号约束。已完成 F6E 0.3/0.4 基线与旧 V1 验收义务映射（见 `findings.md`），未将其视为功能验收。首批计划内加法模型和迁移已落地，含四个 Variant 表、Candidate nullable 链接及精确 published Profile 版本 FK；SQLite/临时 PostgreSQL 迁移门禁已通过。公众号文章、X 推串与单条已有保守的 Text v2 确定性适配器；公众号文章可显式选择或继承项目可见的精确封面引用，X 仍限无素材子集；小红书图文仅对 F6C 已验证真实最终 render 开放；项目级 Variant 历史、适配预览、追加式保存及精确 Fact Boundary citation 已接通。
- 第二轮 SPEC 反馈补充：v5 Candidate 当前性按稳定 `(unit_id, variant_key)` 系列判断，不由整个 Unit 最大 Candidate ID 决定；三渠道预先冻结后可任意顺序审批/授权，同系列新版本仅替代本系列，真实 Master/context/profile/rights/check 漂移仍阻断，v3/v4 保持原闸门。已写入 design/tasks 与三份相关 delta，独立 SPEC re-review 已通过。
- 第三轮 SPEC 窄修：v5 `ContentAsset` 仅 `channel_variant_revision_id` 为来源 FK；既有 `draft_id`、`topic_brief_id`、`mother_revision_id`、`content_master_revision_id`、`workflow_run_id` 均须为空。工作流血缘从 Variant→精确 source Master→冻结 manifest 读取，不用 Candidate 运行 FK 参与分派/当前性；Review/Approval/Authorization/Package 遇污染字段须拒绝。独立 SPEC re-review 于 `main@6f5e022` 给出 APPROVE。
- Variant 检查进度：项目级 `/channel-variants/{id}/checks` 可追加结构、精确 Profile/rule、证据引用、实时素材权利结果；小红书另有真实 render 检查。同系列新版本、源 Master、Profile/Adapter/rule、精确证据或 Graphic/Video 素材/render 漂移时，历史结果只读投影为 stale。公众号缺必需封面阻断，未知规则/未证实语义保持 incomplete，远端能力仍未验证；完整 byte-exact 本地包检查尚未接入，`variant_package` 始终 incomplete，因此整体不宣称可冻结。
- 待完成/TODO：F6C 74/74、F6D 79/79 及独立复核已核对，F6E 0.1/0.2 前置与独立规格任务完成；小红书 Graphic v2 图文适配已要求逐画布真实 render/素材精确版本/公开权利。抖音 Video v2→口播脚本现支持 `shot_source` B-roll 精确素材映射和标明估算的 SRT，仍不是成片；无法证明的音轨/真实字幕/叠字不转换。来源证据、完整 Variant 检查、v5、UI、浏览器和最终门禁仍待完成。三个 Text Adapter 只处理无引用的可完整保留子集；复杂源稿会明确拒绝，不应在 UI 上显示为完整适配成功。不得将本地人工包当作真实远端发布。
- 关键设计决策：无渠道 Master 是显式 source-only 路径；Matrix 选择不会在 Candidate Approval 前创建 DeliveryTarget；渠道适配在 Candidate v5 冻结前完成，Publisher 不改已批准内容，未知交付仍须对账。ContentAccount 自由格式 profile 不证明目标平台所有权；本地包仍须校验账号活动/归属/单元绑定和冻结目标，但只能标为人工交付，远端动作须后续 F7 精确验证。
- 依赖与启动：沿用当前 FastAPI、React、Alembic；F6E 加法迁移 `f6e000000001` 已在代码中，未执行生产迁移。无 push/deploy/canonical 同步或归档授权。

### FE-F7 Capability Integrations + Delivery（仅标准 OpenSpec 草案，未 apply）

- PRD/需求背景：North Star 要求 Model/Tool/Data/Search/Image/Video/TTS/ASR/Renderer/Publisher 成为可替换且可验证的真实能力；注册或配置存在不等于可执行，更不等于特定账号的远端动作已验证。
- 目录结构：[`openspec/changes/fe-f7-capability-integrations-delivery/`](openspec/changes/fe-f7-capability-integrations-delivery/proposal.md) 含 proposal、design、105 项任务，以及新增 Capability 规格和 FE-F2/System Assets/Settings/FE-F4 四份 delta；用户总包源稿保持原样。未来实施复用 `apps/api/app/services/content_harness/registry.py`、`data_source_plugins.py`、`connector_service.py`、`materials.py` 与 `delivery.py`，不重造其真源。
- 已完成：审计原 F7 十条要求及当前 registry/Connector/Material/Delivery/Settings 路径，补 exact-scoped verification、Provider 响应/错误/审计脱敏、媒体字节和许可验证、项目精确引用、未验证 legacy auto-draft 不得绕过远端闸门；进一步把现有 MaterialRevision 的 prompt/URL/metadata 与 ConnectorEndpoint 失败原因纳入安全投影契约，避免原始请求、签名链接或异常文本借既有字段泄漏。只完成规格归位，未改业务代码或迁移。
- 规格预校准：F7 任务中“保存来源 URL”现明确仅允许经过正向验证的稳定公开引用地址；签名、带凭据或过期抓取/预览地址不能落入 `MaterialRevision.source_url`、元数据、审计或 API。无法证明引用地址安全时保留有界来源标识与单向哈希。此项只更新 active OpenSpec，不宣称 F7 实施或独立 SPEC review 已通过。
- 待完成/TODO：F6C 已完成；F6D/F6E 实施验收后，再对 F7 做独立 SPEC review 与 apply 确认；实际 Provider 适配、隔离迁移、浏览器与真实账号验收均未开始，缺凭据则保持 unverified。
- 关键设计决策：复用现有 DeliveryTarget/Attempt/Receipt 和 MaterialRevision；Provider 响应仅是不可信候选，用户显式接受并通过字节、来源、许可和权利检查后才可入库；Publisher 消费已批准冻结成品，不临发布时改内容；unknown 必须对账。关闭旧 `allow_unverified_auto_draft` 对新远端效果的绕过是明示的兼容性行为变化，历史可读。
- 依赖与启动：沿用当前 API/Vite 启动方式。规格预计仅为 CapabilityRegistration/CapabilityVerification 加可逆迁移，实际实现前复核当前 migration head；不 push/deploy/运行生产迁移，不同步 canonical 或归档。

### FE-F8 Production Readiness + Operations（仅标准 OpenSpec 草案，未 apply）

- PRD/需求背景：North Star 的完整产品链路还需生产安全认证、可替换字节存储、真实运行健康状态、恢复演练及 Golden/全链路验收；F8 是部署前的工程收口，不增加 Organization/Invite/Tenant/SSO 产品管理。
- 目录结构：[`openspec/changes/fe-f8-production-readiness-operations/`](openspec/changes/fe-f8-production-readiness-operations/proposal.md) 含 proposal/design、100 项任务（增加身份映射前置审定）、新 Production Readiness 规格与 Product Settings delta；未来实施以现有 `apps/api/app/deps.py`、`main.py`、`observability.py`、`routers/health.py`、`services/materials.py` 与 worker、Settings 为基线。用户原始包不改。
- 已完成：规格校准了原十条目标，补生产 Header/default-user 拒绝、启动只读预检、健康状态真实 HTTP 失败、metrics 有界标签、全媒体读写者存储切换、存量明文 Secret 处理和实际平台验证边界；仅规格，未修改生产代码或数据库。
- 规格预审补丁：现有 User 只有 email/role/status，没有外部 issuer/subject 绑定；F8 明确生产身份不能仅凭 token email/role 猜测映射，须在实施前审定稳定 subject→现有 User 的安全绑定，若需新持久结构先修订规格。完整链路验收也明确：本地 ZIP/人工交付不能直接制造 PublishedContentRecord 或 Learning；须另有符合 F5B 的 `human_confirmed` Receipt 与 `delivered_at`。本批未实施 F8、未改变现有开发认证。
- 待完成/TODO：F6C 独立复核已完成；F6D/F6E/F7 的实施和验收，以及 F8 独立 SPEC review/apply 确认均未完成；生产身份签发方、Secret Provider、对象存储和真实账号未配置或验证，不能称生产就绪。
- 关键设计决策：复用现有 User/Role、MaterialRevision、Run/Attempt/Review/Receipt 真源；生产禁用开发 Header 与自动建号，不在应用启动时迁移；存储切换前验完整引用字节并保留可恢复回退；Golden 质量与真实发布按证据分别验收。
- 依赖与启动：规格预计不新增长期业务表；实际生产启动/迁移/部署须有独立授权和运行手册。本轮不 push/deploy/运行生产迁移或同步 canonical/归档。

### FE-F6C Graphic Production Studio（本地实施 74/74；待主规格同步与归档授权）

- PRD/需求背景：North Star 的图文生产不是图片附件；F6A 仅有 `graphic.master.v1` JSON 壳。标准提案在 [`openspec/changes/fe-f6c-graphic-production-studio/proposal.md`](openspec/changes/fe-f6c-graphic-production-studio/proposal.md)，完整实施计划在 [`docs/superpowers/plans/2026-09-29-fe-f6c-graphic-production-studio.md`](docs/superpowers/plans/2026-09-29-fe-f6c-graphic-production-studio.md)。用户原始总包保持原样。
- 目录结构：标准 change 包含 proposal/design/tasks、Graphic 新规格以及 Production Core、Review、前端性能三份 delta；后端 `apps/api/app/services/graphic_documents.py`、`graphic_master_checks.py`、`graphic_master_diff.py` 复用现有 Master/Ref/Check/Candidate 链，前端 `apps/web/src/product/GraphicStudioModel.ts` 与 `GraphicStudioShell.tsx` 按 Graphic 路径加载，`apps/web/scripts/check-bundle.mjs` 核查静态依赖边界。
- 已完成：按 `main@670dd49` 校准 F6C 的 77 项可验证任务和 Scenario。`graphic.master.v2` canonical 文档/adapter、精确图层素材与证据 locator、按画布顺序的真实手工 render、v1→v2 显式 fork 均已实现；旧无 schema Graphic 保留 v1。exact image profile 规则和四类专业检查已接入；语义/视觉不足仅 warning。Graphic-only UI 已有画布增删复制重排、可缩放/选择的阶段预览、图层几何/样式/裁剪/形状/锁定、exact 共享素材插入/替换、文字证据绑定、每画布最终图片绑定、published Profile preset、显式保存与历史升级/差异。前 12 个可见媒体层经鉴权和 SHA256 校验才预览。隔离 SQLite 与真实浏览器已完成两画布保存/刷新、Brief/事实边界变化使旧 Master stale、精确证据绑定、手工渲染确认、八项检查、Candidate v4、冻结双图预览、警告处置、审批与本地包授权；ZIP 双图顺序/哈希与冻结清单一致，未回填发布。归档单元的 Graphic 输入/保存/检查/冻结均只读；第二单元的并发写入后，旧页面保存显示 409 且本地编辑未冒充落库。重复素材兼任图层/最终渲染时的 ZIP 重名已按失败回归修复；新旧 Candidate 回读与结构化差异保留各自冻结文字和检查哈希，Review 检查名称不再丢失。全后端在排除本机无效 `NO_PROXY/no_proxy` 后为 951 passed/2 skipped；相关定向 97 passed，前端模型 20/20、TypeScript/Vite/FE-P1、OpenSpec strict 26/26、相关 Ruff 与 diff-check PASS。
- 待完成/TODO：独立复核已在 ChatGPT 实际读取 `main@2891bac` 后给出 SPEC 与前端 APPROVE；后端前轮 APPROVE 继续有效（未改后端业务代码），任务 74/74。本轮全后端新跑 951 passed/2 skipped，前端构建/FE-P1、OpenSpec strict 30/30、F6C 相关 Ruff 通过；额外全库 Ruff 有 23 个既有问题，不属于本切片完成声明。原 F6C 真实 Provider 接收/许可/血缘要求明确移交 F7，执行/结果响应脱敏及负向测试已进入 F7 active 规格但业务能力尚未实现。项目接口和 Graphic 工作台仍诚实显示未验证自动渲染不可执行；人工图片确认不代表已验证 Renderer 或视觉语义。不能把 F6C 通过等同整个 North Star 完成。主规格同步/归档另需授权，不 push/deploy/生产迁移。
- 关键设计决策：旧 Graphic v1 显式 Fork；画布顺序与输出一一对应；未验证 Renderer/Search/Image 不冒充可用；GraphicStudioModel 仅在 Graphic 工作区动态加载，通用 Production/Text/Video 静态闭包由构建门禁隔离；小红书旧 `image_note` 当前是 text-classified，F6C 不暗中改类，跨渠道适配由 F6E 承接。
- 依赖与启动：沿用现有 FastAPI/React、MaterialRevision 与生产工作台；目标零新表/零迁移。使用本 README 既有 API/Vite 启动方式，先在隔离数据库做验收。

### FE-F6A Production Core（本地验收完成，五份主规格同步并归档）

- 需求背景：在现有 Workflow/Run、Candidate v3、Review 与 Delivery 链路上增加不可变 `ContentMasterRevision`，让文字、图文、视频共用明确的主版本和上下文血缘；不替换旧引擎，不新增远程发布能力。
- 目录结构：后端 `services/content_masters.py`、`production_modalities.py`、`candidates_v4.py`、`production_validation.py`、`production_packages.py` 承接保存、适配、冻结、live gate 与本地包；既有 Review/Outputs/Overview/Versions 接入 Master。前端 `ProductionWorkspace` 拆分 Header/Canvas/Inspector/AssetDrawer/MasterPanel 和三个 lazy StudioShell；迁移为 `f6a000000001`。
- 已完成：214/214。手工 Text（无 Draft/Topic/Mother/Run）→ checks → Candidate v4 → exact-hash Approval → Delivery Authorization → ZIP；Graphic/Video 经真实文件及精确输入的人工 render attestation 走同一闭环。上下文/CAS/幂等、live rights/evidence/checks、跨 Unit 项目素材、输出血缘、三形态 Review、Master Versions/Overview、历史只读和 Workflow debugger 均已验收。
- 验收：后端 753 passed（206 项 F6A，6 项既有 warnings）；TypeScript/Vite、FE-P1、strict24/24、Ruff/diff 通过。隔离 SQLite 与真实 PostgreSQL16 up/down/up 通过；浏览器 20.1–20.14 和三项独立 review 全部通过。/projects 224.68 kB raw / 72.86 gzip，Production 254.44 / 82.27；无 TipTap/XYFlow 首包泄漏。完整证据与边界见 [FE_F6A_FINAL_ACCEPTANCE.md](docs/FE_F6A_FINAL_ACCEPTANCE.md)。
- 关键设计决策：Workflow/Master dirty 与保存独立；冻结历史不自动跟随身份/Brief/Boundary；新审批/授权要求 current Master，已有授权只交付原冻结历史且仍受撤权/字节/检查 gate；v4 失败不回退。图文、视频不计算假文本相似度；最小壳不冒充专业编辑器。
- 规格收尾：2026-09-29获单独授权后，新增 [Production Core主规格](openspec/specs/production-content-master/spec.md)，更新FE-F2/F3A/F3B/F4四份主规格；实施记录归档至 [F6A归档](openspec/changes/archive/2026-09-29-fe-f6a-production-core-content-master/proposal.md)。29个delta要求块准确同步，40条旧要求/149个旧场景保留，原始包及9份归档文件未改。
- 待完成/TODO：F6A已完成规格生命周期收尾；F6B及以后不执行，须先有具体方案并确认。仅本地提交，未push/deploy/生产迁移；不把本地验收当作生产就绪。
- 依赖与启动：复用现有 FastAPI/SQLAlchemy/Alembic/React，无新增运行依赖；启动沿用下方命令。迁移与验收只在新临时数据库执行，禁止用于未授权开发/生产库。AI Workflow 浏览器验收使用显式 mock provider，不代表真实外部服务验收。
- 开发方式：按用户授权直接在本地 main 实施和提交；不因单 Agent 跳过规格、回归与独立只读评审。

### 下一版规划：文章/图文全渠道

> **2026-09-24 更新（V1 PRD 2.0 Content Harness 已实施）**：下一段提到的 `complete-prd-v1-channel-deliverables` 已标记 **superseded**，被主变更 [`align-v1-prd2-content-harness`](openspec/changes/align-v1-prd2-content-harness/proposal.md) 吸收并实施。当前代码已落地：Channel Registry（14 平台 profile，新增渠道无需改枚举/迁移）、Workflow 版本化 + Node Plugin Registry、Material Library（素材全局复用/权利链）、DraftCheckRun 统一检查、Discoverability（Pre/Post SEO）、Candidate Manifest schema v2、Delivery Router（copy_package / assisted_draft / auto_draft + DeliveryAttempt：prepared→远端→结果，unknown 不自动重发）、节点级 Rerun/Stale、Review & Publish Center（`/review-publish`）。真实账号自动发布仍未验证，平台能力一律如实标注 unverified；PRD §15–16 与 30 Topic 门槛仍需单独验收。实施与偏差记录见该 change 的 `design.md`。

已标记 superseded 的 [`complete-prd-v1-channel-deliverables`](openspec/changes/complete-prd-v1-channel-deliverables/proposal.md) 保留七个历史场景及 PRD §15–16 验收义务，不作为当前 active 实施 change，也不能因 F6E 本地包通过就推定完整 V1 已验收；§3.1 的全渠道验收仍需单独完成。

最新产品蓝图与本地代码的对齐讨论见 [V1 对齐方案](docs/AI_CONTENT_STUDIO_V1_ALIGNMENT_PLAN.md)，核对依据见 [findings.md](findings.md)。旧三渠道澄清稿仅作历史背景；最新目标是三产品矩阵中的文章/图文内容中心，视频属于 V2。

- 已完成：按确认的 M1 OpenSpec 实现并本地验收了母稿、不可变证据、完整候选审批、公众号/X Thread 人工交付与反馈闭环。
- 待完成：真实账号的人工发布验收；后续全渠道适配和自动分发必须另开变更，不以本地交付包代替平台发布。
- 关键决策：复用 FastAPI/React/Celery 和现有事实/审核链；建议首批打通已有文章的公众号 + X 线程成品、人工交付回执及反馈，再补全文章/图文 V1。成品覆盖与自动分发能力分别验收，不以导出冒充已发布。
- 注意：M1 仅覆盖人工交付；公众号自动进入草稿箱、X API 发布、排期与自动重试均未启用。

本轮新增的 M1 路径不改变运行依赖或启动方式；已归档规范见 `openspec/changes/archive/2026-09-22-add-evidence-bound-article-handoff/`。

### M1 当前落地状态

- 已有文章可导入不可覆盖的 `MotherRevision`，并生成公众号 / X Thread 的本地适配稿；冻结证据以类型化快照而非可变 Fact 作为 M1 依据。
- 候选批准同时冻结标题、正文、X 帖子顺序、素材顺序、引用、声明和检查结果；素材、证据公开权限撤销会停止未完成的交付目标。
- 每个账号的人工交付目标独立授权、幂等创建。ZIP 成品包包含正文、HTML 或 Thread JSON、清单和经哈希校验的实际公开素材；回填 `human_confirmed` 只表示人工确认，不表示平台已发布。
- M1 不调用公众号、X 或对象存储接口；目标授权只允许授权操作人下载包或回填结果。
- 旧工作流的公众号远端草稿节点默认不生成；只有显式遗留配置才会保留该节点，且 M1 母稿资产仍会被服务端拒绝。
- 迁移执行：`cd apps/api && .venv/bin/python -m alembic upgrade head`。
- 本地验收已覆盖公众号实际封面 ZIP、X Thread、重复目标、账号隔离、目标独立失败/成功、旧证据阻断、终态不回退和权限撤销；OpenSpec 已在 ChatGPT 最终复核通过后归档。

### 当前实现链路

```text
Source → Fact → FactPack(类型化冻结) → Topic Brief → MotherRevision
       → 公众号 / X Thread Draft + DraftMedia → FactCheck → Review(候选哈希)
       → Asset → DeliveryTarget(账号授权) → ZIP 成品包 → 人工回填 / 反馈
```

核心不变量（"事实不可漂移"主干，全部有测试覆盖）：

- FactPack 冻结后不可变，修改必须 Clone vN+1
- Topic 只能绑定 frozen FactPack
- 模型输出的 fact_id 必须属于当前 FactPack，服务端校验
- Deterministic Checker：无 Fact 支持的数字 → blocker；blocker 未解决不能 approve（HTTP 409）
- 重新生成 / 人工保存产生新 revision，旧 Draft 永不覆盖
- 已生成内容永远记录生成时的 FactPack 版本与 checksum

## 快速启动

### Codex with ChatGPT 连接

- 当前工作区已绑定 ChatGPT 项目「AIContentStudio」，使用「仅限项目记忆」。
- 连接器名称：`Codex with ChatGPT · AIContentStudio`。
- 更换 ChatGPT 账号后，需要重新授权同名连接器，并重新完成工作区读取验证。
- 2026-09-27 连接故障记录：四项独立读取均返回 `internal error`；重启此工作区的安全连接后，HTTP/2 与健康连接数正常，公开 MCP 未授权探测返回 401。待 ChatGPT 端重试 `workspace_info` 完成端到端确认。
- 2026-09-27 后续复查：用户再次报告疑似断开，但公开连通性、HTTP/2、健康连接数仍通过，因此未重复重启；ChatGPT 端仍需 `workspace_info` 实测确认。

```bash
# 后端（默认 SQLite，零外部依赖；Mock provider，无需 API Key）
cd apps/api
python3 -m venv .venv && . .venv/bin/activate
pip install -e . pytest ruff
python -m app.seed                 # 建表 + 种子（4 用户 / 3 渠道模板 / Brand Voice / Prompt）
python -m uvicorn app.main:app --reload --port 8000

# 前端
cd apps/web
npm install && npm run dev         # http://localhost:5173（/api 代理到 8000）
```

或使用根目录 `Makefile`（`make seed` / `make dev` / `make dev-web` / `make worker` / `make test` / `make lint` / `make backup`）。

> 本机代理若为 fake-ip 模式（Clash 等），在 `.env` 设 `SSRF_ALLOW_PRIVATE=true`，否则 URL 抓取/Connector 全部会被 SSRF 防护拦截。生产必须保持 false。

生产部署（docker compose 全栈）：`docker compose up -d --build` 一键起 postgres / redis / minio /
api / web / worker / beat。标准流程：先 `up -d postgres redis minio minio-init`，等 postgres 健康，
宿主机 `DATABASE_URL=postgresql+psycopg://studio:studio@localhost:15432/content_studio make migrate`
（再跑 `python -m app.seed` 做幂等种子），最后 `up -d --build` 其余服务。
访问入口：Web `http://localhost:8088`（nginx 托管 + /api 反代），API `http://localhost:8000`。
入口服务（api 8000 / web 8088）绑定 0.0.0.0 对局域网开放；存储类端口绑定 127.0.0.1
（PG 15432 / Redis 16379 / MinIO 19000、19001），不对局域网暴露；容器内服务互通走 compose 内网。
注意：开发模式身份来自可伪造的 `X-Studio-User` header，局域网开放即局域网内任何人可冒充
admin，正式对外部署须改回 127.0.0.1 并接入真实鉴权。

### 演示账号（开发模式 Header 身份）

设置页可切换：`admin@ / editor@ / reviewer@ / viewer@ studio.local`。
身份通过 `X-Studio-User` header 传递，权限矩阵：admin 全部；editor 产线操作；reviewer 审核+改稿；viewer 只读。

### 系统配置管理页（设置页）

仿桌面客户端设置页（左侧分区导航：模型服务 / 数据与队列 / 对象存储 / 安全 / 身份与权限 / 关于）：

- **展示**：LLM Provider、模型、Base URL、API Key（脱敏掩码）、数据库连接串（脱敏）、队列、MinIO、
  SSRF/上传限制等全部生效配置，附 /health 深探针状态
- **修改**：admin 可在页内修改 LLM 配置并保存即时生效（无需重启），
  支持「测试连接」（对网关发一次最小请求）与「恢复环境变量默认」

### 外部 API 数据接入（Connector）

「数据接入」页配置量化平台等外部 API：base_url + 鉴权（密钥只存环境变量名，值不落库），
Endpoint 定义拉取路径与 JSON→Fact 映射（statement 模板 + fields 字段引用），
「立即拉取」后数据进入来源库走正常确认流程：

```bash
curl -X POST http://localhost:8000/api/v1/endpoints/1/pull -H "X-Studio-User: editor@studio.local"
# 定时拉取（生产交 Celery ingestion 队列或外部 cron）
```

### 运维

- 监控：`GET /api/v1/health`（深探针：DB/provider/队列），`GET /metrics`（Prometheus 文本格式），
  每个响应带 `x-trace-id` 并输出 JSON 结构化访问日志
- 多副本指标聚合：Prometheus 按 replica 逐个抓 `/metrics`（service discovery 自动发现实例），
  指标自带 `instance` label 天然区分副本；**不需要** Pushgateway——它适用于批任务，长驻服务抓取即可
- 异步队列：`.env` 设 `TASK_QUEUE_ENABLED=true` + Redis（`CELERY_BROKER_URL`），生成走 `llm` 队列、
  Connector 拉取走 `ingestion` 队列；`make worker` 启动 Celery worker（compose 部署含 worker 服务）
- 数据库迁移：开发环境 `make seed` 幂等建库；生产/PostgreSQL 执行 `make migrate`
  （`alembic upgrade head`，已在 PG 16 实测），后续 schema 变更用 `alembic revision --autogenerate`
- 备份恢复：`make backup`（SQLite 开发库，保留 7 份）；生产 PostgreSQL 流程见
  `docs/runbooks/backup-restore.md`
- **常驻服务（launchd）**：API 与 Celery worker/beat 由 launchd 管理（崩溃自动拉起、开机自启）：
  `launchctl list | grep aicontent` 查看状态，`launchctl kickstart -k gui/$UID/com.aicontent.api` 重启；
  日志在 `logs/api.log` / `logs/worker.log`；运行时密钥集中在 `apps/api/scripts/startup/runtime.env`
  （600 权限、已 gitignore，DreamO token 过期只需改这一个文件后 kickstart worker）
- **数据保留**：beat 每日 03:30 自动清理——llm_run 超期清空大字段（行保留 30 天）、audit_log /
  export_record 留 90 天、终态 workflow 运行留 30 天，库体积有界
- **拉取节奏**：Connector 端点内容指纹去重（无变化不新建 Source）；beat 扫描 300s；端点周期在
  数据接入页可调（仅手动 ~ 每天）

### Golden 评测

```bash
cd apps/api && python scripts/evaluate_content.py            # 30 Topic 全量评测
python scripts/evaluate_content.py --limit 3                 # 冒烟
```

输出无来源数字率 / Fact 覆盖率 / 校验通过率等指标，报告落 `apps/api/evals/reports/`。
mock provider 下是确定性基线；接真实模型后用同一数据集对比。

### 接真实模型

`.env` 设置：

```text
LLM_PROVIDER=openai_compatible   # 兼容 minimax / openai / 任意 OpenAI 风格网关
LLM_BASE_URL=...
LLM_API_KEY=...                  # 只放环境变量，DB 不存明文
LLM_MODEL=...
```

业务层只面向 `LLMProvider` 协议；`MOCK_INJECT_UNFACT_NUMBER=true` 可让 mock 注入一个
FactPack 外数字，用于验证 FactCheck blocker → 无法 approve 的完整链路。

## 目录结构

```text
apps/api/app/
├── models.py               # 全部数据模型（PRD §8 + Connector + STU 扩展字段）
├── routers/                # sources / facts / fact_packs / topics / generate
│                           # / reviews / assets / templates / dashboard / users
│                           # / connectors / settings / health
├── services/
│   ├── parsers.py          # TXT/MD/CSV/JSON/PDF/HTML 解析器（统一 ParsedDocument）
│   ├── url_fetch.py        # SSRF 安全抓取（禁内网/限大小/限跳转/鉴权 header）
│   ├── fact_extractor.py   # 确定性候选事实抽取
│   ├── factpack_service.py # 冲突检测 + 版本 checksum
│   ├── factchecker.py      # Deterministic Checker（数字/日期/风险词/实体）
│   ├── exports.py          # MD / TXT / JSON / SRT（SRT 标记 estimated）
│   ├── connector_service.py# 外部 API 拉取 + JSON→Fact 映射（EPIC-18）
│   └── generation/         # LLMProvider 协议 + mock/openai_compatible
│                           # + prompt 渲染 + 多渠道编排（fact_id 服务端校验）
├── tasks/                  # Celery app + worker 任务（llm/ingestion 队列，开关式启用）
├── observability.py        # trace_id 日志 / Prometheus 指标 / 深探针
├── llm/prompts/            # 三渠道 Prompt 模板（文件为准，启动时同步版本与 checksum）
└── seed.py
apps/api/scripts/           # evaluate_content.py（Golden 评测 CLI）
apps/api/evals/             # golden_topics.json（30 Topic）+ reports/
apps/web/src/pages/         # Dashboard / Sources / Connectors / FactPacks / Topics
│                           # / Workspace(三栏) / Review / Assets / Templates / Settings
apps/api/tests/             # 63 个测试：端到端主干 + 关键不变量 + 服务层单测
docs/runbooks/              # backup-restore.md
```

## 完成情况（对照执行计划）

| EPIC | 状态 | 说明 |
|---|---|---|
| EPIC-00 工程基线 | ✅ | 目录 / Makefile / docker-compose / .env.example / GitHub Actions CI |
| EPIC-01 RBAC + Secret | ✅ | Header 身份开发模式 + 角色矩阵；Key 只走环境变量 |
| EPIC-02 Source Library | ✅ | 文本/URL/文件（txt/md/csv/json/pdf）、解析状态、可信等级、归档 |
| EPIC-03 Fact 模型 | ✅ | 候选抽取、确认/拒绝/编辑、冲突检测、检索 |
| EPIC-04 FactPack | ✅ | 建/增删 item、冻结（校验+checksum）、Clone 版本链 |
| EPIC-05 Voice/Template/Prompt | ✅ | 版本化 + checksum + immutable + clone/publish/archive |
| EPIC-06 Topic Brief | ✅ | 绑定 frozen 包 + 渠道 + 禁止表述 |
| EPIC-07 LLM Provider | ✅ | 协议 + registry + llm_run 记录 + JSON 一次修复 |
| EPIC-08 多渠道生成 | ✅ | 三渠道独立 job、结构化输出、fact_id 服务端校验、失败不互相回滚 |
| EPIC-09 Fact Checker | ✅ | 确定性层（数字/日期/风险词/朴素实体）+ LLM 层接口 + approve gate(409) |
| EPIC-10 编辑器与版本 | ✅ | TipTap 富文本（Markdown 存储契约不变）；revision 递增不覆盖；选区 AI 改写（按位置替换）；上一版 Diff 视图 |
| EPIC-11 Review | ✅ | 队列 / 退回 / 批准（blocker=0 + frozen + revision 未变三重校验） |
| EPIC-12 Asset/Export | ✅ | MD/TXT/JSON(含 provenance)/SRT(标记 estimated) + 分渠道格式限制 |
| EPIC-13 前端页面 | ✅ | P01-P11 全部页面 + 数据接入页（TipTap 编辑器 + 工具栏 + Diff） |
| EPIC-14 原型验收 | ✅ | Mock 全链路（§22 用例含注入口径）已在测试与冒烟中走通 |
| EPIC-15 测试 | ✅ | 63 个测试；30 Topic Golden 集 + evaluate_content.py 评测 CLI |
| EPIC-16 安全 | ✅ | SSRF 防护 / 上传双校验 / Prompt 注入包装（source 只作数据） |
| EPIC-17 运维 | ✅ | Celery 四队列 + worker 容器；/health + /metrics + trace_id 日志；备份 runbook |
| EPIC-18 Connector | ✅ | generic_rest：API 拉取 + 鉴权（env 引用）+ JSON→Fact 映射 + 前端页 |

## 关键决策

1. **同步/异步双模式生成**：默认同步（Mock 毫秒级、测试零依赖）；`TASK_QUEUE_ENABLED=true` 时同一 API 分发到
   Celery `llm/ingestion` 队列，前端以 queued 状态轮询，接口契约不变。
2. **原文存 DB**：V1 长文本存 `source_document.raw_text`；对象存储是文档化升级路径。
3. **建表走 Alembic**：开发环境 seed 幂等可重跑；生产/PostgreSQL 用 `make migrate`（`alembic upgrade head`）建表，已在 PG 16 实测。
4. **LLM Reviewer mock 下透传确定性结果**：不伪造审查结论；接真实模型后自动启用。
5. **编辑器用 TipTap、存储仍是 Markdown**：`tiptap-markdown` 在边界做双向转换，导出 md/txt/srt 契约不变；选区改写按文档位置替换（不再字符串查找首个匹配）。
6. **SRT 时间轴为估算**：明确标记 estimated，不假装精确字幕。
7. **Connector 鉴权凭据只存环境变量名**：DB 记 `api_key_env`，值运行时从进程环境读取，不落库不入日志。
8. **朴素实体检查**：机构后缀启发式，已剥动词前缀/时间指示词降噪；误报为 warning 不阻塞，NER 是升级项。
9. **运行时配置覆盖（前端设置页）**：设置页展示全部生效配置（Secret 一律脱敏回显）；LLM 配置 admin 可在页内
   修改，写入 `system_settings` 表并即时生效（页面覆盖优先于 .env，「恢复默认」回落环境变量；Celery worker
   执行任务前刷新覆盖）。API Key 允许存覆盖表以支持前端配置（本地开发便利），但任何接口都不返回明文；
   生产建议仍走环境变量 / secret manager。
10. **模板中心只增不改、单版本生效**：模板 / Voice / Prompt 内容一律不可编辑（克隆出的草稿也不可改，API 层
    无内容更新端点，PATCH/PUT → 405），变更 = Clone 新版本再发布；同渠道（模板/Prompt）、同名（Voice）至多
    一个 published 生效，发布新版本自动把旧版本降级 archived（选题/任务按 id 引用历史版本，不受影响）；
    启动时修复历史多生效数据（只留最高版本）。生成时取该渠道最新 published 模板兜底。
11. **多模型 Profiles + 场景路由**：设置页可登记多个模型（DeepSeek / MiniMax / OpenAI / 任意兼容网关，模板化
    添加），并按场景路由——内容生成（generate）/ 选区改写（rewrite）/ 事实校验与审核复核（fact_check）/
    选题发现（topic_discovery，基于冻结 FactPack AI 荐题：模型只读已确认事实提候选，人采纳后预填建题表单，
    仍走完整生成→FactCheck→审核链）各自指向不同 Profile；停用或缺失回落默认（页面 llm 覆盖 → .env）。
    provider 实例按 Profile 缓存，保存即失效重载，无需重启。
12. **技能与插件登记 + local_git 文档数据源**：设置页自动发现本机 Agent skills（~/.agents/skills、
    ~/.zcode/skills，frontmatter 解析），勾选启用集存 system_settings.plugins；MCP server 手工登记；
    dsh :3080 状态探测。Connector 新增 local_git 类型：仓库目录（须在 LOCAL_DOCS_ALLOWLIST 前缀内）读
    文档 + best-effort git log，为「开发进展」类内容供数；只读不执行。资产封面为动态 SVG
    （GET /api/v1/assets/{id}/cover.svg，按渠道配色渲染标题，<img> 直接引用故不做 Header 鉴权）。
13. **配图素材随文走 + 公众号 HTML 导出 + dsh 配置面板**：asset_media 统一素材池（底层全量，前端按资产
    归属展示）；首次查看素材时从 structured_json 的 image_prompts / image_suggestions 懒生成占位位
    （含配图说明），上传实体图「只增不改」顶同序位（占位历史保留，与 revision 哲学一致），占位渲染
    渠道配色 SVG；公众号导出新增 HTML（零依赖 MD 渲染 + 微信兼容内联样式）。dsh 执行层：settings.yaml
    只读快照（providers / 默认模型 / env key 状态布尔）+ Studio 侧稳定性配置（默认与备选模型路由、
    超时、重试、产出目录），可勾选「写回 dsh 默认模型」（自动备份 settings.yaml；结构异常拒绝写入）。
    技能扫描目录可配置（空 = 默认两目录）。
14. **工作流画布（仿扣子编排层）**：`/workflows` 页，React Flow 画布把已有能力点串成可执行 DAG——
    节点 handler 直接调用既有路由函数（同一套校验/审计/409 闸门），结果只沉淀到既有实体
    （Source/FactPack/Topic/Draft/Asset），context 是节点间数据总线（copy-on-write 落库）。
    人工节点（采纳/批准）执行到即暂停（waiting_input），节点上内联操作后断点续跑；失败即停、
    可从失败节点重试（生成 handler 校验 job 状态，真实模型偶发解析失败会被暴露而非静默跳过）。
    内置两条模板：「每日舆情 → 荐题」（拉取→抽取自动确认→打包冻结→AI 荐题→人工采纳）、
    「生成 → 出库」（共享一个 Topic，抖音口播/小红书/公众号各自独立一条线：生成→校验→
    人工批准→导出，公众号线再接 wewrite 草稿箱真实发布）。已实测：荐题工作流与三渠道出库
    工作流均以真实 MiniMax 全链跑通，草稿箱 media_id 真实返回。
15. **DreamO 复盘看板走标准数据服务（Connector 映射 v2）**：量化平台已把复盘中心 4 张看板以
    「一表一服务」标准透出（`GET /api/v1/data/apis/{service_key}/records`，X-API-Key 鉴权，
    参数白名单 trade_date/industry_code/idx_type/limit/offset，`*_json` 列需二次解析，
    限流 60 次/分钟，见 DreamOAgents `docs/api/review-dashboards-data-service-api.md`）。
    Connector 切换到 `X-API-Key`（`DREAMO_DATA_API_KEY` env，原 bearer JWT 无 dm:apis 权限且
    8h 过期）；`scripts/seed_dreamo_data_service.py` 幂等维护 4 个端点覆盖 5 张看板
    （行业复盘与行业生命周期共用同一张 190 列 ADS 宽表，按 API 约定按需取用字段，单端点服务
    两看板）。映射协议 v2（`stages`）：aggregate/expand(JSON 字符串列二次解析)/join(名单汇总、
    分布计数)/item + filter/sort_by/limit/derived，配 offset 分页与 `raw_keep_fields` 原始响应
    瘦身（190 列 × 1031 行/日会打爆 raw_text 与事实库）。每日每端点产出 1-19 条高信号事实
    （大盘上下文、情绪/风险摘要、生命周期分布、RRG 象限分布、focus 行业清单），Float32 精度
    噪声在渲染层统一降噪；指纹去重保证非交易日不产生新 Source。
16. **领域知识层（方法论 + 指标字典注入）**：写稿 Agent 不再裸读量化指标——量化平台官方
    产出的《方法论》（看盘顺序/跨图剧本/成稿模板/自检清单）与《指标字典》（逐字段口径/
    阈值/组合用法/误读红线）落 `app/llm/knowledge/`（`scripts/sync_dreamo_knowledge.sh`
    从 DreamOAgents docs/review/ 同步），`domain_knowledge.py` 按 mtime 缓存加载：
    生成与荐题 prompt 注入方法论全文 + 按本稿涉及指标裁剪的口径卡（token 来自事实
    statement/predicate 中文术语 + 来源 raw_text 里的 API 英文字段名，总长封顶防打爆），
    FactCheck 的 LLM Reviewer 注入误读红线节（数字对但方向/口径/确定性写错 → warning）。
    知识是解读规则不是事实：不进 FactPack、不参与数字校验；文档缺席时全链路优雅降级为
    原行为（空串注入，模板不破），落盘即生效零代码改动。

## TODO（按优先级）

1. dsh 沙箱限制：skill 无法写 `~/.wewrite/runs/`，产出暂落 `.wewrite-scratch/`（待沙箱放行或路径迁移）
2. DeepSeek API key 尚未配置（`~/.dsh/env.local` 留空，MiniMax 已可用）
