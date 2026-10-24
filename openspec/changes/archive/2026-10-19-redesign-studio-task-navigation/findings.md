# 实际发现

- MCP图工具本会话不可用，代码发现使用App.tsx路由和定向页面检查；未扫描无关后端。
- OpportunityPages.tsx硬编码自动分析不可用，同时直接展现Signal.annotation JSON、修订、AssessmentForm；后端daily_opportunities已保存system评估，两者不一致。
- HomePage重复展示进行中、最近活动、最近更新，且存在旧自动分析不可用提示。
- IdentityWorkspace已有七个页签，但树中品牌/角色/账号/栏目混合，普通配置存在JSON工作流定义。
- LearningWorkspace已有分页和页签，不是完全没有结构；同页多个ActionForm仍要求ID/JSON和技术分类，缺少从真实作品到建议采用的任务引导。
- SystemAssetsKnowledgePage已有分页与详情/权利/使用记录，应保留；新建、导入、生成与引用需明确入口。
- ProductSettingsPage模型分区、兼容入口和未保存保护已有，不推倒重建。
- NorthStar保留项目业务根和身份/记忆分离；新导航不能删除这些模型，不能让一次反馈隐式改长期风格。

## 正式页面只读回看

2026-10-19用隔离浏览器逐页导航/home、/opportunities/14、/projects、/production?workspace=persona、/review、/identities、/assets、/learning、/settings；未点击写操作，浏览器拦截所有API写方法。结果见evidence/current-pages-readonly.json，当前机会截图在output/playwright/opportunity-before-1440.png。

- 机会详情实见来源、修订、追加人工评估、创建项目及2个表单；学习默认页实见4个表单。数据说明页面拥挤，不以按钮数独立判定好坏。
- 原型设计之外的现有真实缺陷：审阅页默认儿童拖鞋商品单元时请求 `/content-personas/null/accounts` 返回422；ProjectReviewCenter.tsx:81按unit.persona_id无条件构建地址。正式商品域不依赖角色的合同与此处不一致，应在后续审阅页接入时修复并回归。此次只记录，没有修改业务代码。
- 内容机会列表把全角色自动研究、provider/凭据、批次/暂停控制置于选题列表上方。原型缩为当前角色状态摘要，后台明细进入独立运行/来源管理页；“未运行”和“无合适建议”仍须区分。

## 首批正式实施确认

2026-10-19用户已确认原型与首批实施，规范/任务已同步，8/19开工。当前/home API完整返回；机会18条、角色3个。正式读基线记录evidence/phase1-before-readonly.json。现有转换只创建项目/初始Brief，不能把界面“开始创作”说成已生成内容单元；本轮方向确认后沿用项目现有入口。

已验证API评估返回analysis_source/analysis_provider_key/analysis_provider_version，前端原类型缺这三项。analyze API真实返回capability_unavailable，不增加假的“自动重评”按钮。new/watching的明确最终确认先qualification再convert，原服务expected_revision和idempotency边界保留。

当前工作区存在大量相邻未提交依赖，本轮按用户授权定向修改原工作区，不reset/clean/checkout/提交。MCP代码图工具本会话仍不可用，定向源码读取。

## 首批复核与修正

- 主页使用persona_id而机会初版读取role，导致角色/科技跨日规则丢失；已统一persona_id并兼容旧role。26项fixture覆盖该链与API actionable_only/date参数。
- 无评估来源曾被创建门槛误挡；已分开只读资料与转换资格，reader和无评估均能读正文。
- Home原ready代表执行条件而非今日结果；现在只用日期匹配today_run展示今日状态，null/缺失/paused/补采分别说明。
- 真实页面仍有ISO时间墙与master_*内部标签；已将风险摘要转中文/去重，卡片改推荐方向，时效依据可展开，全部资料缺口分条保留。
- 窄屏高级元数据长checksum造成溢出，增加局部换行，最终30布局无溢出。
- 首轮隔离脚本has_more误把字符串offset=0视作非零，导致下一页被fixture禁用；校准fixture后26项全过，初始JSON保留，未将此记为业务缺陷。

## 第二批当前结构

ProductionQueuePage已具备归档生命周期及details延迟加载，但刷新仍无条件调用tasks.refetch/external.refetch，可能在记录未打开时发请求；本批改为独立记录视图并保持显式GET。筛选/分页目前在局部state，返回不稳定。PersistentProjectsPage新建按钮不依权限、只有标题弹窗；项目详情九同级tab和编辑/归档与日常并排，原deep-link应保留而不是删掉。ProjectOverviewTab已有业务nextAction，应复用不另算状态。


