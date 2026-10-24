# 工作台任务导航与页面原型

## PRD / 需求背景
用户于2026-10-19确认先制作可操作原型，并系统检查全部尚未优化板块。目标是让人知道当前任务、所处步骤、下一步；不再把全部功能平铺。用户于本轮进一步确认原型，授权先正式接入内容机会与今日工作台，其余模块逐步调整。

## 当前阶段
ARCHIVED，19/19；五批全部已接入本机正式平台，包括效果复盘与设置目录。基线main@8539806 + 相邻未提交变更完整保留。

## 目录结构
- proposal.md / design.md / specs/ / tasks.md：范围、方案、验收与任务。
- module-audit.md：全路由盘点和页面归属。
- task_plan.md / progress.md / findings.md / review.md：实施与复核记录。
- prototype/：独立可点击HTML/CSS/JS；模拟数据，无正式API。

## 已完成
已核对34个路由/10主导航及9个正式入口页面。完成分组导航、机会主链、资料管理、审阅与复盘原型；独立设计/代码复核与桌面/手机交互检查通过。

## 待完成 / TODO
全部19项已完成；7个capability的21条新增要求已同步正式规格，已归档。没有本change范围内的剩余任务；商品真实素材验收等相邻change保持独立。商品审阅空角色查询与长期资料页面层级已修复，已优化工作台保留。

## 关键设计决策
沿用项目业务根、独立商品域与角色域；商品六步、角色五步和已优化模型配置内部保持。列表、详情、编辑分别承接不同目的；高级历史可追溯。

## 依赖与启动
正式UI使用现有API8000与Web5173，无新增依赖；Web常规命令为在apps/web执行 `npm run dev` / `npm run build`。原型只需浏览器和Python3：在本change目录执行 `python3 -m http.server 18419 --bind 127.0.0.1`。原型无外部依赖、无模型调用；所有模拟结果不能证明正式能力已接入。

## 原型入口与建议查看顺序

