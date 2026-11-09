# search-promotion-workbench Specification

## Purpose
TBD - created by archiving change search-promotion-workbench. Update Purpose after archive.
## Requirements
### Requirement: Search promotion is its own workbench and production domain

系统 SHALL 提供「搜索推广工作台」作为独立入口，其作品属于生产域 `search`；角色内容工作台和商品视频工作台 MUST NOT 列出 search 域作品，搜索推广工作台也只列 search 域作品。search 域作品 MUST 复用现有文章、图文、视频生产链条，MUST NOT 另建一套，也 MUST NOT 改变另外两个工作台的行为。

#### Scenario: 各工作台互不混列
- **WHEN** 搜索推广项目里开了作品
- **THEN** 作品只出现在搜索推广工作台

### Requirement: Two levels: promotion subject and promotion project

推广对象 SHALL 保存一个品牌、产品或服务的长期资料：资料与带出处的事实、统一品牌说法、禁用词、问题库。推广项目 SHALL 是一篇核心稿及其衍生作品：从问题库选定的一个主题、形式与基调、核心稿、衍生作品、各平台版本。统一品牌说法和禁用词 MUST 由同一推广对象下的所有项目共用；形式与基调 SHALL 按项目设置。

#### Scenario: 不同项目不同基调
- **WHEN** 同一推广对象下两个项目分别设「专业中立科普」和「选购顾问」
- **THEN** 两个项目按各自基调写，但品牌说法和禁用词相同

### Requirement: Only two human gates

文章与图文 SHALL 只在两处等人：基础资料确认、成稿审核。问题库、开项目、写作、衍生、自查、成图判断、平台版本 MUST 由 AI 完成，MUST NOT 要求人确认才能继续；人 MAY 随时查看和修改。视频 SHALL 沿用视频链条的停点（导演稿、小样、成片），成片那一步即其成稿审核，MUST NOT 再另审一次。平台 MUST NOT 提供替人确认资料或通过成稿的 MCP 工具。

#### Scenario: 图文成图不停
- **WHEN** 图文作品渲染出成图
- **THEN** 由写作模型看图判断，不合格自己改，不停下等人

#### Scenario: 视频不重复审
- **WHEN** 搜索推广视频的成片被人通过
- **THEN** 各平台发布文案一并通过，不再出现在整批成稿审核里

### Requirement: Promotion subject is confirmed by a person before use

推广对象 SHALL 只在搜索推广工作台维护，MUST NOT 与商品共用数据，带版本保存。推广对象 MAY 由人录入，或由 AI 根据名称和资料起草。AI 起草的事实 MUST 附原文链接和摘录；平台 MUST 打开链接核对，对不上的退回 AI，链接打不开的标「需人工核对」。没有出处的事实标为「待补出处」，写作 MUST NOT 引用。只有人确认过的版本 SHALL 用于问题库和开项目；修改产生新版本，需重新确认。禁用词默认带绝对化用词清单。

#### Scenario: 摘录对不上
- **WHEN** AI 起草的一条事实，摘录不在所附链接的原文里
- **THEN** 这条事实退回 AI，不进入草稿

#### Scenario: 链接打不开
- **WHEN** AI 起草的一条事实附的是需要登录的页面
- **THEN** 这条事实标「需人工核对」，人在确认资料时判断保留还是删掉

#### Scenario: 未确认不能用
- **WHEN** 推广对象只有草稿
- **THEN** 不能生成问题库，也不能开项目

### Requirement: Promotion subjects use a two-level category

推广对象分类 SHALL 为两层：大类固定为实体产品、数字产品、服务、品牌与机构；小类预置（实体产品：消费品、工业设备、原材料与化学品、零部件；数字产品：APP、软件 / SaaS、数据服务与接口、网站与平台；服务：专业服务、工程与施工、培训教育、本地服务；品牌与机构：品牌、公司、门店），并 SHALL 允许新增、改名、停用小类。AI MAY 提议新小类，随资料一起确认。停用的小类 MUST NOT 再被新选，已使用的保留。

#### Scenario: AI 提议新小类
- **WHEN** AI 起草「窑炉」时提议在实体产品下新增「窑炉设备」
- **THEN** 人确认资料时一并确认这个小类

### Requirement: Question library belongs to the subject

问题库 SHALL 挂在推广对象上，由 AI 依据已确认资料和搜索信号生成：用户问题、关键词（主词、长尾词、品牌词）、搜索意图、优先级。每个问题 MUST 标来源（搜索结果链接，或「模型推断」），并 SHALL 显示覆盖状态（没做 / 在做 / 已有成稿）。同一问题已有在做或已有成稿的项目时，MUST NOT 再开新项目，除非人明确指定。人 MAY 修改问题库，修改产生新版本，已开的项目沿用开项目时的版本。

#### Scenario: 防止重复
- **WHEN** AI 批量开项目时某个问题已有在做的项目
- **THEN** 跳过这个问题

### Requirement: Projects are opened and produced by AI

项目 SHALL 由人在问题库勾选问题后交给 AI，或由 AI 按优先级批量开，单次批量 MUST NOT 超过 5 个项目。每个项目 SHALL 设形式（文章 / 图文 / 视频，可多选）、基调、读者水平，AI 先给建议。开项目时 SHALL 把推广对象已确认版本中带出处的事实冻结为项目事实边界，并锁定所用资料版本与问题库版本。AI SHALL 按问题意图从体裁库（定义科普、选购指南、对比评测、推荐清单、操作教程、价格与参数说明、案例解读、问答合集）选一种体裁；每个体裁是一个平台 skill，规定结构和必用组件。