2026-10-19第二批：执行记录分离后仍需共享分页，并在项目读取失败时禁止将外部执行判为零；新建失败与列表读取错误必须独立；创建成功需同步清除sessionStorage草稿，不能仅依赖卸载前effect。保留view切换前的分页和查询。权限未知/错误按只读，项目及概况请求丢弃过期响应。7处独立复核问题均已修正。额外schema测试仍断言旧迁移头，当前unitlife000001不一致，本批不修改后端配置。


2026-10-19第三批实际发现：
- Review projection原来没有production_domain，persona_id既可null，也可能是商品旧历史保留值，不能据其决定账号路径。增加模型权威域只读投影，商品用现有GET /content-accounts，不新增账号隔离规则。
- 版本比较未读取成功时不能声称“首个候选/没有前序版本”；候选读取失败不能指示用户重新制作冻结。均按pending/error/absent分开。
- unit.reviews只属于整个单元最近候选，不能在选择旧候选或其它v5系列时冒称所选候选审批记录。标题标明最近Candidate ID并明确归属。
- 手机截图显示逐条风险卡仍过密，改为简明问题列表，完整状态/原因统一二级展开；当前阻断、Unknown和warning不隐藏。
- 正式数据检查全部GET；写链、ZIP和official-readback均在全拦截fixture，不能将其等同真实账号/远端发布验收。


2026-10-19第四批关键发现与决策：
- 原身份树只遍历角色账号，独立账号漏展；目录改用既有owned accounts，保留原父子关系和账号栏目/跨平台栏目的不同scope。
- 同对象换页不等于离开草稿：普通画像409比较、创作与工作流草稿保持；跨对象确认丢弃时须清空工作流加载缓存，防止旧输入以clean状态复活。浏览器返回直接以URL派生视图，避免两份tab状态异步覆盖。
- 资料写入和子表单需同一同步锁：原各自busy无法阻止创建栏目与登记账号并发，早完成会错误解除导航锁。新增共享起始锁及回调scope/epoch核对。
- 权限GET失败不应抹掉可读目录，也不应显示成功空态；权限独立降为只读，目录读失败独立错误与显式重读。
- `view in tools`会接收__proto__/constructor等继承属性，改为自有键检查，所有手写链接保持可读错误页。
- SourceDrawer/PackBuilder虽然是既有组件，其可变入口仍须由当前资源读取、权限、非归档门控；只读正文保留独立content页。
- 手机长生效JSON会撑大grid隐式最小宽度，字段卡min-w-0、明确单列及任意换行解决，不改内容。
- MemoryPanel只新增readOnly可选参数，保留只读记忆/修订读取；其余旧调用默认行为不变，效果复盘主功能留到5.4。


## 第五批实际发现
原复盘首页同时加载同步、恢复发布声明、外部导入、批量导入和列表；候选详情直接展示全部操作。设置默认打开模型，分类仅组件内state，无独立目录或可重载分类URL。已优化的模型内部有保留挂载草稿与离开保护，本批只调整外层导航，模型内部函数和组件必须逐字保持。当前正式复盘三类记录均0；非空交互须隔离验证，不制造正式发布记录。

第五批最终决策：旧URL编码保留但分区用已发布作品/表现对比/改进建议/已保留经验；筛选收起以优先任务。defaultValue表单需要相关URL key恢复浏览器历史，不能只更新查询。已保存结论详情需与作品一样保存list_offset。设置role=dialog外层需要自己的覆盖尺寸；原模型逻辑逐字不变。复用不等于隐式采用：候选通过、记忆提升、方法候选三项仍分别明确操作。

主链实际读取发现：ProductionWorkspace delivery仅展开高级工具，无审阅入口；ProjectReviewCenter无learning入口；角色目标页误写详细商品资料；队列继续创作和项目详情返回没有携带列表筛选。上述均为既有导航合同的实际遗漏，使用现有业务API修复，不新增生成/发布行为。


主链复核补充：深度4不足覆盖Home→机会列表→机会详情→项目→制作→审阅→复盘；改为8并去除重复目标。冻结Candidate的独立审阅链接也须与制作台通用入口使用同一返回规则。正式作品7没有冻结候选，实际读链与隔离交付操作分别记录，未虚构实际发布或模型生成。


