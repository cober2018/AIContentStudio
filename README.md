# AI Content Studio（AI 内容生产中心）

事实驱动的内容生产系统：把结构化数据、研究笔记、文件、URL、人工观点整理成 **FactPack**，面向抖音 / 小红书 / 公众号生成内容，经事实校验与人工审核后导出；公众号可进一步自动写入官方草稿箱。

长期产品目标以 [`03_ai_content_studio_PRD.md`](03_ai_content_studio_PRD.md) 为准；其中 §3 的三渠道是首选样本，§3.1 已补入原对话整理的 11 平台文章/图文 V1 目标，并保留抖音脚本。`04_ai_content_studio_execution_plan.md` 是旧版执行参考，边界澄清稿见 [`docs/AI_CONTENT_STUDIO_REQUIREMENTS_REFINED.md`](docs/AI_CONTENT_STUDIO_REQUIREMENTS_REFINED.md)。

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
- 目录结构：`apps/api/app/routers/content_projects.py` 提供持久化项目、单元、流程与快照 API；`apps/api/app/services/project_*` 和 `data_source_plugins.py` 承接授权、版本、产物和数据来源；`apps/web/src/product/PersistentProjectPages.tsx`、`ProductionDesigner.tsx` 是真实项目入口。原 `ProjectPages.tsx` 和 `mockProjects.ts` 留在 `/projects/demo` 作本地演示。规格见 [`openspec/changes/archive/2026-09-27-fe-f2-persistent-production-workflow/proposal.md`](openspec/changes/archive/2026-09-27-fe-f2-persistent-production-workflow/proposal.md) 与同目录 design/specs/tasks。
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

### 下一版规划：文章/图文全渠道

> **2026-09-24 更新（V1 PRD 2.0 Content Harness 已实施）**：下一段提到的 `complete-prd-v1-channel-deliverables` 已标记 **superseded**，被主变更 [`align-v1-prd2-content-harness`](openspec/changes/align-v1-prd2-content-harness/proposal.md) 吸收并实施。当前代码已落地：Channel Registry（14 平台 profile，新增渠道无需改枚举/迁移）、Workflow 版本化 + Node Plugin Registry、Material Library（素材全局复用/权利链）、DraftCheckRun 统一检查、Discoverability（Pre/Post SEO）、Candidate Manifest schema v2、Delivery Router（copy_package / assisted_draft / auto_draft + DeliveryAttempt：prepared→远端→结果，unknown 不自动重发）、节点级 Rerun/Stale、Review & Publish Center（`/review-publish`）。真实账号自动发布仍未验证，平台能力一律如实标注 unverified；PRD §15–16 与 30 Topic 门槛仍需单独验收。实施与偏差记录见该 change 的 `design.md`。

当前待确认的 OpenSpec 是 [`complete-prd-v1-channel-deliverables`](openspec/changes/complete-prd-v1-channel-deliverables/proposal.md)：先建立多平台内容形态规则和交付主链，再分批完成长文、问答、图文、社交文本的 11 平台成品与验收，同时保留抖音脚本。本项尚未实施；PRD §15–16 的原始验收以及 §3.1 的全渠道验收均需单独完成。

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