#### Scenario: 批量上限
- **WHEN** AI 按优先级批量开项目，问题库里有 12 个未覆盖问题
- **THEN** 这次最多开 5 个

#### Scenario: 事实跟着项目
- **WHEN** 项目开出后推广对象资料改成新版本并确认
- **THEN** 这个项目仍按开项目时冻结的事实写

### Requirement: Core text, derived works and writing rules

每个项目 SHALL 先写一篇文字核心稿；项目含图文 / 视频时由核心稿衍生，视频 MUST 先做口语化评审再存导演稿。项目不含「文章」时，核心稿只作底稿，不出平台版本。写作简报 SHALL 包含对应问题、关键词、基调、体裁、品牌说法、禁用词与已冻结的带出处事实，并要求：结论在开头；只用带出处的事实并写明出处与数据时间；写到竞品时竞品信息也有出处、不贬低；带问答段；品牌说法一致；不用禁用词；不堆关键词；不编造。

#### Scenario: 只要视频
- **WHEN** 项目形式只选了视频
- **THEN** 先写核心稿，再由它做口语化评审和导演稿；核心稿本身不出平台版本

### Requirement: Writer, skills and models follow the other workbenches

search 域作品 SHALL 提供与角色内容工作台相同的「平台模型 / 第三方模型」开关和「平台 skill」开关；项目设默认写作方式（默认第三方模型），作品继承，单篇可改。关掉平台 skill 时 MUST NOT 使用平台写作 skill（含体裁 skill），剪辑、特效 skill 照常可用。各环节平台模型 SHALL 沿用「设置 → 模型」用途配置。

#### Scenario: 关掉平台 skill
- **WHEN** 某个作品关掉平台 skill
- **THEN** 写文案和脚本时不用平台 skill，剪辑、特效 skill 照常可用

### Requirement: Platform model runs the same steps in the background

选平台模型时，平台 SHALL 在后台按顺序执行与第三方模型路径相同的平台功能，MUST NOT 走逐阶段等人挑选、采用的创作流程；人工关卡 MUST 仍只有确认资料和审成稿。用途对应：资料起草用选题与资料（topic_discovery）及已接入网页搜索；问题库用检索（discoverability）；核心稿用写作（generate），事实复核用事实核查（fact_review）；平台版本与按意见重写用平台适配（platform_adaptation）。核心稿检查不过关时 SHALL 带着问题重写，最多 2 轮，仍不过关 MUST 停下并写明原因。每一步 SHALL 记录所用模型、结果与失败原因，失败步骤 SHALL 可单独重试。本期平台模型只做文章；图文、视频作品 SHALL 标为「等第三方模型」。

#### Scenario: 点开始后全自动
- **WHEN** 资料已确认，人在推广对象页点「开始」，选 3 个项目、形式文章、发布平台公众号和知乎
- **THEN** 平台生成或沿用问题库，开 3 个项目，写核心稿、自查、出公众号和知乎版本，整批送到「待审成稿」，中间不等人

#### Scenario: 重写两轮仍不过关
- **WHEN** 某个核心稿两轮重写后事实复核仍有阻断问题
- **THEN** 这个项目停在核心稿，项目页写明原因并提供「重试」，其他项目照常继续

#### Scenario: 按意见重写
- **WHEN** 人对平台模型写的知乎版写了意见
- **THEN** 平台按意见重写知乎版、复核后再送审

### Requirement: Projects set their publishing platforms

项目 SHALL 设发布平台（默认公众号、知乎、头条），两条路径都按它出平台版本。公众号版本 MUST NOT 依赖机械映射：由模型直接按公众号格式改写，平台照常检查。

#### Scenario: 公众号版本
- **WHEN** 核心稿结构不规整，机械映射到公众号会被拒绝
- **THEN** 模型直接写出公众号格式的版本，检查通过后照常送审

### Requirement: Platform versions are reviewed in one batch and handed off

AI SHALL 为每个作品按平台出版本，每个版本换切入角度和标题句式，版本 MUST NOT 绑定账号；同一项目内各平台版本标题 MUST NOT 相同。文章与图文 SHALL 整批送审：一个审阅页列出全部平台版本，人逐篇「通过」或「写意见」，写意见的交回 AI 修改后再送审；主稿 MUST NOT 要求人单独审批。平台版本通过后 SHALL 自动生成复制包和稿件包，稿件包 SHALL 附「如属付费推广，按规定标明『广告』」提醒；search 域作品 MUST NOT 进入推草稿箱、回执回填或效果复盘。

#### Scenario: 整批审核
- **WHEN** AI 送审 3 个项目共 9 个平台版本
- **THEN** 人在一个页面看完，通过 7 个、对 2 个写意见
- **AND** 通过的 7 个立即可复制和下载，2 个回到 AI 修改

#### Scenario: 标题重复
- **WHEN** 同一项目的知乎版和头条版标题一样
- **THEN** 平台版本检查给出提醒，AI 改写其中一个

#### Scenario: 转给别人发
- **WHEN** 用户下载公众号版稿件包转给别人的公众号
- **THEN** 平台不要求账号，也不等待回执