[打开内容机会原型](http://127.0.0.1:18419/prototype/#/opportunities)

1. 点击第一条机会→确认方向→阅读/选择资料→模拟创建，返回会保留草稿。
2. 左侧切换项目档案、角色与账号、素材与知识，看列表、详情、编辑如何分开。
3. 审阅与交付→处理问题→账号授权→模拟本地交付；商品单独走商品账号。
4. 效果复盘→建议→明确作用范围；设置查看模型保留边界和兼容目录。

全部为模拟数据，仅当前标签页暂存；顶部可重置演示。商品六步、角色五步和模型配置内部保留，仅展示衔接边界。82个可达URL来自对象/子页，并非新增82个功能模块。

## 验证

见review.md及evidence/：164次布局检查、最终13项主链交互与前轮6项导航/草稿检查通过；代码/设计独立复核通过。正式接入、真实模型与发布未验证。当前本地静态服务端口18419，不修改5173正式服务。

## 首批正式入口（2026-10-19已接入）

- [今日工作台](http://127.0.0.1:5173/home)：先看待处理，再继续创作；活动、身份提醒和全部记录分页面。
- [科技内容机会](http://127.0.0.1:5173/opportunities?persona_id=2)：查看有效建议→推荐详情→确认创作方向→阅读并勾选来源→确认选题并创建项目。
- 运行与来源、历史、高级人工维护仍可进入，日常无需重填自动评估。草稿在当前用户/机会/评估范围暂存；409或评估更新保留输入并明确核对。
- 创建仅建立项目与初始任务书，来源关系不等于已确认事实；后续从项目现有入口继续角色创作，已有项目直接打开。

### 首批代码与验证

代码：apps/web/src/App.tsx（只叠加导航分组）、product/HomePage.tsx、OpportunityPages.tsx、opportunityTypes.ts。当前main@8539806+相邻未提交变更，未重置、提交或推送。

18既有检查、Web构建/预算、26隔离交互、30正式页面布局与独立规范/代码复核通过；18机会/3角色回读不变。证据见review.md与evidence/phase1-*。没有新的持久测试、迁移或真实模型调用。

下一批按任务第5节：作品队列/项目入口→审阅交付→长期资料→复盘/设置；已优化工作台与模型配置内部继续保留。全站change不在首批完成时归档。

## 第二批正式入口（2026-10-19）

- `/production?workspace=persona`：作品清单为默认页，任务记录独立；筛选和分页支持返回。
- `/projects`：项目档案，搜索/状态/分页；`?view=new`独立新建页，名称与目标暂存至当前用户标签页。
- `/projects/:id`：总览、作品、项目资料、历史记录四组；九个旧tab链接仍兼容，制作工作台内部不改。

代码为apps/web/src/product下ProductionQueuePage、PersistentProjectsPage、PersistentProjectPage及project/ProjectOverviewTab、ProjectMatrixTab。第二批本地验收通过；仍为main@8539806+相邻未提交变更，未提交/push/归档。

验证：46项相关既有检查、Web构建/预算、27项隔离交互断言和20项正式只读布局通过，7项目回读不变。额外schema检查10通过/1失败：旧测试期望a3series00000001，当前配置unitlife000001；本批未改后端/迁移，差异单独记录，不将全套测试宣称全绿。下一批5.2审阅与交付仍待实施。


## 第三批正式入口（2026-10-19）

[审阅与交付](http://127.0.0.1:5173/review)：先在作品列表搜索/筛选，点“核对作品”，按核对作品→问题与审批→账号与授权→交付与回填操作。历史与变更为独立页；既有project/unit/candidate链接保留，列表返回保留筛选/页码。步骤浏览不代表批准或执行。

当前问题使用简明提示，技术状态/原始检查可展开。商品按Unit.production_domain使用自有账号目录，不查询null或历史角色账号。候选级草稿/逐目标回执、权限未知只读、历史/归档禁写、精确hash与冻结账号、Unknown对账均保持；ZIP与人工回执不等于公开发布。

代码：ProjectReviewCenter.tsx；App.tsx仅导航文字；services/project_review_projection.py本批仅增加production_domain只读字段，既有相邻商品逻辑不归本批。132相关既有检查、Web构建/预算、40临时隔离断言、28正式只读布局及规范/TS/Python独立复核通过；7项目、2账号及旧审核投影字段回读不变，4个既有制作工作台文件hash不变。证据见review.md与evidence/phase3-*。API8000已重启加载只读字段，Web5173可直接使用。未新增依赖、迁移或持久测试，未正式审批/交付、未调用模型或远端发布；未提交/push/归档。全站仍active，下一批5.3长期资料。


## 第四批正式入口（2026-10-19）

- [角色目录](http://127.0.0.1:5173/identities)：搜索/状态/分页选择角色，再看概览、编辑资料、修订历史、创作配置；关联管理、工作流、内容记忆和平台连接分别进入。旧 `?persona=:id` 仍打开对应角色。
- [账号目录](http://127.0.0.1:5173/identities?directory=account)：同时保留角色账号与独立自有账号；`/accounts`定位到此目录。登记只记录公开标识，不表示登录或发布授权。
- [栏目目录](http://127.0.0.1:5173/identities?directory=series)：保留跨平台角色栏目与旧账号栏目关系、版本化投放绑定。
- [素材与知识](http://127.0.0.1:5173/assets)：按素材、文档网页、证据包、集合查找；选资源后进入概览、版本/正文、使用记录、使用到项目、管理。上传/导入为常用入口，其余工具放二级入口；列表不同时铺开详情和工具。

资源可按自有项目名称明确引用，精确Revision、冻结证据包/checksum、边界expected_revision及权利原合同保持。集合只是组织引用，不等于事实边界或公开授权。角色草稿同对象往返保留，换对象丢弃需确认；409先核对再显式加载，禁止自动重试。

本批代码：IdentityWorkspace.tsx、SystemAssetsKnowledgePage.tsx、systemLibraryTypes.ts；App仅/accounts定位；LearningWorkspace仅MemoryPanel/MemoryDetail可选readOnly透传及维护表单门禁，不重做复盘。后台/API/依赖/迁移未改。145既有检查通过、1跳过；65隔离断言、74正式桌面/手机布局、规范与TS独立复核通过；15组API投影（含3角色、2账号、151共享资源）回读相同，12个既有工作台/创作/导入/生成组件文件hash保留。见review.md和evidence/phase4-*。

正式资料未因验收改写；未真实注册账号、上传/生成/接受素材、绑定项目或变更权利。main@8539806+相邻未提交改动保留；未提交/push/归档。下一批5.4效果复盘与必要设置。


## 第五批入口与本轮验收
- [效果复盘](http://127.0.0.1:5173/learning)：已发布作品→表现与反馈→表现对比→改进建议→明确适用范围。同步/导入、观察与审核各自单独进入；默认不展示全部写表单。
- [设置目录](http://127.0.0.1:5173/settings)：六类用途目录→分类配置；[原模型配置](http://127.0.0.1:5173/settings?section=models)内部保持。
- 本轮128既有检查、71隔离断言、52桌面/手机布局、构建预算及独立规范/TS复核通过，详见review.md和evidence/phase5-*。正式业务数据只读；现有复盘记录为空，未制造发布/指标。
- 本轮代码只改LearningWorkspace、ProductSettingsPage与App导航名称；无后端/依赖/迁移/持久测试，未提交或推送。模型内部函数及保留工作台指纹核对。


## 最终归档回执
2026-10-19，全部19/19完成，OpenSpec CLI同步21新增/0修改/0删除，归档目录即本目录。独立规范与代码复核通过；15个保留文件及模型函数不变。本地main@8539806＋未提交修改，未推送或发布；归档仅关闭本change的规格生命周期，不表示整个产品已完成真实运营验收。详情evidence/phase5-archive.txt及phase5-canonical-readback.json。


## 主链补充验收（2026-10-19）
已修复主页/机会/项目/制作/审阅/复盘的来源返回、制作至审阅及交付至复盘入口，角色资料文案更正。正式只读25项、隔离转换5项和审阅交付40项通过；构建、独立复核、strict44/44通过。14保留组件+模型函数不变；正式未写入，未提交/push/发布。详见review.md本轮章节及evidence/journey-*。

补充回归：复盘46项隔离断言通过（evidence/journey-learning-isolated.json）；主代理重跑返回规则验证，完整7页链、30次反复往返、6类非法地址及筛选/候选上下文均通过（journey-helper.txt）。临时脚本留在/tmp，无持久测试代码。

最终返回文案按来源区分首页/审阅/其他页面，4项实际只读断言通过（journey-return-labels.json），独立复核通过。本轮浏览器断言共120项（25+5+40+46+4），另有返回规则专项验证；无持久测试代码及正式写入。


## 最新追加：真实内容验收已完成
2026-10-19，机会3→项目35/作品41→9阶段创作→Master61→批准候选3→本地ZIP已实际跑通，未公开发布。两处后端阻断已修，完整回执见review.md的“真实科技机会至本地交付验收”。保留1条角色检查提醒并记录委托AI复核，不冒充全自动通过。代码在services/stage_resolver.py、services/creation_recipes.py，仍为main@8539806的未提交工作区；无新依赖/迁移。下一步可在审阅与交付查看正文、下载成品包；公开发布不在本轮授权范围。


Latest verification: identity truncation fixed; same Master61 passes8/8. Current candidate4 and target4. Use output/ai-tech-eval-project35-checked.zip; candidate3 retained as history. No public publication. See latest review section.


Latest real lifestyle acceptance: opportunity8 -> project36/unit42 -> all9 stages -> Master65 -> candidate5 -> local target5 ZIP. Final checks8/8 pass. No public publication. Review latest report for editorial interventions and narrowly scoped identity-check fix. Current branch remains main@8539806 plus preserved adjacent uncommitted work.


## 2026-10-19 双角色图文/音频真实验收补充
科技图文unit43：Master73、candidate6、target6；生活图文unit45：Master74、candidate7、target7（以real-media-43/45-delivery.json为准）。各4张1080×1440实际PNG，逐张检查后通过原生render_attestation绑定；结构、事实、权限、渲染、平台检查通过，身份视觉语义覆盖警告保留并做委托AI审阅处置。两个本地ZIP CRC通过，未公开发布。
生活音频unit46：原音色chunzhen_xuedi，任务165419d8fb1d40e1bc0b5152f5b2b9ad，220.683875秒WAV；已完整ASR、声学检查、接受输出及本地打包。clipping=0，保留ASR简繁/专名/文本差异提醒与human_review_required；没有直接试听，不声称人类感官验收。
科技音频unit44仍未完成：真实TTS任务9b9aa8c83bba44699c14a8df8003f9c9返回unknown，正常recover后generation_original_job_unknown，未取得文件或供应商任务号。只读音色目录确认原音色仍存在。现有回执不能确定供应商是否执行或具体失败原因；未重置状态、未盲目重发、未替换默认声音。此项不能判通过。
限定修复：creative_configuration保留原生工具身份，提示方法仅作用于声音规划；creation_recipes去除重复域/ASR正文但保留接受校验与哈希；stage_resolver明确图文引用目标定位合同。独立代码复核通过。最终既有检查148+600通过，无新增持久测试；8个优化工作台/模型配置组件哈希不变，published-content总数0。原文字作品及相邻修改保留。
成果：output/persona-35-graphic.zip、output/persona-36-graphic.zip、output/lifestyle-audio-project36.zip。证据：real-media-operations.jsonl、real-media-43-delivery.json、real-media-45-delivery.json、real-media-46-delivery.json、real-media-44-unresolved.json、real-media-preservation.json及两份测试日志。原导航change已归档，本补充任务不重复归档、不把音频未完成项关闭。

正式页面回读：四个制作入口、两个候选交付入口，桌面1440/手机390共12项通过，下载ZIP按钮可用；零浏览器错误与写请求。证据real-media-ui.json。


## 科技音频续验：明确额度阻断（2026-10-19）
用户授权原模型/音色重试。读取原任务冻结2685字符稿，以speech-2.8-hd、lengdan_xiongzhang、rate1.0执行一次CLI诊断重试，0.47秒内退出1，供应商明确返回“当前已达到 Token Plan 用量上限”，未产出音频。证据real-tech-audio-quota-rejection.json。此前任务丢弃CLI具体错误，只存unknown；原请求原因不能从旧回执单独证明，本次同输入复现已确认当前额度阻断。
原音色仍在目录；不更换音色/模型、不修改计费策略、不购买或升级套餐。旧unknown历史保留。额度恢复后才能从正常TTS阶段继续ASR、QC及本地交付；task50/51保持未完成，不宣称全流程验收通过。本轮无业务代码改动，无需重跑无关测试；使用using-superpowers、systematic-debugging、executing-plans及openspec-apply-change流程。


## 科技音频额度刷新后闭环（2026-10-19）
用户明确授权重新生成，原run21未知回执完整保留。正常平台拒绝同run未知任务重发，故在原unit44/workflow33建立run24；未重置未知状态。首次口播候选合同不合格被拒绝，按本次覆盖指令重新生成约三分钟中文口播，审阅通过后继续。覆盖指令不改默认模型/角色配置。
run24五阶段spoken/voice/tts/audio_asr/audio_quality全部succeeded，最后continuation complete。新TTS任务f5fbbc786b1b4835a8ba471fd7378b8d，素材revision80；speech-2.8-hd、lengdan_xiongzhang、rate1.0与原任务冻结完全一致，multimedia_config_hash也一致。
实际WAV为192.838秒、32000Hz、单声道、12342818字节；哈希52f593b32369294afac13615953dd1101b0c9c71364a63577805c287470f512b。全长本地ASR72段；792归一化字符中18处差异(2.27%)，逐段比对为主要同音识别差异，保留audio_transcript_script_differs警告并明确委托AI处置。clipping=0，RMS=-23.256dBFS，头尾静音156/172ms，无声学阻断。未直接试听，human_review_required保留；不能宣称人类感官验收或字幕已经校正。
本地交付output/tech-audio-project35.zip包含WAV、script.txt、原始转写及ASR字幕草稿、质量报告和使用说明；ZIP CRC和包内音频哈希通过。API真实回读run24全部成功；8个工作台/模型配置组件哈希不变，published total0。无业务代码改动，不重复跑上一轮748项代码测试；未提交/push/公开发布。
证据real-tech-audio-task.json、real-tech-audio-run-final.json、real-tech-audio-delivery.json、real-tech-audio-preservation.json及五阶段回执。至此两角色图文和音频均完成约定的本地技术验收，保留感官/字幕边界；原导航change已归档，不重复归档。
