# Findings

- 「高级运行环境」= 本机运行配置（`pages/Settings`，1204 行：场景路由、模型 Profiles、AI 生图、默认模型、dsh、技能目录、MCP 登记、数据库 / 队列 / 对象存储 / SSRF / 上传限制、身份与权限、关于、文档）+ 15 个旧页面入口 + 能力方法库。
- 旧版本数据为 0：draft、draft_media、mother_revision、content_job、draft_check_run、draft_claim、topic_brief。
- 新版本在用的旧后端：sources / facts（1714 条事实）/ fact_packs（11）——项目事实边界；connectors（4 个连接器、7 个端点，定时拉取）——内容机会数据源；templates（品牌口吻 2、提示词 8）；workflows（55 / 48 次运行）——创作流程；content_asset / review / delivery_target（各 13）——新审阅中心。
- 新页面引用旧页面文件里的组件：`SystemAssetsKnowledgePage` 用 `pages/Sources`（SourceImportModal、SourceDrawer）、`pages/Materials`（MaterialUploadModal）、`pages/FactPacks`（PackBuilder、NewPackForm）；设置页内嵌 `pages/Settings`、`pages/Connectors`、`pages/Templates`。
- 新页面里还有一处旧入口链接：审阅中心「兼容入口 → 旧 Topic 审核与发布」。
- 用户原则（2026-10-24）：新功能沿用的旧后端保留并搬进新结构；只属于旧版本的全部删除，要干净的单一版本。数据接入（内容机会数据源，如每日行情自动成文）和模板（把好作品风格沉淀成模板 / Skill，给便宜模型用）必须保留。
- 工作流：workflow 表 55 条 = 角色默认 10（published）、商品默认 2、项目级 40（自动复制）、草稿 3；workflow_run 48 次。34 个后端服务文件依赖引擎。用户 2026-10-24 同意去掉设计层、只留引擎和内置流程。
- 实施中调整（2026-10-25）：
  - 「按项目覆盖流程 / 按角色设默认流程」的接口保留为内部接口（不在任何页面出现）：13 个测试文件约 150 个新功能测试靠它装入阶段流程，它也是引擎把流程绑到作品的方式；删掉收益小、代价大。页面上的编辑入口已全部去掉。
  - 项目级流程副本不是「自动复制的垃圾」：它们是「选择创作流程」时钉住的版本，36 个被运行历史或作品引用，删了会断历史，只删了 4 个无人引用的。
  - 原管理员运行配置里的默认模型兜底、AI 生图、dsh、技能目录仍被生成代码读取，按原则 1 搬进「模型与 AI」，没有删；场景路由 / 模型 Profiles 已被新「模型与 AI」覆盖，删；数据库 / 队列 / 对象存储 / SSRF / 上传限制 / 身份 / 关于只是展示，删。
  - 旧版本有四个早就没人引用的前端文件（ProductPlaceholders、AccountDesk、EditAgentStatus、ProductCreationDialog），不属于旧版本，未动。