真实创作发现：项目sources关联不等于可供创作引用的冻结evidence_refs；须核对事实边界与模型使用许可。机会3原始网页为作者个人复盘，本次不沿用行业统计或作者经历，改成原创实践建议并留原网址。真实模型回执记录openai_compatible / gemini-3.8-flash-high / configuration_revision13，仅说明当前网关配置，不推断上游模型。


## 真实文字创作验证结论（2026-10-19）
推论字段规则必须进入模型输出合同，不能只依赖结果校验；当前Master在创作方法阶段的重复载荷会超过标题阶段输入上限，按精确ID引用可保留内容且消除重复。两处已修并真实重跑。最终角色检查提醒如实保留，用委托AI复核处置，不降级检查门禁。本地copy_package使用GET包下载接口，不能把execute拒绝当作发布适配故障。


2026-10-19：身份快照17默认JSON10411字符以上；三个媒体creative_profile占6236字符。文字检查无差别传完整多模态快照导致8000字符截断。保留通用visual_language等字段，只排除已知非文字制作配置。


Lifestyle real run: persona3 has no account. Existing v4 local copy_package accepts an explicit local recipient without inventing platform identity. Current-mode source guard requires a confirmed fact/event with a real linked source; author_opinion alone correctly remains blocked. Source123/date-verification event714 and pack6 satisfy this after actual page read. Date extraction produced numeric date candidates712/713; these were not confirmed or used. No guard relaxation.

Lifestyle refine102 returned Markdown-derived content without structured citations and reintroduced publication dates. Normal edited acceptance restored exact-span source references and omitted nonessential dates from prose (dates remain source/FactPack provenance). This is an explicit editorial intervention, not a claim of unattended quality. No global citation/date gate was disabled.

## 2026-10-19 图文/音频实际验收发现
- 科技图文作品43：已接受图卡计划，但组装预览报graphic_composition_method_invalid。阶段方法开关覆盖了必须存在的确定性排版工具身份；修复仅保留组成器工具身份，方法开关仍控制创作指导。
- 科技口语稿两次模型输出被安全合同拒绝；保留拒绝，不放松检测。生活配音已实际返回WAV，待质量验收。
- 媒体列表的credential_continuity_unverified是无凭据探测的库存状态，不等于实际执行不可用；生活TTS真实执行成功。

### 图文/音频继续验收
科技口语稿第三次受控生成已通过；不放松安全检测。修正确定性组成器与TTS工具身份；音频长稿和ASR报告重复进入上下文导致128KiB回执超界，保留原域快照并使用哈希引用去重。生活TTS220.684秒、69段ASR已完成，字面对比提醒保留。图文验收初始误沿用百家号文章渠道，现两独立图文作品改小红书图文，原文字作品不动。532项既有检查通过（后续修改仍需重跑）。


真实PNG入库不等于完成Master渲染：必须声明render_asset_ref，按canvas绑定slot_key/placement/sort_order，并提交真实render_input_hash确认。此次通过现有API完整完成，没有放宽门禁。科技TTS未知状态无原供应商任务号，recover保持未知；不得当作失败后可安全自动重试。


## 科技音频续验：明确额度阻断（2026-10-19）
用户授权原模型/音色重试。读取原任务冻结2685字符稿，以speech-2.8-hd、lengdan_xiongzhang、rate1.0执行一次CLI诊断重试，0.47秒内退出1，供应商明确返回“当前已达到 Token Plan 用量上限”，未产出音频。证据real-tech-audio-quota-rejection.json。此前任务丢弃CLI具体错误，只存unknown；原请求原因不能从旧回执单独证明，本次同输入复现已确认当前额度阻断。
原音色仍在目录；不更换音色/模型、不修改计费策略、不购买或升级套餐。旧unknown历史保留。额度恢复后才能从正常TTS阶段继续ASR、QC及本地交付；task50/51保持未完成，不宣称全流程验收通过。本轮无业务代码改动，无需重跑无关测试；使用using-superpowers、systematic-debugging、executing-plans及openspec-apply-change流程。

额度恢复后正常TTS已成功，之前额度阻断解除。未知原任务按合同不能原地重发；用户明确授权新运行重试后成功，旧证据不删。语义口播稿单次覆盖约三分钟，模型和音色默认配置未改变。
