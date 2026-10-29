2026-10-29 **产品文档只留本地**：根目录的产品战略、PRD、开发 OpenSpec、前端契约、原型和总过程记录（task_plan / progress / findings / HANDOVER）移到 `openspec/docs/`；原 `docs/` 移到 `openspec/docs/项目文档/`，openspec 根目录的需求包移到 `openspec/docs/需求包/`；公开仓库历史中已一并清除，与本地成果目录 `output/` 一样加入 .gitignore，不再上传；文件仍在本机。

2026-10-29 **商品工作台 AE 模板（已本地实施）**：新增 15 个商品模板（亮相、卖点、参数与对比、价格与优惠、材质与成分、使用方法、信任背书、下单引导），竖屏 9:16 和横屏 16:9 两版，播放安全区零越界，用户看审片视频验收后入库为 ready；另复用 `callout-label`（卖点标注）、`magnifier`（成分特写），共 17 项写进 craft-ae 模板库「商品」分组，商品分镜的 AE 包装指向这里。价格、评价、证书、参数只填真实资料，商品图不变形。设置页「AE 模板库」可按商品分类看预览视频。审片页 `output/_平台/模板审片/商品/index.html`。[需求入口](openspec/changes/archive/2026-10-29-product-ae-templates/README.md)。

2026-10-29 **项目文件夹带日期前缀、本地输出目录规范（已本地实施）**：内容项目的素材文件夹统一命名为 `YYYYMMDD_项目名称`（日期取项目创建日，北京时间；名称取标题第一个「｜」之前），定下后不随标题改动；素材盘上已有的两个项目已改为 `20261022_海底光缆`、`20261027_儿童麸质饼干`，素材位置同步更新、全部可找到。本地输出目录 `output/`：跟内容项目有关的成果放 `output/YYYYMMDD_项目名称/`，平台自身的放 `output/_平台/`（`模板审片/竖屏`、`模板审片/横屏`、`规格/播放安全区`、`吸收资料`、`剪辑技法`、`测试`），以后生成的东西照此放。[需求入口](openspec/changes/archive/2026-10-28-project-folder-date-and-output-layout/README.md)。

2026-10-29 **AE 模板横屏版、模板库预览、默认由大模型选模板（已本地实施）**：46 个模板加 16:9 版本（横屏单独排版、过 16:9 安全区检查），出片按画幅自动选、没有横屏版时明确报错不拉伸；每个模板竖横各一段动画预览，设置 → AE 模板库可按类别查看和播放；默认由大模型按内容自选模板，用户微调时点名的效果必须用，按口播出现的效果（如并列图片展开）按配音逐句时间对齐。[需求入口](openspec/changes/archive/2026-10-28-ae-templates-landscape-and-library/README.md)。

2026-10-28 **AE 模板库第二批：46 个竖屏模板入库（已本地实施）**：口播、AI 科技短片、生活短片用，分九类（关键词标题、金句对句、标注聚焦、人物图形、数字图表、步骤流程对比、开场章节转场、素材地图、结尾引导），叠加类带透明通道；按用户给的播放安全区排版，剪辑 skill 收进安全区规格、每个工程带安全区参考层、新增自动检查（零越界）；动态效果用完整动画视频和参考卡片并排验收。[需求入口](openspec/changes/archive/2026-10-28-ae-template-library-batch/README.md)。

2026-10-29 **模型配置全局唯一（已本地实施，未提交）**：所有大模型配置只在 设置 → AI 与模型：厂商与密钥在「厂商与模型」登记一次（MiniMax 卡片即 MiniMax 厂商）；对话、封面生图、写作工具（dsh）、选题搜索在「用途路由」选；生图/视频/配音/语音转文字在「生成能力与插件」选厂商+模型，地址密钥不再单独填。删除兜底模型、AI 生图、dsh 执行层表单与旧数据，环境变量只能切离线 mock；角色、商品、SKU、阶段和调优不再单独选模型（旧记录只作历史，不生效）。本机 mmx / dsh / wewrite 配置文件由这里自动写入。[需求入口](openspec/changes/archive/2026-10-28-unify-model-config/README.md)。

2026-10-29 **MiniMax 只认一把密钥（已本地实施，未提交）**：设置 → 厂商与模型的 MiniMax 卡片是唯一填 MiniMax 密钥的地方；写作（MiniMax 地址的主模型/配置档）、AI 生图（MiniMax）、配音、选题搜索都用它；主模型和生图选 MiniMax 时不再显示密钥框，旧密钥已清除；保存卡片同步写入本机 `~/.mmx/config.json`、`~/.dsh/env.local`、`~/.wewrite/config.yaml` 的密钥项。[需求入口](openspec/changes/archive/2026-10-28-single-minimax-key/README.md)。

2026-10-28 **MiniMax 厂商改成设置页可配置（已本地实施）**：设置 → 厂商与模型里 MiniMax 卡片可编辑：API Key（保存/清除，只显掩码，标注「本页保存」还是「本机 mmx 登录」）、访问地址（https 或本机/局域网）、区域、启用开关（即时生效）、测试按钮；页面保存的值在调用本机 mmx 时优先生效，没保存就回退 mmx 自己的登录和启动开关。[需求入口](openspec/changes/archive/2026-10-28-minimax-vendor-settings/README.md)。

2026-10-28 **设置里配置素材数据源（已本地实施）**：设置 → 素材数据源，7 个免费素材库（Pexels、Pixabay、Openverse、Wikimedia、NASA、Internet Archive，新接 Coverr 视频）各一张卡：说明、许可、Key（只显示掩码）、启用开关、测试、申请链接；启动配置文件里已有的 Key 继续有效；关掉的来源不参与镜头素材搜索。[需求入口](openspec/changes/archive/2026-10-28-stock-source-settings/README.md)。

2026-10-28 **吸收三个视频仓库的方法（已本地实施）**：skill 分商品 / 角色 / 通用三类，作品只看到自己那类加通用；clipforge 的带货方法写成商品脚本 v2、商品镜头 v2、带货合规检查，以及通用的脚本评审、免费素材找挑、数字人出镜（数字人生成功能未上线，只用于规划）；shotcraft、talkcraft 232 张配方梳理后换算成 AE / 达芬奇做法进剪辑武器库（新增文字包装、标注、素材呈现、数据、转场等），全部「试用」。[需求入口](openspec/changes/archive/2026-10-28-absorb-shotcraft-talkcraft-clipforge/README.md)。

2026-10-28 **厂商与模型显示 MiniMax（已本地实施）**：设置 → 厂商与模型里只读显示 MiniMax（本机 mmx 命令行）的版本、启用状态、区域、密钥掩码和用途（一键配音、AI 生图），账号仍在终端用 mmx 管理。[需求入口](openspec/changes/archive/2026-10-27-show-minimax-vendor/README.md)。

2026-10-28 **商品视频改用第三方模型视频流程（已本地实施）**：商品视频制作页改为「商品与本条目标 → 导演稿 → 素材 → 配音与音乐 → 小样 → 成片 → 交付」，和角色视频共用同一套页面与后台，导演稿一步有「平台写作 skill」开关；旧的导演方案 / 定样 / 剪辑包装页去掉。[需求入口](openspec/changes/archive/2026-10-27-product-video-uses-chain/README.md)。

2026-10-28 **第三方模型用不用平台写作 skill 由人控制（已本地实施）**：每条作品一个「平台写作 skill」开关（默认可以用），关掉后第三方模型读不到平台的文案、脚本、镜头规划等 skill；剪辑和特效 skill（craft-resolve、craft-ae）一直可用。模型读需求时能看到开关状态。[需求入口](openspec/changes/archive/2026-10-27-stage-switches-for-third-party-model/README.md)。

2026-10-28 **作品的制作归各自工作台（已本地实施）**：商品视频工作台点商品改为「进入商品」，看到已有作品继续做，只有「为此商品新建视频」才新建；制作页左侧菜单亮所属工作台，返回链接回到工作台（商品 → 该商品作品页）。内容项目只管项目本身。网址不变。[需求入口](openspec/changes/archive/2026-10-27-product-work-stays-in-workbench/README.md)。

2026-10-28 **内容项目默认只显示进行中（已本地实施）**：内容项目列表默认隐藏已归档项目，可切到「全部状态」或「已归档」。[需求入口](openspec/changes/archive/2026-10-27-projects-default-active/README.md)。

2026-10-28 **从项目新建商品自动带入信息（已本地实施）**：从项目点「商品视频」进入工作台后新建 SKU，商品名称和介绍自动填成项目标题和目标，可改后再保存。[需求入口](openspec/changes/archive/2026-10-27-prefill-sku-from-project/README.md)。

2026-10-28 **从内容项目直接开始作品（已本地实施）**：项目里还没有作品时，项目页提示「这个项目要做什么？」——选角色内容打开添加作品窗口；选商品视频进入商品视频工作台选或新建商品，视频加在这个项目里，不再新建项目，已有素材和资料都保留。「作品」页也可「加商品视频」。[需求入口](openspec/changes/archive/2026-10-27-start-work-from-project/README.md)。

2026-10-28 **项目引入原始素材文件夹（已本地实施）**：项目「资料」页可填素材库盘上的一个文件夹路径，里面的视频、图片、音频原地登记到项目；成片通过后，没被用到的原始素材按类型搬进项目标准目录（视频/其他素材、图片/图片素材、音频/音效），文件名不改，搬不动的可在资料页「重新归档」。[需求入口](openspec/changes/archive/2026-10-27-import-raw-material-folder/README.md)。

2026-10-27 **剪辑武器库与选用表（已本地实施）**：把一套剪辑课提炼的 100 张技巧卡梳理成 DaVinci / AE 做法，写进 craft-resolve（7 类 + 选用表 choose.md）和 craft-ae（4 类）；按问题挑招、克制使用，导演稿镜头备注写手法和理由；每招带「试用 / 常用 / 退役」状态，由本地技能 craft-arsenal 负责加新招和复盘。技能改名为 craft-resolve、craft-ae。[需求入口](openspec/changes/archive/2026-10-27-distill-editing-course-into-craft-skills/README.md)。

2026-10-24 **视频流程去掉「专业执行准备」（已本地实施）**：新视频流程只有「导演稿」；角色 2、3 和商品视频默认流程已切换；进行中的作品隐藏这一步，「准备剪辑」直接建剪辑任务。[需求入口](openspec/changes/remove-professional-prepare-stage/README.md)。

2026-10-23 **导演包好了自动开剪（已本地实施，待安装）**：点「准备剪辑」后平台建好粗剪任务排队；本机后台每分钟看一次，自动启动 Claude Code（可换 Codex）领任务、达芬奇剪辑调色、AE 做特效镜头、交回粗剪等你审片。安装一次：`apps/api/scripts/install_edit_dispatcher.sh`。[需求入口](openspec/changes/auto-start-edit-agent/README.md)。

2026-10-23 **采用导演稿后自动准备剪辑（已本地实施）**：点「采用这版」后，平台自动补齐素材、把素材放进主稿、判断哪些镜头要 AE（达芬奇负责全部剪辑调色，AE 按镜头加特效并写原因）、保存并重做导演包；之前采用过的作品在导演稿处点「准备剪辑」。[需求入口](openspec/changes/auto-edit-handoff/README.md)。

2026-10-23 **素材库唯一存放 + 浮窗拖拽 + 存储位置设置（已本地实施）**：新素材统一存进素材库里的 `AIContentStudio/视频|图片|音频`，U 盘没插时提示「素材库未连接」、不存别处；设置 → 存储位置可改素材库和本地工作位置；右下角「素材库」浮窗可把素材拖到分镜表的素材格，也可从访达批量拖入。[需求入口](openspec/changes/material-library-single-home/README.md)。

2026-10-23 **视频页面简化（已本地实施）**：内容方案只有一张分镜表和一个按钮（生成导演稿 → 采用这版，采用后自动补齐素材）；制作内容只留分镜表、配音、导演包和保存，其余收进「更多」。一键生成配音还没做。[需求入口](openspec/changes/simplify-video-production-page/README.md)。

2026-10-23 **补齐素材：新 AE 模板 + AI 示意图（已本地实施）**：新增对比卡、图片推镜两个模板；空着的行最后用平台生图做一张示意图，再用推镜模板做成镜头，画面里标「AI 示意」（证明类标「非实拍」），每次最多 8 张。[需求入口](openspec/changes/autofill-generated-shots/README.md)。
2026-10-23 **分镜表 AI 补齐素材（已本地实施）**：一键给空行补素材：先搜素材库和可商用素材站（看图打分），合格就选；不合格或属于后期做的行用 AE 模板生成；都不行标缺口并写原因。每个自动选择都写来源，不覆盖你选过的，主稿由你保存。[需求入口](openspec/changes/storyboard-auto-material/README.md)。
2026-10-23 **文章流程精简为两步（已本地实施）**：九步改为「写作方案（2–3 个完整方案选一个）→ 成稿（一次出全文，确认一次）→ 质量检查自动跑」；渠道版本只改格式。[需求入口](openspec/changes/article-two-stage-flow/README.md)。
2026-10-23 **AE / 达芬奇两个技巧 skill 与 AE 模板库（已本地实施）**：craft-ae、craft-resolve 两个独立入口，各有目录，由平台 MCP 提供；AE 效果固化为带说明书的版本化模板，本机 aerender 渲染成候选素材。[需求入口](openspec/changes/craft-skills-ae-resolve/README.md)。
2026-10-23 **视频导演稿改为一张分镜表（已本地实施）**：新视频流程去掉「视频脚本」「镜头计划」，导演稿一次生成一张表，一行一个镜头：镜头、时长、信息点、画面、运镜、台词、声音、备注、素材；镜头格子里选过的素材不再重复选。[需求入口](openspec/changes/video-storyboard-table/README.md)。
2026-10-23 **导演稿沿用镜头计划（已本地实施，待生产验收）**：视频导演稿直接沿用已采用镜头计划的镜头（数量、顺序、编号、时长），AI 只润色每个镜头的口播和画面；去掉导演稿最多 8 段的上限对有镜头计划时的限制，镜头槽位素材按编号对上。[需求入口](openspec/changes/master-follows-shot-plan/README.md)。

2026-10-22 **采用方案不再被补素材/重启打断 + 制作页「下一步」（已在本地完成，未提交/归档）**：补素材或 API 重启后，等你确认的方案仍可采用，脚本等真实输入变了才要重做；制作页左侧导航「内容方案」下列出各阶段，等你处理的那一项高亮；阶段报错改成大白话；模型调用结果不确定时，你可以确认放弃那次再重新生成。[需求入口](openspec/changes/fix-stage-adoption-and-next-step/README.md)。

2026-10-22 **镜头素材槽位**（已在本地完成，未提交/归档）：视频制作中每个镜头带简报（旁白、画面、搜索词、生成提示词、建议途径），作为接受任意来源的槽位，显示 缺素材/有候选/已选定，素材库找素材的选择自动出现在对应镜头；缺素材不挡起草和剪辑；MCP 只读 `get_shot_slots`。[需求入口](openspec/changes/add-shot-material-slots/README.md)。

2026-10-22 **设置新增「MCP 接入」**：平台 MCP 的状态与自检、Codex/Claude Code 连接方式、23 个工具的分组清单（只读/会改动、MCP 不能做的事）、外部 MCP 服务登记集中在 `/settings?section=mcp`；不返回令牌。Claude Code 已在本机接入。未提交/归档。[需求入口](openspec/changes/add-mcp-settings/README.md)。

2026-10-22 **大模型出方案、你在平台决定（本地实现，待你走一遍验收）**：创作 MCP 新增 8 个工具（查看/预览/运行阶段、读结果、读你的决定、按文案找素材与回读），MCP 不能替你接受/拒绝/绑定/发布；图文排版候选在接受前即显示平台渲染的卡片图，素材每段新增「都不合适」。卡片排版改为字号自适应填满。未提交/归档/发布。[需求入口](openspec/changes/add-agent-review-loop/README.md)。

2026-10-20 **角色内容方法改进接续交接，11/25**：参考/五步/方法与交接技术验收已补，科技/生活真实正文B正在质评，最新601项既有检查/Web通过；生活精修Unknown、新图/音视频/新题与用户默认决定仍待。最新A17最终修复尚未加载正式API，保留原配置/商品/历史，未提交推送或归档发布。[最新交接与原25项验收映射](openspec/changes/improve-persona-content-methods/development-handoff.md)。

2026-10-19 **生活角色真实创作与本地交付完成**：机会8→项目36/作品42，9阶段完成、最终8项检查通过，候选5批准、本地ZIP已校验；修正文字角色审核职责，保留其他工作台与模型配置。未公开发布。[验收记录](openspec/changes/archive/2026-10-19-redesign-studio-task-navigation/review.md)。

2026-10-19 **Identity review warning fixed**: unchanged Master61 passes8/8 real checks; candidate4 and local delivery4 ready. Original candidate retained; no public publication. [Verification](openspec/changes/archive/2026-10-19-redesign-studio-task-navigation/review.md).

2026-10-19 **真实科技机会创作与本地交付已跑通**：机会3→项目35/作品41，9阶段完成、候选3按委托AI审阅批准、ZIP下载校验通过。修复推论引用合同和标题输入重复两处阻断；保留1条角色检查提醒。未公开发布/提交/push。[实际验收](openspec/changes/archive/2026-10-19-redesign-studio-task-navigation/review.md)。

2026-10-19 **完整使用链补充验收通过**：补齐制作→审阅→复盘入口，保留主页/机会/项目来源及筛选、步骤、候选返回；更正角色任务书文案。正式只读走链、隔离转换与交付、桌面/手机和独立复核通过，模型配置与制作内部保持。未正式写入/提交/push/发布。[验收记录](openspec/changes/archive/2026-10-19-redesign-studio-task-navigation/review.md)。

2026-10-19 **任务导航五批全部接入并归档，19/19**：机会/主页、作品/项目、审阅交付、角色/素材、效果复盘与设置均通过本机限定验收；商品/角色工作台与模型内部保留。本批128既有检查、71隔离断言、52桌面/手机布局及独立复核通过；9项API投影、15个保留文件与模型函数核对不变。7个正式规格新增21条要求。未提交/push/发布。[入口与验收](openspec/changes/archive/2026-10-19-redesign-studio-task-navigation/README.md)。

2026-10-19 **全站任务导航原型已按确认方案分批落地**：原34路由盘点和独立模拟原型保留在[归档成果](openspec/changes/archive/2026-10-19-redesign-studio-task-navigation/README.md)，原型本身仍为模拟，正式接入与验收以五批回执为准。

2026-10-19 **科技规则与Radar自动日报已启用，15/17**：科技按48小时动态/30天进展/持久价值参评，有效建议跨日可见，空态依据实际运行说明。免费Radar首轮15条项目线索已入库；现有08:00日批先自动生成日报、导入，再冻结科技评估。每天一次、失败/unknown不盲重发，生活来源与预算不变。81既有检查、隔离smoke、Web/预算及限定代码复核通过；自然日批与归档仍待，不把启用视为质量验收。无迁移/付费调用/提交推送。[范围、代码与使用入口](openspec/changes/improve-tech-opportunity-selection/README.md)。

2026-10-18 **商品实拍前端一致性修正通过，58/66**：六步引导、商品摘要和拍摄/后期状态已统一；正式12页桌面/手机、下载任务书及7场景回归通过。当前Master57四镜可拍，旧数据保留，真实成片仍待。[入口与验收](openspec/changes/improve-product-keyframe-preproduction/README.md)。

2026-10-18 **已确认测试项目7–10彻底清理完成**：物理删除528条专属记录、27媒体文件和7执行目录；其余记录与29保留媒体文件核对一致。项目34及其他任务/共用配置保留，首页待处理仅剩项目34的2项，API健康。混合备份及共用开发历史未改写。[运维回执](openspec/changes/archive/2026-10-18-purge-confirmed-test-projects/README.md)。

2026-10-18 **商品前端一致性追加核对：56/66**。四段实拍任务已正式显示且确认可拍；发现旧AI引导与旧Brief表达仍需统一，重开两项展示验收。[当前记录](openspec/changes/improve-product-keyframe-preproduction/README.md)。

2026-10-18 **商品实拍流程与Skills非素材工程验收完成，58/66**：脚本→拍摄任务书→逐镜原片审阅/选段→后期包与反馈版本已接通；模型辅助、SKU范围与手机页面通过隔离验收。儿童拖鞋Master55已确认可拍，只需四段原片；真实成片仍待，不归档提交。[任务书与验收](openspec/changes/improve-product-keyframe-preproduction/README.md)。

2026-10-18 **角色创作清单归档、恢复与删除已启用并归档，8/8**：先备份再加法迁移，231项既有检查、Web构建及隔离页面/API操作、代码复核通过。正式API/Worker健康，40旧单元及内容历史保全；删除只移出清单，不清理共享素材。未对正式作品执行归档/删除，未push。[使用与验收](openspec/changes/archive/2026-10-18-add-persona-creation-list-lifecycle/README.md)。

2026-10-18 **商品实拍任务书主链已接入，53/66**：脚本/任务书确认、逐镜原片与选段审阅、自编方法开关已接；360+18既有检查及隔离上传链/Web通过，本机ready。儿童拖鞋Master50为待审阅草稿，旧资料保全；真实拍摄/成片和完整反馈验收仍待，未归档提交。[入口与证据](openspec/changes/improve-product-keyframe-preproduction/README.md)。

2026-10-18 **角色创作清单归档/删除方案待确认**：只读检查确认五步入口与已有科技样片可读；当前未选渠道阻止冻结交付，新 Recipe 尚未运行。新增归档恢复与逻辑删除 OpenSpec，业务实现0/8，未改正式数据。[方案与体检](openspec/changes/archive/2026-10-18-add-persona-creation-list-lifecycle/README.md)。

2026-10-18 **自然日批科技0条/生活3条，转载日期语义修复后待再次自然验收**：科技候选按冻结日期门槛退出，无凑数；天气选题转载页日期误标原文，已备份修复生成/双评分提示并追加日期v2，另修正一处正文未明示的限定词。旧运行/评分/历史保留；40既有检查通过、1原有失败，API/页面与Worker核验通过。两change仍43/45、8/10，10月19日自然日批继续验收，未归档。[同一验收记录](openspec/changes/add-daily-persona-content-opportunities/review.md)。

2026-10-18 **目标与受众第9节返修验收通过，50/58**：R2默认继承筛选/作品优先级/冻结版本、R4并发保存/继承方法保全已验证。442既有检查、Web及隔离联动验证通过，API已加载且ready=true。原8项素材与成片收尾仍待，未归档提交。[验收记录](openspec/changes/improve-product-keyframe-preproduction/review.md)。

2026-10-18 **目标与受众方法二次独立验收未通过，46/58**：R1/R3及R5现有样本通过；R2默认继承筛选、R4并发保存仍需返修，模型归属按保存回执更正。442既有检查/Web/strict通过；未改业务代码/正式数据，未提交归档。[验收记录](openspec/changes/improve-product-keyframe-preproduction/review.md)。

2026-10-17 **目标与受众方法独立验收未通过，45/58**：442既有检查、Web构建及strict通过；关闭指令残留、字段筛选、关闭保存、并发配置保全与选区润色质量需返修，已回写同一[验收记录](openspec/changes/improve-product-keyframe-preproduction/review.md)。未改业务代码/正式数据，未归档。

2026-10-17 **商品目标与受众方法方案已确认、待实施，43/58**：同一OpenSpec第9节新增7项，拟接两项自有可开关方法至AI补齐/润色；商品空目标/受众可给待确认建议。仅方案修订，无代码/数据变化；既有商品解耦及旁白优先路线保持。[方案入口](openspec/changes/improve-product-keyframe-preproduction/README.md)。

2026-10-17 **商品业务域解耦已在本机接入，工程验收通过，43/51**：商品入口、上下文、默认方法、音色/模型配置、SKU留存、质量与账号交付独立于Persona，AE/Resolve等底层共用。备份后迁移productdomain0001，106旧表旧字段一致；旧Master/Run/Identity/模型及媒体历史逐行保留。零角色mock链、真实API预览、Web构建及独立复核通过；原8项真实素材/新样片质量仍待，未归档/提交/push。[使用与验收](openspec/changes/improve-product-keyframe-preproduction/README.md)。

2026-10-17 **双工作台与SKU已接入，35/43**：商品六步/角色五步、SKU与版本配置已启用；桌面/窄屏24页、键盘与读取异常、候选全拒绝/局部补交机制完成，相关138项复跑/Web及独立复核通过。修复默认图文渠道误用于视频；当前沙发Master47仅策划，缺事实与新媒体质量验收，未归档/提交/push。[入口、验收及一次性材料清单](openspec/changes/improve-product-keyframe-preproduction/README.md)。

2026-10-17 **新入口自然日批科技2条/生活1条；正文边界修复后待再次自然验收**：一条VERID功能细节仅见上游摘要，未获冻结正文支撑，已备份修复模型输入并追加评估v2；原运行/评分/历史保留。40项既有检查通过、1项修复前同样失败；API/页面与Worker回读正常。两change仍43/45、8/10，下一次自然日批通过后才归档。[验收与证据](openspec/changes/add-daily-persona-content-opportunities/review.md)。

2026-10-17 **双工作台与SKU商品资产方案待实施确认，16/43**：平台内商品视频独立、底层共用；角色5步、商品“目标→导演方案→视觉声音定样→逐镜素材→剪辑包装→成片反馈”。已整理24组来源的方法抽象与取舍、多类型作品/口型同步/参考二创、连续镜头和逐镜回传页面；不导入第三方实现。用户已确认先用可操作原型评审作品列表、导演方案与逐镜素材，Canva稿停止作为实施依据；SKU长期档案、多套方案与作品留存已补入同一方案和原型；最新原型接通选品后六步模拟路径、视觉/声音局部页签、剪辑交接回片及定位返工，语法/规范与静态复核完成，尚无新版浏览器验收；原16项完成保留，第7节23项正式实现待批准。[页面与方案](openspec/changes/improve-product-keyframe-preproduction/product-workspace-design.md)。

2026-10-16 **AI表单补齐、定点润色与商品素材导演已接入，17/17**：任意已填内容补空白、逐项确认、固定浮窗润色、反馈与明确偏好版本、品类/风格阶段配置和实际看图动态提示词已接入；完整商品生产可用性仍待真实任务验收。纯候选286检查/Web构建及独立复核通过；备份后加法迁移、本机API/Worker和页面回读通过。旧商品关键帧仍待确认，未生成新视频、未push。[使用与验收](openspec/changes/archive/2026-10-16-add-contextual-ai-form-assistance/README.md)。

2026-10-16 **科技/生活聚合站已验证后正式切换，8/10**：科技71/生活22条真实精选快照及增量、原文正文、正式后台补采/API/页面通过；41既有检查、Web及独立复核通过。双备份后源54/55分别关联角色2/3，原来源配置/订阅及12条机会历史保留；每日08:00选题沿用原质量门槛，08:20跟进新入口自然验收，通过后归档。[接入方案](openspec/changes/add-aihot-persona-source-integration/README.md)。

2026-10-16 **商品销售资料与三列镜头台已接入，完整生产收口实施中，16/20**：版本化买家/场景/购买理由/证据/顾虑/CTA、可编辑素材分类与独立内部成本已实现；视频单元逐镜选图、提示词、人工回传、审阅采用和Resolve/AE交接可用。280项既有检查、Web构建及独立复核通过；本机服务与真实页面已只读回读。五张图片用户已确认，正式Brief9/Master45为新版六镜，任务3–7已准备待人工网页回传；真实Run18脚本/镜头/整稿修改后采用通过，新视频未生成。3文件导航/状态说明已改，132检查/Web及复核通过；隔离空白起步真实模型通过，图片按用户确认以有限模型用途导入，公开门禁保留。部分前置代码已随8539806提交，本change未归档。[同一成果与审图](openspec/changes/improve-product-keyframe-preproduction/README.md)。

2026-10-16 **自然日批已运行，日期语义修复后待再次自然验收，43/45**：科技/生活真实Beat→Worker各1条；科技发布时间误作事件日期，已备份后最小修复并追加近期报道评估v2，原始运行/评分/昨日10条保留。41既有检查、独立复核及正式API/页面通过，来源partial如实显示；下次08:00自然日批继续验收，尚未归档，无新增依赖/迁移或push。[同一成果](openspec/changes/add-daily-persona-content-opportunities/README.md)。

2026-10-16 **商品视频Skills正式接入、样片已回收，20/20**：六项方法/首轮冻结/阶段开关及AE/Resolve适配完成；懒人沙发16秒有声样片、8项接受产物和Master41本地绑定通过委托AI质量评审。纯候选564项既有检查/1跳过、Web及独立复核通过；已归档同步10条规范并选择性本地提交。未直接试听，公开门禁保留、角色默认不变、未push。[使用入口与验收](openspec/changes/archive/2026-10-16-add-product-video-production-skills/README.md)。

2026-10-16 **角色风格与阶段Skills已正式启用并归档，22/22**：科技角色v4、12项方法/十阶段开关/3首场景配乐已接入；47秒有声样片及8个产物正式接受，Master39本地绑定，32项API回读通过。纯候选521项既有检查、Web及独立复核通过；未直接试听、公开门禁保持，已选择性本地提交、未push。[使用入口与验收](openspec/changes/archive/2026-10-16-add-persona-production-skill-profiles/README.md)。

2026-10-15 **停机补偿已正式接入并归档，19/19**：备份后加法迁移catchup000001；恢复先补采结案，再生成未开始的当天选题，断点/预算/历史缺口可见。41既有检查、Web/bundle/Ruff、独立复核、隔离真实模型与Beat/Worker停启、正式恢复及API/UI通过。原角色/今日10条/评估/创作记录保全，临时服务已关闭；代码未提交或push，原次日自然日批验收独立继续。[成果与回执](openspec/changes/archive/2026-10-15-add-discovery-offline-catchup/README.md)。

2026-10-15 **手动来源管理已接入并归档，16/16**：「内容机会→信息源储备」可添加新闻/RSS/博主链接、选择多个角色并统一配置自动来源。人工设置保留、后台验证、失败原因可见；81既有检查、Web构建和独立复核通过，隔离真实Beat/Worker日批从手动来源生成1条。正式未加入验收数据，原5条建议/历史保全；原每日选题明日自然验收继续。[使用与回执](openspec/changes/archive/2026-10-15-add-manual-discovery-source-management/README.md)。

2026-10-15 **每日选题质量修复已正式接入，43/45**：已备份；今日保留科技2条常青、生活3条建议，其余3备选/1合并/1缺正文暂缓，历史评估保留。正文、三类日期、同类合并、来源分散与每角色0至5条检查已接通；81既有检查、Web构建、独立复核和两个角色隔离真实模型链通过。明日08:20继续自然日批验收，通过后同步规范并归档。[同一成果](openspec/changes/add-daily-persona-content-opportunities/README.md)。

2026-10-15 **每日角色机会与商品创作已正式启用，40/42**：先完成DB/75素材/config备份，再迁移discovery000001；91旧表858行与18素材引用保全。科技/生活角色已启用现有MiniMax MCP自动搜源和荐题，今天已各生成5条；商品入口共用原Recipe。正式5173/8000健康、160检查通过/1跳过；明日08:20复核自然日批；本次10条质量审查发现缺陷，关闭质量问题后才同步主规范并归档。[正式进度与回执](openspec/changes/add-daily-persona-content-opportunities/README.md)。

2026-10-15 **今日工作台测试内容已重置**：经用户确认，6个测试项目已归档保留全部内容，172条测试活动及6条归档活动在完整SQLite备份后移除；首页7个列表API回读均为空且无投影错误。角色、账号、模板、模型配置及其他业务表逐表一致。内容机会原本为人工入口；现有定时任务未接每日机会生成，旧FactPack荐题也未写入该模块。本轮未改产品代码或启用调度。[重置与诊断记录](backups/workbench-reset-20261015/README.md)（本地私有备份，Git忽略）。

2026-10-15 **网页视频与有声样片验收完成**：图片先确认、据图提示词、人工Grok/Gemini回传、平台CLI/MCP、达芬奇主剪与AE合成已跑通；60秒科技音色旁白/字幕/原生工程通过独立AI评审，Master46/执行8本地采用；公开门禁保持，未直接试听。29/29已归档，31路径选择性本地集成，正式发布未声明、未push。[同一成果](openspec/changes/archive/2026-10-15-verify-grok-gemini-media-capabilities/README.md)。

2026-10-15 **Obsidian本地只读知识与风格接入完成，14/14**：正常“来源与证据”可检索已保存笔记、选连续片段、分别指定专业参考/风格样本与Persona范围、明确模型授权；Run冻结和真实预览/生成/精修已接通。两个角色正常页各初稿+精修，Master35/37，独立AI质量通过；181既有回归、Web/TypeScript/bundle与strict通过。加法迁移obsidian000001，968旧业务行/75媒体/477归档/相邻修改保全；未安装MCP、不写Obsidian、不push或公开发布。[入口、步骤与完整回执](openspec/changes/archive/2026-10-15-add-obsidian-knowledge-context/README.md)。

2026-10-14 **两角色日常生产已完成，18/18**：正常页面六链真实完成并刷新，两篇文章、六张1080×1440 PNG、两段完整音频159.679/129.226秒已正式保存；真实音色/Recipe/事实权限齐备。独立AI全模态评审接受，SEO/视觉语义提醒和未直接试听边界保留。四文件最小修复、19既有检查及Web/FE-P1通过，strict43/43；482旧行/53旧素材/三归档/相邻修改保全。已归档并选择性本地提交，未push或公开发布。[直接使用与完整回执](openspec/changes/archive/2026-10-14-enable-two-persona-daily-production/README.md)。

2026-10-14 **两个相邻change独立收尾完成**：Persona156/156、Creation Recipe144/144均已归档并同步canonical；Persona六张修订默认图卡及原件/音频经委托AI独立复核通过，Recipe补齐66持久案例并修复两项真实缺陷。实际候选2670通过/28跳过/1既有wewrite环境豁免，最终OpenSpec strict42/42；正常UI创建/继承/Preview与已有结果审阅已核对，正式8000/5173可达。未直接试听，日常仍需有效证据、素材权限及Audio Recipe/voice ID；未push/公开发布，相邻修改保留。[Persona成果](openspec/changes/archive/2026-10-14-add-persona-creative-studio/README.md) · [Recipe成果](openspec/changes/archive/2026-10-14-creation-recipe-stage-control-loop/README.md)。以下旧阶段状态保留历史。

2026-10-14 **Creation Recipe独立收尾完成，144/144**：66新增持久案例、非法反馈ID及合法Descriptor冻结深度两项最小修复通过独立复核；实际候选2670通过/28跳过/1既有wewrite环境豁免，Web/FE-P1/Ruff/strict通过。9capability32新增同步并归档，仅本轮7代码路径选择性本地提交，相邻plugin/Studio改动保全；Persona默认图卡质量修复独立进行中，未push/公开发布。[Recipe成果](openspec/changes/archive/2026-10-14-creation-recipe-stage-control-loop/README.md)。

2026-10-14 **十二平台/十七形态交付已验收并归档，43/43**：事实边界、图文平台检查及用户委托的AI整模态评审通过。七capability同步23新增/2修改，选择性本地main提交保全相邻改动；2639后端通过/28跳过/1既有wewrite环境豁免，实际候选368通过/1跳过、Web/FE-P1/Node/Ruff与独立复核通过。未直接试听、push或公开发布；相邻Persona151/156、Stage141/144保持。[成果与精确边界](openspec/changes/archive/2026-10-14-complete-multiplatform-content-handoff/README.md)。以下保留阶段历史。

2026-10-14 **正式12平台/17形态Profile已启用，40/43**：全权授权后完成配套备份/dry-run/幂等启用、四账号独立真实ZIP、三项缺陷修复与独立复核。后端2626通过/28跳过/1已知环境失败豁免，Web/FE-P1/strict/Ruff/diff通过。两个角色新增2文章/6PNG/2WAV与QC回执；完整质量仍有事实边界、平台inline媒体和人工评审门槛，7.1/7.2及最终生命周期3.1未关闭，不冒称归档或发布。必要API已加载ready=true；无新迁移/产品依赖或运行配置改动，用户Vite/worker未动。[当前成果与下一步](openspec/changes/archive/2026-10-14-complete-multiplatform-content-handoff/README.md)。下方均保留为历史。

2026-10-14 **Batch B已实施，33/43，等待独立最终验收**：12平台/17形态合同、服务端Descriptor编辑、目标账号精确冻结与独立交付、安全本地ZIP均在本地落地。17 API/ZIP、17生产页＋17Review/页面下载通过；后端2624 passed/28 skipped/1既有wewrite断链失败如实豁免，Web/8项编辑模型/FE-P1、strict38/38与diff通过。正式Profile启用、真实模型质量/公开发布与生命周期仍待独立授权/验收；没有正式库/Profile/素材/配置/服务或Git生命周期操作。本批零迁移/新增产品依赖，沿用现有启动方式。[当前成果与下一步](openspec/changes/archive/2026-10-14-complete-multiplatform-content-handoff/README.md)。下方早期状态均保留为历史。

# AI Content Studio（AI 内容生产中心）

2026-10-09网页可达性恢复：5173原无监听，现已沿用原npm/Vite入口启动，仅`127.0.0.1:5173`；主页/前端入口HTTP200，`/api`代理ready=true，API/Worker未重启。Web仍是前台运行方式，不是登录自启；日常命令和停止方式见[本机运行手册](openspec/docs/项目文档/runbooks/production-readiness.md)。无业务代码、数据库/素材、运行配置、依赖或迁移变更；未调用模型或新增部署体系。浏览器可视化未由此次HTTP检查替代。

当前执行口径：WeWrite Skill安装/测试不纳入本轮，不阻塞使用；不再重复跑它或完整回归。`add-persona-creative-studio`功能实施项已完成，剩5项为人工质量/独立复核及另行授权生命周期；不把“暂缓验收”记成“已通过”。两角色文字、图文、音频与配置入口沿用当前版本，公众号适配器和运行配置不因此改动。

集中验收入口：[两个角色的文字、六张图卡、两段完整音频与安全回执](/Users/mshengran/Project/AIContentStudio/backups/persona-review-20261009.O02VLb/README.md)。已保存原件精确副本；最新隔离后端2528 passed/12 skipped、Web/FE-P1与Ruff通过（旧插件测试的临时Skill元数据前提见[回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)）。不再调用模型；人工试听/全模态质量、独立复核与单独授权生命周期仍待，151/156不变。此目录被Git忽略，应纳入本机备份；依赖、正式数据与现有启动方式不变。

2026-10-09 **当前151/156、5开放；两个角色完整真实音频均已走通**。用户恢复Gemini出口后，新隔离生活Run9完成口语/声音规划→MiniMax→246.535秒WAV→受限素材接受→QC pass/零问题；20.4关闭。CPA2/MiniMax1、串行/间隔≥10秒/应用零重试，旧Unknown不重发。正式5,170行/70素材/配置保持，服务继续启用；只剩人听/全模态rubric、独立质量及单独授权生命周期，不冒称整体关单。目录/依赖/启动不变。[真实产物与回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下为历史检查点。

2026-10-09 **完整Audio仍受外部出口阻断，自动试验停止**：第三轮live路由/CPA配置仍一致，两个旧Unknown与停止的验收服务保留；无活生成句柄、新模型调用或VPN修改。149/156、7开放及360秒配置保持，不冒称全部完成；新版API/Web/Worker继续启用、不回滚正式库。待CPA专用出站修复/新有界批次方向确认或外部状态变化后恢复。目录、依赖与启动不变，[完整证据](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-09 **失败代理出口已只读确权**：live Clash选择HTTP-72.245.152.14，Google连接日志明确记录该peer reset；磁盘Google规则不等于live生效，日本节点只有旧health记录。未切换全局代理/改VPN、未调用模型，149/156及360秒设置保持；下一步是CPA专用出站路线修复的范围选择，不是再测同一Unknown。目录/依赖/启动不变，[当前证据](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-09 **音频阻断已定位到CPA→Google出口**：原两失败窗口的网关请求最终500/上游EOF，一次无认证、零重试连通性检查也在TLS握手失败；不是360秒音频上限或120秒等待错误，MiniMax未进入。仅安全日志诊断，旧Unknown/正式配置/服务/VPN不改，无新模型调用；149/156、7项仍开放。目录、依赖与启动方式不变，[证据及限制](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)已记录。

2026-10-09 **生活图文真实成品链已补齐**：实物审计发现旧功能副本封面为测试色块；新独立副本复用已有MiniMax真实图，三个1080×1440 PNG→显式接受→Master15→渲染/结构/权利检查通过。原记录保留、零模型调用/正式写入，文字hash与既有批准一致；固定视觉自评及Mock语义警告如实记录，仍149/156，完整Audio/全模态人审与独立质量未关闭。目录、依赖和启动方式不变。[产物和回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-09 **360秒音频配置再次只读确认**：运行中正式API返回routing revision9、TTS成品上限360秒、接口等待上限120秒、273音色；新内置Audio模板为360秒，历史Workflow/Run不回填。本次核验未调用模型、改配置或重发任务。目录、依赖和启动方式不变，整体仍149/156；音频成品/人工听感不由时长配置代替。[完整回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-09 **多媒体持久覆盖已补齐，当前149/156、7开放**：只在两个既有测试文件新增33用例，覆盖图片1–4候选、精确选择入库/历史候选保全/不改Master、音色scope/目录刷新/CAS失效及签名/字节完整性。集中离线236passed/1既有warning（5.29秒），两项保护旁路验证按预期失败，Ruff/strict38/38/diff通过。正式360秒配置保留，未调用模型、重发Unknown、改正式数据/服务或做归档提交。完整Audio、人审和独立质量仍待。目录、依赖、启动方式不变；[完整回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下为历史检查点。

2026-10-09 **音频上限已按用户要求设置360秒**：正式routing revision8→9，仅改TTS成品时长上限；120秒接口等待、273音色及其他完整模型配置保全。新内置Audio Recipe模板同步360秒，旧Workflow/Run不改；104项Audio回归、Ruff及正式两角色模板checksum回读通过，API已加载，Worker不变。新完整Audio批首个CPA口语改编无响应/Unknown，已停止，实际CPA1次、MiniMax0次；未重发，完整Audio和人听不冒称通过。当前148/156、8开放。目录、依赖与现有启动方式不变，备份和证据见[回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。下文为历史检查点。

2026-10-09 **已授权 MiniMax 真实音色样本，部分通过**：生活指定 `chunzhen_xuedi`/`speech-2.8-hd` 的 3.62 秒真实 WAV 已接受为正式 MaterialRevision 7，并通过字节/hash、签名 voice/rate、当前绑定及 Audio QC；科技样本首发 422、现为 Unknown，不重发。两条均仅实际合成一次，无 CPA/公开发布/自动改 Master。完整 Audio Recipe 和人听仍待验收，当前 **148/156，8 项开放**。本轮持久覆盖审计确认 Audio 回执用例已有，图片 batch/候选选择与音色目录回归仍缺，不用旧总数虚关 13.6；目录/依赖/启动不变。[真实回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)记录正确素材根、配套备份、旧行保全及覆盖缺口。下面是历史检查点。

2026-10-09 **MiniMax 多候选图片配置已补齐**：正式模型路由 revision 8 将 `image_generation.max_items` 从 1 调整为 4；image/TTS/ASR 的本地执行计划均可解析。这里只完成配置与只读能力核验，没有调用供应商、自动选音色或写入素材。当前 OpenSpec 记账 **148/156，8 项开放**；真实音频质量、人审、持久覆盖和生命周期仍按任务清单独立验收。

集中离线冒烟已通过：Persona/Graphic/Audio/Stage/model routing 既有回归 **570 passed / 1 existing warning**；使用 Mock/隔离 SQLite，不代表真实 TTS 或人工质量验收。

2026-10-09 **图文功能链已隔离收口，音频合同烟测通过**：科技 Persona 与生活 Persona 均完成精确素材引用、确定性排版、三张真实 PNG、产品接受、append-only Graphic Master、render attestation 和当前结构/平台/render 检查；Audio/Stage 回归本轮211项通过、8个既有warning，正常页面隔离链覆盖两种 Persona，但使用合成音调夹具。此处只代表功能链通过；真实 TTS、人审质量与生命周期仍未完成。当前 OpenSpec 记账 **148/156，8 项开放**；正式 SQLite/素材/配置未被隔离验收改动。详见[图文音频验收回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

2026-10-09 **使用配置已授权补齐并即时生效**：正式routing revision5→7；chat为8192输出tokens、最多3候选、120秒等待，MiniMax音色目录一次同步273项。两个角色文字配置均ready，实际页面音色搜索可用；未自动选声或生成内容。API/Key/默认Gemini、旧媒体限额、5,162条其他数据库行、67素材文件及runtime.env保持不变。配置回执本身不等于全部质量验收；当前总进度以顶部148/156为准。详见[启用与配置回执](openspec/docs/项目文档/PERSONA_CREATIVE_FRAMEWORK_HANDOFF_2026-10-08.md)。以下均为历史检查点。

2026-10-09 **本机初始化已完成，146/156，10项开放**：配套SQLite/素材备份后刷新原API/Worker，正式新增科技Persona2、生活Persona3及各自3个默认Workflow，重复初始化无覆盖。5,147旧行、67素材文件/运行配置hash不变，schema仍crs000000001；[角色与配置页](http://127.0.0.1:5173/identities)和生产/媒体入口实际可见，API ready=true。**尚需补使用配置**：正式chat调用限额缺失、Audio未选voice ID；image1张/TTS10秒等原限额未扩，不能把页面可用当成全部生成已就绪。未调用模型、迁移、归档提交推送或追加全量/审美验收。目录/依赖/启动方式不变，详见[启用与备份回执](openspec/docs/项目文档/PERSONA_CREATIVE_FRAMEWORK_HANDOFF_2026-10-08.md)及[进度](openspec/changes/add-persona-creative-studio/progress.md)。以下均为历史检查点。

当前 **144/156，剩12项**。生活混合卡片方向已明确并落地：暖杂志封面带精确图片、正文可纯文字；Preview、排版和结构QC统一。既有生活计划已生成三张真实1080×1440 PNG预览，未自动接受成品或修改正式库。离线校验及新鲜全量回归 **2495通过/12跳过/80既有警告，142.91秒、exit0**；Ruff/strict38/38/diff通过，Web未改/未重跑。未追加模型调用、依赖/迁移、永久测试或生命周期操作，目录/启动方式不变。[预览与完整验收边界](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下为历史检查点，未答复方向/blocked文案不再代表本项当前状态。

当前 **144/156，剩12项**。已批准的新120秒图文批次实际CPA3/3、MiniMax2/2全部返回；两个JPEG和科技默认流程的三张1080×1440中文字卡已生成。科技链路已到隔离Master/真实renderer，但素材接受、context/evidence、完整GraphicQC与人工质量未完；生活规划因自动续行占用额度尚未完成，不追加调用或虚关19.3/20.3。本轮只改验收脚本/回执，无业务源文件、音频、正式SQLite/素材/配置/服务、依赖/迁移或生命周期变化；目录和启动方式不变。[真实产物与限制](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下均为前序检查点。

当前 **144/156，剩12项**。图片/TTS已精确消费冻结等待参数；进一步修正普通Audio v4 Stage的独立25秒上限，使合同与服务统一为既有1–300秒，默认25秒不变，正式120秒策略仍优先阻断超限请求。最新21项临时离线冒烟、六组已有回归 **475 passed/8 warnings（15.20s、exit0）**、app Ruff、strict38/38、diff通过。前序全量2495passed与Web build保留为历史证据，本次未重跑。未调用模型、写正式库/配置、重启服务、新增永久测试或归档提交；真实图文/音频、13.6、正式初始化及生命周期仍待。目录/依赖/启动不变。[当前回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。

以下是前序批次记录；“仅验收脚本25秒”由上面的产品执行层诊断补充纠正。

当前 **144/156，剩12项**。新授权图文批次实际调用CPA 1/4、MiniMax 2/2：科技视觉规划和一张1152×864 JPEG返回，生活图片在本批25秒等待上限后为Unknown，无原任务句柄；后续调用已停止，不重发。完整默认图文/人审未通过，剩余CPA额度不因存在而继续派发。正式SQLite/素材/模型配置/服务及依赖、启动方式不变；详见[本批回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。下面等待授权及门禁记录均为前序历史。

本轮最新集中门禁：**2495 passed /12 skipped /80 warnings**，134.01秒、exit0；显式已有本机renderer后原16项条件跳过实际运行，无新增测试。当前Web TypeScript/Vite/FE-P1、app Ruff、strict38/38和diff通过；手动生图面板仍在五个日常入口初始静态图之外。进度保持144/156，真实图文/音频验收、13.6、初始化及生命周期不因绿灯关闭；四次MiniMax预算不重置，不重复Provider请求或同一批门禁。正式目录、依赖、启动与服务不变，详见下面同一回执的最新集中门禁节。

2026-10-08 **当前144/156，剩12项**。后续多平台规格已统一真实`stage.variant.adapt@1`及未来持久覆盖计划，仅关闭Persona前置0.3/0.4，不启动多平台业务、不解除当前新测试写入限制。现有composer＋本机headless renderer实际生成两张1080×1440中文PNG，视觉检查无明显溢出；已有图文/渲染/API回归223passed/1warning、strict38/38、diff通过。手工卡片计划不冒称默认Persona完整图文验收；四次MiniMax调用预算耗尽，无新模型调用、正式数据/配置/服务或依赖/迁移变化。真实图文/音频、人工rubric、持久覆盖13.6、正式初始化及生命周期仍待；目录和启动方式不变。[当前回执与产物](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。以下142/156等均为历史检查点。

2026-10-08 **已登记MiniMax真实生成批结束，当前142/156、剩14项**。隔离环境四次调用，返回两张JPEG和一份3.70秒WAV；科技图有乱码未通过成品检查，原科技音频超限保持Unknown且不重发。修复本机CLI帮助输出stderr导致音色参数误阻断，已有165项回归与Ruff通过。只关闭本批真实调用授权21.2，不把原始媒体样本当完整Persona图文/音频或人工质量验收；正式数据、配置和服务未改，无新增依赖/表/迁移/永久测试。图文确定性排版/真实PNG、音频Stage/QC与人听验收、正式初始化和生命周期仍待，启动方式不变。详见[有界真实调用回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。下面141/156等为历史检查点。

2026-10-08 **CPA图片协议与ChatGPT手动生图已实施，当前141/156、剩15项**。CPA图片仅引用已登记的 `openai.compatible` provider/model/profile 与 image binding，使用 `cpa.images.b64.v1`、1–4个候选、严格字节校验和现有MaterialRevision接受链；未知网络结果不自动重试，不探测端点，不偷偷换Provider。ChatGPT仍是提示词复制→用户自行生成/下载→拖入或选择→明确接受入库，不读取Cookie、不调用ChatGPT或自动改Master。零新依赖/表/迁移、未改正式配置/素材库/服务；本轮为合成协议/一次性SQLite烟测，未宣称真实CPA图片质量。真实Graphic/Audio验收、初始化/持久覆盖/生命周期仍待完成，未提交归档推送。详细[实施回执](openspec/changes/add-persona-creative-studio/progress.md)。

2026-10-08 **ChatGPT手动生图已实施，当前140/156、剩16项**。入口：素材与知识→生成素材预览与接受→ChatGPT（手动生图）。完整提示词复制→用户自行生成/下载→拖入或选择原图立即暂存→逐张预览/选择→明确接受入库；不会读取Cookie、调用ChatGPT或自动改Master。零新依赖/表/迁移，启动与正式SQLite/素材库/配置/服务不变。既有后端2479 passed/28 skipped、Web/FE-P1、Ruff、strict38/38及隔离合同冒烟通过；测试图不冒称真实创作质量。CPA10.11、真实Graphic/Audio验收、初始化/持久覆盖/生命周期仍待完成，未提交归档推送。详细[实施回执](openspec/changes/add-persona-creative-studio/progress.md)。下方139/156及“未apply”属于本项历史阶段。

2026-10-08 **ChatGPT改为人工生图交接，设计已确认、业务未apply**：前端选择ChatGPT后提供完整提示词/一键复制和图片拖拽上传；拖入立即进入临时候选区，预览选择并明确接受后才成为MaterialRevision，Master另行绑定。取消浏览器Agent/Cookie/session依赖与自动提交/下载，不伪造网站模型回执。同一OpenSpec已同步，仍139/156、17开放；目录、依赖/启动与正式运行环境不变。[当前进度](openspec/changes/add-persona-creative-studio/progress.md)。下面Chrome/blocked记录是历史。

2026-10-08 用户已确认复用Chrome现有ChatGPT登录，页面只读确认可用；Cookie留在浏览器，不导出、不保存为模型Key。会话选择已明确，但网站生成/回传/人工入库尚未验证，仍139/156、17开放。无业务代码、依赖/迁移、正式配置或启动方式变化；下面blocked是回答前的历史，见[当前回执](openspec/changes/add-persona-creative-studio/progress.md)。

2026-10-08 自动续行已停止等待人工信息，当前139/156、17项开放；不是全需求完成，也未关闭本机API/Web。CPA图片协议和ChatGPT浏览器会话尚未明确，其余真实质量/正式初始化/生命周期边界保留。无新业务改动、依赖、迁移、配置或启动方式变化，详见当前[进度](openspec/changes/add-persona-creative-studio/progress.md)。

2026-10-08 **范围补齐：139/156，17项开放**。CPA Gemini/Grok生图与ChatGPT网页生图已作为本次统一多媒体需求的两项未完成任务写回OpenSpec，不能用MiniMax已实施代替它们。当前本机只读设置回读revision5：Gemini/Grok仅声明chat、image binding缺失；MiniMax图片配置存在但运行投影为credential_continuity_unverified，尚不能声称正式生成链可执行。未调用真实Provider或修改正式配置/服务。ChatGPT浏览器会话及CPA exact图片协议待确认/复核；本轮只修规格和回执，目录/依赖/启动方式不变，未归档提交。[当前进度](openspec/changes/add-persona-creative-studio/progress.md)。以下139/154是前批历史检查点。

2026-10-08 **图片＋音频配置批已实施，Persona OpenSpec 139/154，剩15项**。图片支持 MiniMax 原生1–4候选、逐张校验预览、明确选一后入库；音色支持本地目录搜索/语言/收藏、克隆Voice ID登记、已有素材试听以及Persona/Account/Series精确绑定。普通/高级设置只发送适配器声明支持的参数，配置失效时停止、不换模型。新增共享组件 `apps/web/src/product/VoicePresetPicker.tsx`，没有新依赖/表/迁移，正式启动方式不变。后端2479通过/28跳过、Web/FE-P1、Ruff、strict38/38和六项隔离页面冒烟通过；真实Provider调用0，未改正式库/配置/服务。新增持久回归13.6、真实Graphic/Audio质量、初始化及归档仍待完成；Gemini/Grok/ChatGPT网页生图不冒称已接入。[当前完整回执](openspec/changes/add-persona-creative-studio/progress.md)。以下133/147等为历史检查点。

2026-10-08 当前133/147：科技文字样稿与生活文字编辑稿已获用户人工接受；生活编辑候选仍只作为隔离验收证据，不覆盖原Master/Candidate/ZIP，也不冒充新的模型直出。两个角色文字流程框架已串通；图文、音频真实成品验收与正式Persona初始化仍分开，后续在程序内继续调整。原流水线/ZIP/SQLite/回执和正式配置保留，零新增模型调用；[文字回执](openspec/docs/项目文档/PERSONA_TEXT_FINAL_REVIEW_2026-10-08.md)记录样本边界。功能目录、依赖/启动不变，不提交归档推送。

2026-10-08 **两个角色真实文字流程已串通，当前133/147、剩14**。科技稿Master5（真实流程祖先＋明确编辑）、生活稿新Run4九阶段/三版Master均经当前checks→Candidate v4→Approval→本地ZIP；精确引用、冻结正文/ZIP/hash和SQLite回读通过。本批17/30次Gemini请求，实际并发1、启动最短间隔10.0008075秒，零应用重试/fallback/旧Unknown重发，正式库/配置/服务不变，自有验收API18337已停。仅关闭19.2/20.2，**人工稿件质量与独立最终复核仍待完成**，Graphic/Audio没有启动；[完整回执](openspec/docs/项目文档/PERSONA_TEXT_REAL_ACCEPTANCE.md)。目录、依赖和正式启动方式不变，无提交/归档/推送。下方131/147及“新检查缺失”是之前的检查点。

2026-10-08 **科技编辑稿已接回新隔离Master4，整体仍131/147**。复用现有保存服务追加user_edit/parent3，七条精确证据引用与渲染正文一致，幂等/刷新/历史行保全通过；缺少新检查时冻结正确409阻断。原停止批次/Master/Candidate/ZIP不覆盖，不冒称双角色Text或全模态验收通过。[稿件](openspec/docs/项目文档/PERSONA_TECH_TEXT_EDITORIAL_2026-10-07.md)与[回执](openspec/docs/项目文档/PERSONA_TECH_TEXT_EDITORIAL_REVIEW_2026-10-07.md)保留；限定独立APPROVE_ISOLATED_ADOPTION、strict38/38/diff通过。零CPA/正式写入，现有产品目录、依赖和启动方式不变。

2026-10-07 **验收批次调度参数已确认并离线落实：最多3在途、请求启动间隔至少10秒**。仅私有验收调度器，7项离线检查/Ruff通过、默认真实调用预算0；不是产品/CPA全局限流，未启动模型调用或改正式配置/库/运行方式。当前131/147，真实Text→Graphic→Audio仍分别验收；旧Unknown保持，完整[回执](openspec/docs/项目文档/PERSONA_TEXT_REAL_ACCEPTANCE.md)。

## 2026-10-07 真实Text质量→精修交接修正

实际隔离数据修前186597bytes超过128KiB；修后129061bytes且完整resolution可canonicalize。仅传精确CheckRun ID/input hash/status/full-report hash及必要问题/coverage；完整报告留在immutable源头，原live/currentness/人工warning处置不变。科技初稿已明确编辑保存，实际fact/identity完成，正在同批继续精修；347既有回归通过/8warnings/13.46s，130/147暂不改变。未新增持久测试或放宽大小/调用限制；当前真实质量尚未终验。

2026-10-07 **新一批双Persona真实文字验收已获明确授权并开始**：最多30次应用模型请求，首次计入单请求总尝试≤5；Unknown立即停止，不重发旧Unknown。仅fresh隔离SQLite/素材，不做正式初始化、图文、音频、发布或生命周期动作。此前blocked文案是未执行的状态计划：授权先到，goal实际仍active。130/147保持，真实质量以本批产物验收为准。

2026-10-07 **8项持久测试已补齐并独立复核通过，当前130/147、剩17**。仅关闭3.7/4.6/18.1–18.3/18.7–18.9，最新集中568项通过；落库默认模态集合与幂等绑定的漏项已补强、反例正确被拒绝。使用隔离SQLite、Mock和合成PNG/WAV；真实文字→图文→音频质量仍分别待验收。目录新增三个聚焦测试文件，扩展既有Persona测试；依赖/正式启动不变。本轮零CPA/真实Provider/ASR推理、正式数据/配置/服务或生命周期动作。下方122/147与“等待授权/复核”是历史，最终全量回执见[本轮进度](openspec/changes/add-persona-creative-studio/progress.md)。

后续自动续行只读确认旧真实Text的两项Unknown未变、零Master、原证据hash保持且临时验收API已停止；新批次调用授权连续三轮未获答复，自动目标转blocked等待人工回答，不再重复跑检查，也不自动访问CPA或重发。目录/依赖/正式启动方式保持，130/147不虚增，完整目标保留；见同一进度回执。

2026-10-07 **Persona仍122/147，等待8项持久测试写入例外确认**。同一权限冲突连续三轮未获答复，现有测试/进程复核未提供可替代覆盖；停止重复自动检查，不把早前199项绿灯当新进展。允许例外后继续补齐并集中验证，随后分别验收真实文字、图文、音频；目标范围不缩小。目录、依赖/启动、正式库/服务及CPA不变，无新业务代码/测试/调用/提交归档，见[阻塞审计](openspec/docs/progress.md)。

2026-10-07 **集中已有合同回归199通过，仍122/147、25开放**。当前任务/计划摘要已纠正旧121/26和95/52数字；历史全量/浏览器结果未冒充本次证据。8项永久测试与后来的“不新增测试代码”要求存在冲突，已提一个明确例外问题，答复前不写新测试。真实文字→图文→音频仍分别验收，199Mock/隔离SQLite回归不证明成品质量。目录、依赖/启动不变，本轮不访问CPA、不改正式库/服务或旧Unknown、不提交归档；见[当前精确进度](openspec/changes/add-persona-creative-studio/progress.md)。

2026-10-07 **CPA总尝试上限已落实并热加载**。首次计入用户最多5次的限制；当前采用保守配置：无额外重试轮次、单轮最多2个凭据，普通失败最多2次生成尝试，即使401刷新补发也最多4次，不为了凑满5次继续调用。禁用stream bootstrap重试和credits兜底；15:58:28运行日志确认加载，PID700未重启，原配置已0600备份。其他配置、VPN、URL/Key、正式库及旧Unknown未改，本轮零模型调用；固定频率间隔没有新增，网络/真实质量不冒称修复。122/147保持，目录、依赖、启动方式不变，完整[回执](openspec/docs/项目文档/PERSONA_TEXT_REAL_ACCEPTANCE.md)。下方未修改CPA配置的说法属于实施前历史。

2026-10-07 **CPA初稿出站故障进一步定位，仍122/147、8/30调用**：原失败窗口Clash记录147条当前HTTP出口主动reset；CPA v8代理端口本身正确，不应盲改。日本既有节点Google探针通过，香港节点超时；当前出口也曾恢复HEAD404，但不等于稳定生成或已修复。未改VPN选择/配置/服务或重发Unknown；只让CPA的Google流量使用专用路由需先确认策略，其他软件出口保持。依赖/启动方式不变，完整[回执](openspec/docs/项目文档/PERSONA_TEXT_REAL_ACCEPTANCE.md)，真实质量仍PARTIAL。

2026-10-07 **真实默认Text新验收批次PARTIAL，仍122/147、剩25**。用户新授权最多30次文字调用，本批使用8次：科技/生活两角色研究→角度→大纲六个真实结果已逐项接受；各自默认三候选初稿均未收到可用响应，Attempt7/8保留Unknown，不重发、不换模型。前后CPA认证发现均200/32模型，不能据此宣布生成或质量通过；本批零Master/Candidate/交付，正式模型配置hash不变，自有临时API已停。依赖/正式启动/目录不变，无业务代码、新永久测试、Graphic/Audio、正式数据或生命周期操作。完整[本轮真实文字回执](openspec/docs/项目文档/PERSONA_TEXT_REAL_ACCEPTANCE.md)；下方页面合同PASS不替代真实质量。

2026-10-07 **当前122/147，剩25：Video普通页面交接验收完成**。两角色从内置初始化→默认四阶段→脚本/镜头明确接受→Video Master→导演包明确接受/刷新，21检查点通过、零页面脚本错误；隔离库验证2Master/2Package、零外部执行/素材/候选，关闭19.5。Mock不证明创作质量，独立窄review无新结论；下方121/147与“没有页面验收”为前批历史。本批只更新证据和任务，不新增业务代码/永久测试/真实调用，不改正式库/配置/服务或启动依赖，不提交归档。见[集中回执](openspec/docs/项目文档/PERSONA_NORMAL_PAGE_CONTRACT_ACCEPTANCE.md)。

2026-10-07 **Video导演包合同补验，仍121/147、剩26**：两个角色默认脚本→镜头→Video Master→Director包隔离API37点通过；修正9:16与[9,16]匹配误阻断，不改Master或派发外部执行。新鲜相关233测试、Ruff、strict38/38及diff-check通过；下方1968/full和Web属于6.4前批。独立窄review额度耗尽未返回结论，19.5不提前关闭；Mock不是真实质量，也没有新的Video普通页面验收。正式数据/配置/服务、目录/依赖/启动方式均不变，无永久新测试、真实调用或生命周期动作。见[精确回执](openspec/changes/add-persona-creative-studio/progress.md)。

2026-10-07 **当前121/147，剩26：6.4已验证收口，独立复核APPROVE**。确定性组合参数按“Persona方法默认→Project设置→Run调整”消费；最终方法/output/Director package一起校验，禁止selector补丁偷换执行器，跨模态就绪与执行一致。实际内存服务链22检查点、修后全量1968/28skip（102.20s）、Web/FE-P1、全appRuff、strict38/38和空白检查通过。剩余永久覆盖、真实成品质量、正式初始化/生命周期及历史依赖未冒称完成。正式数据/配置/服务、真实调用和提交归档均未动；目录、依赖和启动方式不变。完整[本批回执](openspec/changes/add-persona-creative-studio/progress.md)，下方120/147和6.4待答均为前序历史。

## 10月7日前序记录

2026-10-07 **Persona120/147，剩27：整体安全与普通页面产品/UX均独立通过**。两个角色Graphic10点、Audio22点合同闭环（试听→明确Material接受→QC→估算SRT）已完成；Text沿用既有24点证据。整体复核新增的Master回执额外字段及中间素材实时权利缺口已最小修正，34项临时红绿检查通过，原reviewer完整22.4重审APPROVE；22.5亦APPROVE。上轮修后1968passed/28skipped（104.40s）、Web/FE-P1、Ruff/strict38/38及空白检查通过；本次只读剩余范围核验，没有重跑全量或新业务变化。不冒充真实质量、ASR或全规格完成；6.4仍待答，永久覆盖/真实成品/正式初始化/生命周期仍开放。正式库/角色/配置/服务未动，临时18331/15331已停止。完整[集中回执](openspec/docs/项目文档/PERSONA_NORMAL_PAGE_CONTRACT_ACCEPTANCE.md)及[剩余范围核验](openspec/changes/add-persona-creative-studio/findings.md)，目录、依赖/启动方式不变；下方118/147为历史。

2026-10-07 **整体复核补充4处修复，仍118/147**：Variant Stage安全回执、Quality模态匹配、创作配置权限/祖先归档、音频QC/素材指引已最小修正。69项后端临时检查、六组UI场景及原15项状态检查通过；最新全量1968passed/28skipped、Web/FE-P1、Ruff与strict38/38通过。限定backend复核APPROVE，但whole22.4/22.5和真实创作质量仍分开验收；完整证据见[最新回执](openspec/changes/add-persona-creative-studio/progress.md)。目录、依赖、启动方式不变，正式库/配置/服务及生命周期未动。
2026-10-07 **五处复核缺陷已修正，限定安全/UX独立复核通过**：完整创作配置安全校验、现代Stage先校验后记安全回执、只读入口不自动建号、精确身份/请求代次保护、跨形态草稿与保存结果核对。41项隔离安全检查、15项隔离UI状态检查、两个角色24点Text→本地ZIP合同冒烟和最新Web/FE-P1通过；最终全量门禁见[本批回执](openspec/changes/add-persona-creative-studio/progress.md)。目录、依赖及启动方式不变，不改正式库/配置/服务、不做真实模型调用或提交归档。整体仍118/147，限定修复批准不替代whole22.4/22.5、真实成品质量或6.4待决边界。

2026-10-07 **Persona自动浏览器验收入口已修正并复验**：用户手动Chrome正常；脚本优先复用本机已有headless browser，保留显式选择、不修改日常Chrome资料或安装新依赖。两个角色Text→Master→Candidate/Review→本地ZIP重新24检查点通过、零页面脚本错误；临时Mock库/服务已停止，正式服务与数据未动。整体仍118/147，不等于真实创作质量全部验收；范围、启动依赖和证据见[文字合同验收](openspec/docs/项目文档/PERSONA_TEXT_CONTRACT_ACCEPTANCE.md)。

2026-10-07 **Persona当前118/147，剩29项，尚未全部完成**：两个默认图文流程已通过隔离SQLite/Mock规划、确定性排版、真实1080×1440 PNG、显式素材接受/新Master保存、QC/可冻结；限定独立复核同意关闭10.1/10.2、17.3及6.6路由修正。已补组合路由与逐方法反馈，182项既有定向回归、Web/FE-P1、Ruff及strict38/38通过；全量结果见[当前进度](openspec/changes/add-persona-creative-studio/progress.md)。非AI组合消费边界待一次选择，真实文字/图文/音频质量仍单独验收。没有正式库/配置/服务变更、付费Provider调用、新依赖或迁移，也未提交归档；日常Chrome崩溃未宣称修复，图文使用现有headless renderer。

## 10月6–7日前序批次历史（当前以顶部和进度文档为准）

2026-10-07 **Persona OpenSpec仍99/147、剩48，未全部完成**：最新接通Chat Stage/Run精确模型覆盖和Graphic Recipe内既有素材准备入口，两处连续操作问题已修正、独立定向复核APPROVE。新鲜165项既有回归、Web/FE-P1、Ruff、strict38/38/diff通过；下段1968全量是上一批证据。仍待完整Audio本机ASR入口、跨模态产品冒烟、两个角色真实成品质量及正式初始化/生命周期。没有新增真实调用或改正式数据/配置/运行服务；目录和启动方式不变。当前以[实施进度](openspec/changes/add-persona-creative-studio/progress.md)为准。

2026-10-07 **Persona Creative Studio当前99/147，剩48，尚未全部完成**：已补Recipe→图文编辑器/真实状态、Persona图片尺寸校验、已有ASR对稿/真或估算SRT、Starter Fork与只读就绪卡片；明确操作不覆盖Master草稿、不自动识别/调用模型。限定独立复核、1968项既有全量回归（28skip）、最终105项定向、Web/FE-P1、Ruff、strict38/38通过。48项包括剩余功能/合同、持久测试、真实质量、正式初始化与生命周期，不等于48个都没写。正式库/配置/角色/服务未变，无新测试/迁移/Provider调用/发布/提交归档，目录和启动方式沿用现有方案。见[本批完整进度](openspec/changes/add-persona-creative-studio/progress.md)；下面95/147是此前批次。

2026-10-07 **Persona Creative Studio尚未全部完成，当前95/147、剩52**：本批关闭30项资源/typed中间产物/确定性Graphic排版与基础QC/Text质量/配置库存/导演与角色方法窄scope及轻量UI合同。音频显式模型覆盖和导演指令上限两处定向疑点已闭合，完整Audio复核仍PARTIAL。最终后端1968 passed/28 skipped（106.33s）、Web/FE-P1、Ruff、OpenSpec strict38/38及diff通过；20份资源/八份可移植Recipe纯冒烟通过。完整Renderer阶段承接、ASR/字幕入口、Starter fork/readiness及真实默认Text/Graphic/Audio质量尚待，不以代码/Mock替代成品验收。正式库、配置、运行服务不变，不新增测试/migration/真实调用、不提交推送归档。当前以[本change进度](openspec/changes/add-persona-creative-studio/progress.md)为准，以下65/147、Text-only和图文未开始记录为历史。

2026-10-06 **两个角色真实文字到本地交付已验通，默认Recipe质量仍PARTIAL**：Gemini科技/生活原稿已分别保存，独立复核编辑并补7条精确引用后，隔离Master1/2→真实checks→Candidate v4→Review→copy_package ZIP实际通过，正文/独立标题/hash保持一致。稿件见[科技编辑稿](openspec/docs/项目文档/PERSONA_GEMINI_TECH_EDITED_2026-10-06.md)与[生活编辑稿](openspec/docs/项目文档/PERSONA_GEMINI_LIFESTYLE_EDITED_2026-10-06.md)。Agent复核不代替用户质量确认；默认Text文档grammar/服务端引用选文计算已补，345项既有回归/Ruff通过，但新合同真实call18无响应，Unknown不重发，18/30调用。完整九阶段真实验收与固定rubric仍待，65/147不虚增；图文/音频未开始，正式库/配置/Persona及运行拓扑不动、不发布/迁移/归档/提交。详细当前证据见[真实文字回执](openspec/docs/项目文档/PERSONA_TEXT_REAL_ACCEPTANCE.md)；以下同日一篇/零Master记录为历史。

2026-10-06 **Gemini一次完整文章生成成功，Persona质量验收仍部分完成**：按用户新授权，在隔离库新单阶段Run7/Attempt11中使用exact Gemini，50.79秒返回并校验text.master.v2、导出1822字符[原稿](openspec/docs/项目文档/PERSONA_GEMINI_ARTICLE_2026-10-06.md)。未换模型或重发旧Unknown，未接受Master/发布；两个角色完整默认Recipe/人工质量仍待验收，65/147不变。正式配置/库不动，图文/音频未开始；当前回执见[真实文字验收](openspec/docs/项目文档/PERSONA_TEXT_REAL_ACCEPTANCE.md)。

2026-10-06 **CPA本机隧道已按用户授权直接生效**：`http://127.0.0.1:8317/v1`，正式配置revision5；Key/已登记模型/默认Gemini/各环节路由保持，应用认证发现200/32模型。仅明确登记的literal127.0.0.1开放，原API/Worker已安全刷新；无新生成、Unknown重试或迁移。详细当前结果/依赖见[模型登记](openspec/changes/add-provider-model-registration/README.md)，目录连通不等于真实创作质量验收。

2026-10-06 **当前方向：Persona Creative Studio，两个角色文字先行**。[add-persona-creative-studio](openspec/changes/add-persona-creative-studio/README.md)已获SPEC APPROVE及apply授权，当前65/147项完成。两个Starter Persona的九阶段文字流程已在隔离SQLite/Mock中走通：证据→角度→大纲→初稿→检查→精修→标题→最终Master→最终检查，再经Candidate v4/审批/授权生成本地ZIP。浏览器24个检查点、后端1968 passed/28 skipped、Web/FE-P1通过；这证明合同与产品链路，不证明真实文章质量。真实模型文字质量单独待授权验收，图文之后、音频最后；部分高级配置/UX仍待补齐。十二平台提案继续暂缓，不初始化正式Persona，不改正式crs数据/运行拓扑，不新增migration，不提交推送归档。见[文字合同验收](openspec/docs/项目文档/PERSONA_TEXT_CONTRACT_ACCEPTANCE.md)。

2026-10-06 **下一项范围已确认：十二平台专属稿件＋素材交付包**，公众号保留草稿箱、其他平台人工发布；知乎/B站/X各形态独立，共十七形态。标准提案与两批计划见[complete-multiplatform-content-handoff](openspec/changes/archive/2026-10-14-complete-multiplatform-content-handoff/README.md)。本轮仅规格，尚未business apply/正式profile写入或公开发送；原有Recipe/F8/ACO完成状态不因此改变。

2026-10-06 **Creation Recipe已在本机正式启用，141/144**。正式SQLite、approved默认/readiness及私有配置均为`crs000000001`，API/原Worker已恢复，Web仅`127.0.0.1:5173`。配套备份/副本演练/正式升级后确认5,145行原数据、65个素材hash不变；健康/Recipe选择/MCP只读入口通过。旧Unit不自动绑定新流程。永久新回归、完整backend和规格生命周期仍待收尾；本轮未调用模型/公众号、未提交推送归档。见[本change](openspec/changes/creation-recipe-stage-control-loop/README.md)和[正式启用与备份](openspec/docs/项目文档/CREATION_RECIPE_LOCAL_ENABLEMENT.md)。

## 10月4–5日历史状态（当前以10月6日crs启用记录为准）

2026-10-05 Creation Recipe批次五/六：新change为56/144（剩88）。已接入真实Prompt分层预览、按阶段临时调节、Text候选选择/结构化修改/显式接受、Master正文与版本回读，以及接受后自动执行下一阶段并停在人工审阅处。刷新只恢复原Attempt，不再次调用模型；回读延迟/失败禁止新调用，恢复固定原Run/key，独立Master未保存编辑保持不变。隔离Mock浏览器9项通过；完整后端1908 passed/28 skipped、Web/FE-P1/strict36/36通过。拒绝反馈、保存有效调整、跨形态和完整Candidate→Review→Package仍待后续批次，不冒称全部完成。现有API/Web/Worker、SQLite/素材及启动方式不变；无正式库升级、真实供应商调用或提交归档。范围、设计与进度见[本change说明](openspec/changes/creation-recipe-stage-control-loop/README.md)。

2026-10-05当前正式schema校准：Creative Orchestration已另行获准在本机启用，SQLite为`aco000000001`（f7d→f8a→aco），API/Web/原Worker/MCP保持运行。local approved默认、readiness和恢复目标以aco为准；f8a两列nullable身份字段全空/inert，不启用JWT/服务器认证，也不回滚真实库。原F8 82/82和f7d验收记录保留为历史，不重写成新测试结果。新版见[正式启用](openspec/docs/项目文档/ALIGN_CREATIVE_LOCAL_ENABLEMENT.md)；core implementation通过，R1/R2修正和108项永久回归已完成（完整后端1768 passed/28 skipped），153/154只剩最终closeout复核，尚未canonical归档/新功能提交/push；见[收尾回执](openspec/docs/项目文档/ALIGN_CREATIVE_LEGACY_FINAL_PARTIAL_ACCEPTANCE.md)。

2026-10-04正式部署决定（部署范围继续有效，以下动作记录为当时历史，当前schema以10月5日说明为准）：**这台电脑就是最终单机生产环境**，SQLite＋当前本地素材库＋仅本机API/Web，维护目标为易启动、易排查、可备份恢复，不是等待服务器升级的临时方案。F8批准范围82/82已验收，功能ade4ce0、收尾1aa0024；原18条是范围外扩展/未验证，不是当前生产缺口。缺少PostgreSQL、MinIO、JWT或独立Secret Provider不阻断正式使用。技术APP_ENV=production与使用称呼分开，不改配置/身份/凭据/Worker。当前main基线341ead8保持，此轮仅文档/规格校准，不重跑模型/公众号、不push/deploy/迁移/主规格同步归档。

## 当前单机生产：日常入口

| 操作 | 现有入口 |
|---|---|
| 启动/停止/重启API和Worker | [单机生产运行手册](openspec/docs/项目文档/runbooks/production-readiness.md)，现有launchd/startup脚本；API为127.0.0.1:8000，不新增部署体系 |
| Web | `cd apps/web && npm run dev`，localhost:5173；不新增对外绑定 |
| 排查 | 显式Settings运行状态/health readiness；`logs/api.log`、`logs/worker.log`按trace/reason定位，避免复制私密内容 |
| 备份恢复 | [配套备份恢复手册](openspec/docs/项目文档/runbooks/backup-restore.md)，SQLite＋素材同快照、隔离验integrity/head/hash/历史包；make backup仅数据库，make stop仅API |
| 验收状态 | [正式验收](openspec/docs/项目文档/FE_F8_LOCAL_FINAL_STATUS.md)、[能力矩阵](openspec/docs/项目文档/FE_F8_LOCAL_CAPABILITY_MATRIX.md)；ZIP不等于公开发布，契约测试不等于生成质量 |

仅本机访问限制入站，不禁止既有获准模型/公众号出站。不要为“生产”改APP_ENV、复制服务器模板、运行seed/迁移、切换素材目录或删除Worker。主规格同步/归档属于另行授权的文档生命周期，不是服务器设施阻断。

## 历史阶段记录（不作为当前部署或完成口径）

以下等待提交、未生产就绪、82/83及17项是历史时点，当前以顶部正式范围和运行手册为准。

2026-10-04 F8 本机实施验收通过，等待本地提交及主规格同步/归档授权。正式基准为个人本机 SQLite、本地素材库、仅 loopback 访问；本机 `82/83`，原清单 `82/100`，只剩本地最终提交/ROADMAP记录。17项生产身份/Secret Provider/新增真实远端发布义务已确认延期，保留未勾选/未验证。此前总体复核及最终定向复审闭合四项恢复/安全blocker，安全与架构均APPROVE；正确apps/api cwd全量1660 passed/28 skipped/8 warnings、186定向、Web/预算、strict34/34、Ruff/diff通过。三形态/五渠道本地闭环、20个新浏览器gate、恢复重新导出和确定性Golden证据保留，真实模型质量未验收。CLI内部HTTP/供应商后台grant不由本机helper证明。未commit/push/deploy/正式迁移/主规格同步归档；未批准身份draft不得混入提交。目录增加恢复脚本和Golden夹具，依赖与启动方式不变。见[本机验收](openspec/docs/项目文档/FE_F8_LOCAL_FINAL_STATUS.md)、[出站审计](openspec/docs/项目文档/FE_F8_EXTERNAL_CAPABILITY_SECURITY_AUDIT.md)、[本机闭环](openspec/docs/项目文档/FE_F8_LOCAL_FULL_CHAIN_ACCEPTANCE.md)、[恢复验收](openspec/docs/项目文档/FE_F8_RECOVERY_ACCEPTANCE.md)与[Golden夹具](apps/api/evals/goldens/README.md)；下方旧计数为历史。

2026-10-03 F7已按当前批准范围收口：主任务110/110（Commons为用户暂缓行政关闭，不是实测PASS），模型路由23/23；F7实施已本地main提交`3f28a51`。主F7与模型路由均已归档，八份delta完整同步七份canonical，原有54条要求/146个场景精确保留，strict34/34及diff通过。F7-only后端1660 passed/28 skipped、Web/FE-P1/state和Ruff通过；无push/deploy/正式迁移或新增微信/供应商调用。F8及原始资料仍保留工作区、不在本次提交。目录、依赖与启动方式沿用既有配置，后续Commons/F8需另定范围；见[F7归档](openspec/changes/archive/2026-10-03-fe-f7-capability-integrations-delivery/README.md)。以下旧计数与active状态为历史。

2026-10-03 F7本地生命周期收尾：仅F7的81文件拟提交快照经后端1660 passed/28 skipped、Web/FE-P1/state、full app Ruff、strict34/34与diff验证通过，Projects224.89/72.97kB。共享文件按片段排除F8认证/MinIO/f8a，F8工作区完整保留。Commons按用户决定暂缓/未实测，不标真实PASS；公众号沿用已确认的当前草稿与精确系统记录，模型路由23/23。当前108/110，接下来只做本地提交和七份主规格同步归档，无push/deploy/正式迁移或新增外部调用。目录增加已实现的本地生成任务/ASR服务，依赖与启动命令不变；见[最终门禁](openspec/docs/项目文档/FE_F7_FINAL_LOCAL_GATES.md)。下方计数与未提交描述为历史快照。

2026-10-03 公众号精确范围验收完成：原短稿/黄色封面经AIContentStudio Candidate7→审批→Target7/Attempt7一次上传/draft/add成功，用户确认最新草稿后真实Receipt1/CapabilityVerification1原子持久化于私有验收库，重复回填幂等；不同账号/形态/动作/版本/运行身份均不能复用。补齐历史Attempt指纹校验，120定向/1660全量、Ruff/strict34/diff和限定复核通过。F7现107/110，剩Commons用户暂缓、本地提交、主规格同步归档；模型路由23/23。无公开发布/回读/重发或正式库改变，F8、依赖和启动方式不变，未提交推送归档。见[本轮真实证据](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)；下方105/110为历史。

2026-10-03 F7主任务10.3已按真实模型证据收口：当前105/110、剩5条，模型路由23/23。真实image-01字节/hash、正式TTS accepted→MaterialRevision6→Text Master9、本机Video Master5的43字幕记录只读回读一致；MiniMax视频/H3排除、Commons暂缓、未证明权利仍false。公众号旧两稿均成功，但没有系统收据/验证、历史指纹与当前实现不匹配；内存副本receipt实际409回滚，8.3/10.5不提前关闭，还须补Attempt指纹绑定及当前版本一次获准草稿/同账号确认。119项既有回归通过，限定证据复核同意10.3关单；没有新业务代码/依赖/迁移、外发、正式库写入、提交、推送或归档。目录与启动方式不变，见[公众号核对](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)和[模型证据](openspec/docs/项目文档/FE_F7_MODEL_VALIDATION.md)。下方旧计数为历史。

2026-10-03 模型路由最后五项已完成：`add-model-capability-routing` 23/23，2.1/2.5/2.6/2.7/2.9全部关闭。五处预览/Workflow/ASR/音频契约缺口修复后，后端1660 passed/28 skipped、177定向、Web/FE-P1/state、strict34/34、Ruff/diff与两份限定独立复核通过。CPA聊天、真实MiniMax图像/语音及本机ASR沿用已记录验收；视频/H3为用户排除、CPA媒体未证实、未证明公开权利仍false。当前main工作区未提交，未新增供应商或微信调用/正式库写入，目录/依赖/启动方式不变。仅本change实施收口，canonical同步/归档与整个F7/F8关单仍按各自范围处理。见[最终门禁](openspec/docs/项目文档/FE_F7_FINAL_LOCAL_GATES.md)和[任务](openspec/changes/add-model-capability-routing/tasks.md)；下方18/23等是历史。

2026-10-03 当前模型路由18/23：可靠性3.2/3.4及完整页面2.8已收口，仍剩2.1/2.5/2.6/2.7/2.9，F7未整体完成。实际隔离页面验证chat-only→图片插件/原生TTS→预览→人工接受→刷新，Unknown不重发、缺video插件零发送、页面配置保存和旧任务发送前409均通过；fixture与既有真实TTS/本机ASR证据分开。两处Panel状态/中文提示修复通过新鲜Web/FE-P1/state、144定向和限定独立复核；不改正式库/配置、不调用供应商或微信。目录/启动/依赖未变，下方17/23是先前可靠性收口记录。

2026-10-03 生成任务可靠性已整项收口：模型路由3.2/3.4完成，change为17/23（剩6个复合项），不是F7全部完成。修复原key身份、原job/file一致性和known-job Unknown后，最终后端1660 passed/28 skipped/8 warnings、Web/FE-P1/state、strict34/34、Ruff/diff通过，限定独立源码复核APPROVE。0新增真实供应商调用/正式库写入、无新依赖/迁移或提交推送；下方“收口前”状态为历史。下一项继续产品路由/浏览器链路验收，目录和启动方式不变。

2026-10-03 最新 F7 接受/可靠性：正式 MiniMax TTS task 已经一次执行、接受为 MaterialRevision6，并经项目精确引用保存到可写 Unit3 的 Master9/v3；浏览器刷新回读通过，public/model/commercial 权利保持 false，不能冻结公开 Candidate。可靠性初验完成38个私有场景；定向复核后最小修正历史key派生、terminal原job/file核对和known-job unavailable→Unknown，补33组正负向验证通过。来源claim commit的授权边界已核清，接受仍实时检查撤权；这批0真实供应商调用/正式库写入，无新依赖或migration。整体F7独立终审及其余验收仍TODO。目录及启动方式未变；下方同日“正式TTS尚未执行”是历史记录。见 [可靠性证据](openspec/docs/项目文档/FE_F7_FINAL_LOCAL_GATES.md) 与 [当前进度](openspec/docs/progress.md)。

2026-10-03 公众号草稿成功后的系统记录已接入：同一官方账号的 `succeeded` Attempt、非空 `media_id` 与 `human_confirmed` 收据会原子幂等地写入既有 `CapabilityVerification`，仅验证 `wechat/article/auto_draft` 精确范围，不代表公开发布，不调用 `draft/get`，不新增表或 migration。定向交付/能力回归 165 passed，Ruff PASS；本轮未重新发送公众号草稿。

2026-10-03 本机ASR已完成真实产品验收：复用自有Radar/voice-pro最小MLX桥接，用户视频`废电池回收处理设备.mp4`进入正式MaterialRevision3和项目共享素材，页面默认本机MLX Whisper，实际生成43条字幕，人工接受后显式保存Video Master5/v3；刷新和API重启后仍回读同一字幕、来源、runtime及`verified_output_match` provenance。产品链路只使用`model_use_allowed=true`、`public_use_allowed=false`的本地素材，不公开发布、不冻结Candidate、不生成可发布包。普通素材仍兼容“公开可用或模型可用”，最终render继续要求公开权利。105项Video/ASR/材料定向回归、1660全量后端（28 skipped、8 warnings）、Web/FE-P1、OpenSpec strict34/34、Ruff与git diff-check均通过。新增canonical规格`openspec/specs/local-asr-subtitles/spec.md`，change已归档到`openspec/changes/archive/2026-10-03-add-local-mlx-asr/`。无新表/0migration、无云端请求；未提交、未推送。

2026-10-03 当前本地接入：已备份并演练后准确升级个人本地SQLite到f7d（不含F8），启动配置加载稳定私有签名key并启用MiniMax image/TTS/ASR插件；CPA Gemini默认、七文本routes和密钥保持不变。页面TTS准备路由通过但未执行付费生成；已有真实WAV经页面导入正式Revision2、项目引用及Master2显式保存，刷新/API重启回读和新进程回执验签通过。来源如实为upload，公开/商业权利未确认；不冒称新任务生成接受或ASR字幕链路完成。118项既有回归、Web/FE-P1、strict33/33、diff及限定只读复核通过。无commit/push/公开发布/全F7归档；详见[当前接入证据](openspec/docs/项目文档/FE_F7_MODEL_VALIDATION.md)。下方同日“未正式配置/迁移”是此前阶段记录。

本地启动仍沿用`apps/api/scripts/startup/start_api.sh`和`start_worker.sh`，两者加载被忽略的`runtime.env`；CLI需PATH含/opt/homebrew/bin，稳定key-ID及JSON key映射须显式加载、0600保管，不打印或提交。0700私有目录`backups/minimax-local-z98vx7ki/`保存升级前/后SQLite及配置/key备份；没有新的依赖或迁移版本。剩余TODO：新正式任务生成/显式接受、Production ASR接受和复合F7验收；既有97条FK异常另列历史债，不自动处理。

2026-10-03 最新语音实测：获准的三次MiniMax调用全部成功——3.413秒TTS、音频ASR、视频音轨ASR；后两项准确返回原句。TTS经隔离产品持久任务API并通过新进程回执/字节验签；ASR验证现有固定适配器，不冒称Production入口/正式素材接受完成。视频为本地黑底测试容器，不调用视频生成。54项现有回归、strict33/33、diff-check通过，无业务源码/依赖/启动/正式配置改变；正式持久任务表、媒体binding和签名配置仍TODO，F7未整体关闭。目录与证据见 [模型验收](openspec/docs/项目文档/FE_F7_MODEL_VALIDATION.md)。

2026-10-03 用户范围：MiniMax 视频生成与原H3下载不再要求，停止其调用/查询并记为用户排除，不是已验收；下方DNS阻断保留为历史，不再卡F7。MiniMax聚焦文字转语音、语音转文字、已有视频提取音轨后转文字，不包含生成视频或画面理解；用户随后批准三次≤10秒语音实测，结果见上方。未变更正式配置、依赖或启动方式，无正式迁移/推送。

2026-10-03 当前模型状态：模型登记/路由必要依赖及新版模型设置已本地提交 main@8c0e3b8，未推送。已保存 CPA 的 Gemini/Claude/Grok 三模型真实聊天、模型发现、七用途解析和 Gemini JSON 消费者调用通过，默认/revision3/路由未改。MiniMax 原 H3 已远端成功，但成品 OSS 下载仍被 VPN Fake-IP198.18.4.255 阻断；未重发、无视频素材接受，F7 媒体并未整体收口。无新增依赖或本次迁移，其他 F7/F8 保留；下方未提交/旧401均为历史步骤，当前证据见 [F7 模型验收](openspec/docs/项目文档/FE_F7_MODEL_VALIDATION.md)。

2026-10-03 模型设置布局已完成：仅“模型与 AI”改为厂商与模型、用途路由、生成能力与插件三视图，沿用紧凑管理员布局、默认折叠技术信息、保留草稿和独立保存范围。其他五分区、legacy、现有配置/密钥/默认模型未改；无后端/依赖/启动变化。Web/FE-P1、85 项既有安全回归和独立源码复核通过，桌面/390px/草稿离开确认/viewer 只读已验收；原生 Back/Forward 未实际验证。六条新增契约已同步主规格，原有 10 条要求/15 个场景完整保留；归档后 strict 33/33、diff-check PASS。见 [归档与验收](openspec/changes/archive/2026-10-02-organize-model-ai-settings/README.md)。仅本地 main 未提交，不推送/部署、不调用供应商。下方 CPA 鉴权记录为此前诊断，不作为当前状态。

2026-10-02 设置页恢复：用户同意后温和停止 9 月旧 API 进程，本机服务自动拉起新版；产品设置、厂商登记及模型能力接口经 8000 与 5173 代理均实际返回 200。前端保留，数据库/密钥/代码/迁移未人为改动，用户浏览器可能需刷新。CPA 网关 401 仍是独立待办，不能由本机页面恢复推定模型可用；详见 [进度](openspec/docs/progress.md)。

2026-10-02 设置页 Not Found 诊断：5173 新前端连接到 9 月 25 日启动且无热重载的 8000 旧后端；运行中 OpenAPI 缺 10 月 1 日加入的产品设置/模型登记路由，三条设置接口实际 404。未重启服务或改代码/配置/数据；需先更新本机后端进程并核对接口，再处理独立的 CPA 401。目录、依赖和启动方式未变，见 [进度](openspec/docs/progress.md)。

2026-10-02 CPA 鉴权只读排查：运行中 API 与诊断读取同一 SQLite 配置；已保存 Bearer 请求 `/v1/models` 得 401 `invalid api key`，无密钥得 401 `missing api key`。网络/路径/头部已定位正常，需在 CPA 网关核对当前有效客户端密钥；不能把本地已登记/可选模型称为远端可用。本批仅更新任务证据，无业务代码、目录、依赖、启动、默认或配置变化；详见 [进度](openspec/docs/progress.md)。

2026-10-02 H3 能力核验：本机 MiniMax CLI 一次 5 秒任务 `448101822222777` 已远端完成；AIContentStudio 下载受当前 VPN Fake-IP/安全 URL 校验阻断，未取得正式视频字节或素材。CPA 模型/默认已登记，但 `/models` 实际鉴权拒绝，不能作为可用视频 fallback。只更新验收记录，不改目录、依赖、启动/默认配置或业务代码；后续恢复同一任务，不重新生成。详见 [模型路由变更](openspec/changes/add-model-capability-routing/README.md)。

2026-10-02 模型路由本批：仍以 `openspec/changes/add-model-capability-routing/` 为 active 规格，复用现有 SystemSetting/Registry/ProviderGenerationTask/MaterialRevision，不增加第二套真源。已核对本机 MiniMax 固定 CLI 命令及现有 83 项路由/持久化回归，并更新 [Provider 契约](openspec/docs/项目文档/FE_F7_PROVIDER_ADAPTER_CONTRACTS.md) 和 [F7 能力矩阵](openspec/docs/项目文档/FE_F7_CAPABILITY_MATRIX.md)。CPA 实际聊天合同、MiniMax 视频原任务/权利、完整浏览器与安全验收仍是 TODO；外部付费、生产身份/存储、发布均未启用。目录/依赖/启动方式不变，运行仍需显式 CLI opt-in、持久 receipt key、已授权的本地 schema，不能把配置当已验证能力。

同批安全修正：MiniMax image/TTS CLI 一旦可能已接单，即使本地非零退出或输出文件异常也保持 Unknown/原 claim，不把它解释成“可重新生成”的确定失败。当前完整任务仍 15/23，剩余 8 项不能由离线探针或已有构建代替外部与浏览器验收。

生成面板现从冻结任务回执读取执行路径并在准备态/历史态标明模型自身或已授权插件；只改只读投影，不改变路由、默认模型或本地/生产部署方式。

MiniMax ASR 的 CLI 非零退出现保持 Unknown，不将该错误当作安全重试依据；通用异常仍按既有 502 脱敏契约处理。ASR 使用短期建议收据，并非持久生成任务，完整防重和真实转录验收继续待办。

2026-10-02 F7 范围校准：成功公众号草稿以有效 `media_id` 落库和同账号后台人工确认验收，不强制成功后 `draft/get`；Unknown 对账和一般 Publisher `verified` 仍分开。Gemini/`grok-4.7` 均经第三方 CPA 网关，模型路由复用可配置 OpenAI-compatible 接口，不再要求 Google/xAI 官方专用适配器；生图/视频/语音能力须逐操作证明，否则走已配置插件或显示不可用。沿用现有目录、依赖与启动方式；模型真实合同、MiniMax 原任务可靠性和 F7 一般账号验收仍待完成。详见 [F7 任务](openspec/changes/fe-f7-capability-integrations-delivery/tasks.md) 与 [模型路由](openspec/changes/add-model-capability-routing/README.md)。本次不发草稿、不运行生成、不改正式数据库或默认配置。

2026-10-02 F8 schema readiness：生产启动与 `/api/v1/health/ready` 现在共用只读 Alembic 检查，要求代码、数据库与显式配置各只有同一个 head；多头、缺失或陈旧版本返回安全失败，不自动迁移。沿用现有 `apps/api/app/db.py`、`main.py`、`observability.py`；目录、依赖与启动命令不变。F8 身份绑定、真实存储连通及完整验收仍待后续任务，详见 [F8 OpenSpec](openspec/changes/fe-f8-production-readiness-operations/tasks.md)。

2026-10-02 指定原HTML长文已通过AIContentStudio公众号适配器进入同一真实公众号草稿箱：新私有产品链 Candidate v5 → Approval → Target/Attempt 上传封面和八张正文图并调用一次 `draft/add`，有效 `media_id` 已落库，原正文在替换上传图URL后可精确还原，九个素材上传保留原文件名。旧失败Unknown库不变；未公开发布或回读；本次指定草稿验收通过，但一般Publisher验证及F7全阶段仍未完成。代码目录、依赖、启动方式未变；证据见 [F7公众号草稿验收](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)。

2026-10-02 原HTML公众号产品链路已补齐：wechat.article.v1可携带与可见文本/精确图槽一致的安全HTML，审批前冻结official renderer v3，保留样式/原文件名，独立HTML一次授权不放宽旧短稿/一般验证。前端v3仅在禁止脚本及远端资源的opaque sandbox内显示内联样式。实际一次执行已完成token及封面上传，首张正文图响应被本地URL白名单拒绝，draft/add调用0次、无草稿media_id，旧Attempt保留Unknown。对照成功WeWrite记录已补from=appmsg兼容，八个真实历史URL离线通过；后续外发待新的单次授权，不自动重试。目录/依赖/启动/迁移不变，详见docs/FE_F7_SHORT_DRAFT_ACCEPTANCE.md；不是整个F7完成。

2026-10-02 WeWrite实际源码核对完成：原图片名multipart上传、原HTML写入draft/add的content、UTF-8 JSON并以有效media_id确认；没有2KB正文限制或强制成功回读。产品长文阻断来自本地短稿实验gate/原HTML入口缺失，不再要求用户重复确认已授权原稿封面。此轮只读核对与文档纠正，尚未发送，目录/依赖/启动未变。

2026-10-02 指定长文产品重发预检：用户批准沿用原HTML/封面同公众号一次草稿发送，输入hash已核对；产品仍仅开放<2KB短稿实验且缺原HTML保真入口，47577字节正文实测被拒绝。本次零微信请求，没有新草稿或media_id；最小长文契约/入口修订待确认，不以独立WeWrite替代产品验收。目录、依赖和启动方式未变，详细证据见task_plan.md、progress.md、findings.md。

2026-10-02 公众号补充已提交本地main@931915d并完成主规格/归档。F8继续按原计划补齐存储、健康、安全和恢复验收，当前不是产品整体完成；不推送、部署或运行正式迁移，MiniMax/路由/F8工作区改动保持独立。当前计划与证据见task_plan.md、progress.md、findings.md。

2026-10-02 公众号补充收尾：用户接受指定账号草稿/media_id+后台确认，额外成功回读为豁免不是已执行。原文件名已冻结于official render v2并逐步核对、原样上传，缺失/不安全名称拒绝；历史候选不回填。完整工作区后端1660/28 skipped，公众号-only拟提交快照1624/28 skipped、PG迁移22项、Web/FE-P1、41隔离UI、范围Ruff/diff及独立复核通过。仅同步account-bound-wechat-draft-publisher主规格并归档本补充，不将未提交MiniMax/F8混入；不再外发、推送、部署或生产迁移。一般runtime未解除安全门槛，其他F7/F8 TODO仍保留。目录增加四个wechat_official服务、AccountPublisherPanel/OfficialArticlePreview、f7c账号字段迁移；启动/依赖不变，正式f7c升级仍需独立目标授权。详见[公众号收尾证据](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)。

2026-10-02 用户确认公众号草稿创建实验到此结束：产品已保存有效media_id，且后台人工确认通过；不要求成功草稿额外回读，取消拟议的新入口和补测，不再上传/create或公开发表。只更新记录，不把未执行回读记为PASS；其他F7任务及Unknown对账边界保持不变。目录/依赖/启动不变，详见[验收结论](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)。

2026-10-02 产品草稿回读零网络预检：原Attempt6仍succeeded、Target6 awaiting_manual_receipt，精确media_id/hash保持一致，readback_hash为空。现有official-readback仅允许Unknown对账，且原实验授权已过期，不能直接用于成功草稿核验。未调用微信、重复创建或修改DB；成功草稿只读回读契约待单独规格/实施授权，F7不提前关单。仅文档记录，目录/依赖/启动不变；详见[公众号验收](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)。

2026-10-02 MiniMax真实能力单次验收：在私有临时数据库中各调用一次 `image-01` 和 `speech-2.8-hd`，均真实进入 `result_ready`；图片JPEG33997 bytes/hash=`1e18a7be540f091ac7d71510a3aebe68a24ca57413f99b2e00667857c0db7298`，语音WAV180980 bytes/hash=`5e6c663fb225d07c8db2b0609294966b3a452e791160ef351443c05a39cbcb7b`。未接受到正式素材库、不重试旧Unknown、不调用视频/ASR。新进程完成数据库/字节hash回读，但临时receipt key未持久化，HMAC跨进程验签仍未完成；不冒充完整F7或生产就绪。

2026-10-02 F8第一批：统一 `StorageProvider` 的 immutable put/read/exists/size/delete-if-unreferenced 边界，MaterialRevision 的 Delivery、package、Article Handoff 和 renderer 输入先走 provider/hash 校验；绑定 revision 的失败读取不再回退旧本地路径；新增管理员安全存储诊断；健康接口区分 live/ready，生产 metrics 需要管理员，DraftMedia 无 revision 的旧路径保留兼容桥。相关范围回归128 passed、Ruff、diff-check、OpenSpec strict33/33通过。生产 MinIO 切换、全量 legacy 路径迁移、备份恢复和F8终验仍未完成；无正式迁移、部署或推送。

2026-10-02 指定HTML完整长文单次草稿测试成功：用户确认短标题、首图封面及8图副本压缩后，沿用原正文/内联排版，经独立WeWrite HTML API创建一个草稿并draft/get回读；标题/正文/216个style、8图资源顺序一致。微信URL规范化为HTTPS/640，不能称HTML/远端图片字节完全不变；后台视觉待人工核对。原HTML/PNG、正式库/配置/历史Unknown未改，不公开发布；不替代产品Candidate→Delivery验收或解除一般gate，F7仍131/152。仅临时验收和文档，无业务代码/依赖/迁移/启动方式变化，详见[本次完整HTML测试](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)。

2026-10-02 当前统一验收：公众号产品短稿创建+用户后台可见性PASS；F7 8.5冻结内容不可改已独立复核并关闭。新鲜门禁129公众号定向/1660后端（28 skipped）、Web构建/FE-P1、strict33/33、范围Ruff及diff通过。主切片98/105、路由14/25、公众号19/22，复合131/152，剩21；一般长文/普通账号verified、整阶段终审提交/归档仍未完成。原文件名透传差异如实保留，不新增草稿或公开发布。MiniMax已只读核对原语音WAV/hash与图片Unknown；当前进程缺原receipt key，无接受/恢复/重发。证据见[公众号验收](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)与[当前矩阵](openspec/docs/项目文档/FE_F7_CAPABILITY_MATRIX.md)。无业务代码、依赖、正式配置/库、迁移或启动方式变化；后文旧计数/失败记录为历史。

2026-10-02 用户后台截图已确认本次草稿：标题“响应兼容测试，请勿发布”、同一黄色测试封面，更新14:31；“创建并进入草稿箱”真实验收PASS。只补人工确认记录，不公开发布、调用接口或写入DB回执/能力验证，不将此确认扩大成整体F7或一般长文合同通过。公众号仍19/22，无代码/依赖/启动变化。

2026-10-02 公众号真实产品链路成功：用户精确授权后，测试稿“响应兼容测试，请勿发布”通过Candidate6→Target6/Attempt6完成token、原封面上传、draft/add，返回有效media_id并记录succeeded/awaiting_manual_receipt。未公开发布、未追加远端回读、未重试五条旧Unknown，旧记录全字段保留，正式库/配置未变。仅关闭短稿验收2.8a，公众号19/22，一般长文合同/终验/归档仍待完成；无新代码/依赖/迁移或启动变化。证据见docs/FE_F7_SHORT_DRAFT_ACCEPTANCE.md；下文审批阻断等是此前记录。

2026-10-02 新草稿测试已授权并通过本地冻结审批/预检：Candidate6，“响应兼容测试，请勿发布”，118字节HTML、原19723字节封面，五条旧Unknown全字段保留。实际本机外发命令在启动前被auto-review拒绝，要求明确具体账号/正文/封面授权；没有微信请求或新Attempt，不能绕过。私有预览与证据保留，公众号仍18/22；本轮无业务代码、依赖、迁移、正式配置/库或启动变化。

2026-10-02 授权的公众号响应兼容修正已本地实现：固定官方接口允许application/json或text/plain中的严格合法JSON，仍检查HTTP200、errcode、操作字段/media_id、预算/TLS与无重试。129定向、全后端1660 passed/28 skipped（77.68秒）、15正向/16拒绝无网络探针、strict33/Ruff/diff及独立窄复核APPROVE。未读取凭据或调用微信，旧Unknown和正式库未变；公众号仍18/22，真实新草稿另需授权。无新依赖、迁移、前端或启动变化；证据见docs/FE_F7_SHORT_DRAFT_ACCEPTANCE.md。下文未修正等为之前阶段记录。

2026-10-02 最新单次授权测试：token成功，封面上传收到HTTP200/text/plain，但产品要求application/json并在解析正文前拒绝；Attempt5 Unknown，无draft/add/media_id。已核对本机WeWrite直接resp.json()，没有相同MIME门槛，后续需定向修正响应兼容；本轮不改代码或追加请求。四条旧Attempt全字段未变、不重试、不公开发布，公众号仍18/22。仅临时私有验收数据/脚本和记录更新，无新依赖、迁移、正式配置/库或启动变化。证据见docs/FE_F7_SHORT_DRAFT_ACCEPTANCE.md。

2026-10-02 本地诊断补丁：公众号上传失败现可记录固定阶段/原因、严格HTTP状态整数与响应类型分类，Attempt持久化再次过滤；不记录原始header/body/error或凭据。129项定向、全后端1660/28 skipped（74.80秒）、strict33/33、Ruff/diff、无网络探针及独立诊断窄复核通过，未调用微信接口、未改旧Unknown、未公开发布；公众号仍18/22，真实上传原因待下一次独立授权验收。仅transport/delivery诊断和文档变化，无新依赖、迁移、业务对象或启动变化。

2026-10-02 最新真实验收：用户授权 token 修正后单次新测试稿。产品预检通过，token 实际成功，但封面上传响应仍未确认；新 Attempt 4 保留 Unknown，尚未调用 draft/add、无 media_id。旧三条 Unknown 全字段未变化，未重试、未公开发布或写正式库。本轮仅验收与文档更新，无业务代码/依赖/迁移/启动变化；公众号仍 18/22，响应具体失败分支需安全诊断后再确认。详见 `docs/FE_F7_SHORT_DRAFT_ACCEPTANCE.md`。

2026-10-02 最新纠正：前一批 token 虽已改成 GET，地址仍遗漏为 stable_token，既有测试也保留了旧期望；本轮已改为 WeWrite 的 `/cgi-bin/token`，并修正接口拒绝时的实际发送提示。最新真实 Attempt 3 在 token 阶段被拒绝，未上传或创建草稿；旧 Unknown 不改写/重试。110 项定向、全后端 1660 passed / 28 skipped / 8 existing warnings（81.27秒）、Ruff/公众号 strict/diff 及独立窄复核通过，本轮无真实请求。公众号补充仍 18/22，不宣称 F7 完成；无新依赖、迁移、配置或启动方式变化。

2026-10-02 最新：已将公众号官方适配器的 HTTP token、multipart 上传和 `draft/add` 请求行为对齐本机 WeWrite 实现；`draft/add` 成功必须有 `media_id`。本轮通过 110 项定向回归及全后端 `1660 passed / 28 skipped / 8 warnings`，未发起真实公众号请求、未公开发布、未重试旧 Unknown。公众号真实联调仍需单独授权，数据库、启动方式和生产配置未改变。

最新公众号真实联调（2026-10-02）：按用户授权在原验收库私有副本创建了一篇带“请勿发布”标记的新测试稿，只执行一次产品适配器调用，不公开发布、不重试旧Unknown。账号绑定、冻结HTML和368字节短稿门禁通过；token成功后素材上传未获确认，产品正确记录新Attempt为`unknown`、Target为`reconciliation_needed`，没有media_id/remote_id。旧验收记录保持不变，需人工核对后才能继续；公众号2.8、2.9、2.10仍未完成。正式配置、生产库和代码启动方式未改变。

当前开发状态：F7 为 `128/150`（22项未完成）；模型登记切片 `4/4`。本轮本地验收和限定独立复核已通过，不代表真实供应商、公众号整链路或F7整体完成。F8 基线已审计，身份/schema与生产准备尚未启用。当前只在本地 `main` 工作树开发，未推送、部署、执行生产迁移或公开发布。详细进度见 `progress.md`、`findings.md`、`docs/FE_F7_FINAL_LOCAL_GATES.md` 与 `docs/FE_F8_BASELINE_AUDIT.md`。

2026-10-02 本轮更新：独立证据校准先重新开放 routing3.5/registration2.2，再补精确f7d原生PG约束/往返、模型登记真实隔离浏览器保存刷新/409草稿保留，以及默认与显式功能路由。修复 accepted 重放跳过live/字节/父素材检查、同名无效schema约束保护；追加保护literal空格/NOT VALID/partial index。最新全量1661 passed/28 skipped/8 warnings（86.96s）、TypeScript/Vite/FE-P1、strict33/33、Ruff/diff通过；限定独立安全/登记复核APPROVE，两个本地任务现已关闭。下方同日旧计数/描述是历史快照；以此段和门禁文档当前记录为准。无新依赖/迁移版本/启动方式变化，不运行正式迁移、不改正式模型配置、不调用供应商；F7完整验收与F8身份/schema仍TODO。

模型路由 Batch B 本地门禁续批：migration/CAS/capability 既有回归 `88 passed`；不调用供应商、不执行生产迁移，MiniMax 原任务恢复/稳定 receipt key、公众号产品回读和 F8 身份复核仍未完成。

CPA 模型登记验收收口：前端模型路由状态脚本 PASS、相关后端 `32 passed`；CPA `/models` 实际 HTTP 401，登记配置仍是 configured/registered，不标 executable/verified。

2026-10-02并发/崩溃验收：双线程真实execute仅一次本地stub发送、两类子进程退出保留claim/unknown不重发通过；无供应商调用或真实媒体接受。Workflow仍缺发送前真实Attempt关联，design5.3为待确认细化，不是实现。依赖/启动/目录不变，F7仍125/150，F8未启用；详见progress与F7门禁记录。

2026-10-02任务表迁移保护：f7d已有表分支现校验四个FK的列和目标，拒绝缺失/错误目标；隔离正常重复升级/迁移往返及负向探针、既有迁移5项、Ruff/strict33/diff通过。类型/表达式等完整等价审计仍TODO；无新依赖/目录/启动变化或正式迁移，F7仍125/150，F8未启用。

2026-10-02持久任务验收续批：精确f7d在私有SQLite up/down/up、9类负向约束、retained downgrade保护通过；原真实TTS新进程校验、外部owner/缺key/签名篡改/unknown重发拒绝通过，双session交错CAS与晚worker保护在副本验证。PG仅DDL编译，真实并发/原job恢复/媒体接受/Workflow仍TODO，F7/F8未完成。未改业务代码/依赖/启动/schema，也未运行正式数据库迁移，完整证据见progress与docs/FE_F7_FINAL_LOCAL_GATES.md。

2026-10-02认证读取边界续批：设置库存/规划预览不再启动CLI或读取官方认证；明确任务准备与执行前复核才检查请求能力/候选路由的runtime与认证。库存显示尚未核验，不把配置当真实可执行；原任务恢复/接受仍保留冻结认证连续性门禁。三处既有service最小补丁，依赖/目录/启动/schema不变。144相关回归、Ruff/strict通过，新全量1661 passed/28 skipped/8既有warnings（85.16秒）；F7/F8未完成，无真实生成或默认变更。

2026-10-02 CLI配置前端续批：Settings补齐`minimax.cli`选项、本地地址和受控认证引用提示；已有CLI绑定不再误显OpenAI协议，未改配置/默认值。隔离产品浏览器成功验签预览原真实TTS（1.96秒），图片unknown原记录未重发。许可确认待定，未接受入库/开放使用权；F7仍125/150，F8未启用。前端build/性能预算、已有状态回归、strict33/33与diff-check通过；仅UI补丁，不以旧后端全量当本轮验证。依赖/目录/启动不变，详见task_plan/progress/findings。

2026-10-02 F7真实MiniMax续批：image/TTS已接持久任务固定submit_task；图片显式预算尺寸/base64，TTS真实WAV在隔离任务成功（1.96秒），新进程验签回读通过，未入正式素材库。图片另一次25秒截止unknown并保留原任务不重发。Google/Grok/Commons暂缓，F7仍125/150、F8未启用；完整Workflow/媒体接受/浏览器及产品公众号回读仍TODO。独立WeWrite草稿成功不替代产品Publisher验收。目录/证据见[能力矩阵](openspec/docs/项目文档/FE_F7_CAPABILITY_MATRIX.md)；依赖和启动方式不变，正式运行仍需显式稳定receipt key与另获授权的f7d schema，不自动迁移/切默认。

2026-10-01 Video ASR输入续批（仍11/25）：`apps/api/app/services/minimax_cli_provider.py`补精确MP4首音轨→16kHz/mono PCM WAV准备，实际时长≤500秒及请求限额、不裁剪补造，结果仍是需人工接受/显式Master保存的ASR建议。复用ffmpeg/ffprobe依赖，固定file-only命令、4096字节诊断及剩余deadline/进程组回收；无新依赖/表/迁移/默认变更。完整模型路由、认证连续性、Workflow和真实供应商/浏览器仍TODO，不把已注册称verified；沿用既有API启动，未运行用户生产迁移或真实转录。

本批同步修正模型库存：`model_capability_routing.py`保留CLI已加载的合法runtime hash及credential_continuity_unverified原因，但executable/verified仍false。缺安全认证证明不能因为help/dry-run成功显示可执行。独立限定源码复核已通过，不代表用户账号或付费生成验收；未提交、推送、归档或启用F8。

2026-10-01 MiniMax异步协议续批（仍11/25）：`apps/api/app/services/minimax_cli_provider.py`新增固定H3 async提交、V1/V2原job查询及30MiB/DNS固定/HTTPS同源结果下载；`generation_tasks.py`保存签名原file_id。V1安全下载和CLI认证连续性未闭合，真实调用仍blocked，不标verified；Workflow/ASR/浏览器TODO。无新依赖、默认变化或本批迁移，沿用现有API启动和显式f7d授权/receipt key前置；本批没有运行用户生产迁移或真实生成。现有回归不是新协议全覆盖证明。

2026-10-01任务结果/入口续批：视频实际字节decode后验证首视频流与容器时长上限；generation私有结果使用0700目录/0600文件和原子无覆盖落盘，父目录项同步。既有ProviderMediaPanel可显式读取登记模型、选择能力与限额、仅保存准备任务、再独立确认一次执行；列表展示冻结路由并可选原prepared任务。Unknown不清幂等键创建替代任务。真实CLI认证/submit/query、Workflow/ASR和浏览器仍TODO，F7/F8未完成；没有新外部依赖或生产迁移，ffprobe/ffmpeg仍为视频字节验证依赖，缺工具明确拒绝。

2026-10-01持久任务apply增量：一个ProviderGenerationTask表、f7d加法迁移、owner-scoped任务API以及前端查询/预览/人工接受底座已实现；完整MiniMax发送/安全身份连续性、视频时长验证、Workflow/ASR及创建执行UI仍TODO，不将CLI安装视为真实可执行。目录位于apps/api/app/services/generation_tasks.py、routers/materials.py、alembic/versions/f7d000000001_generation_tasks.py和apps/web/src/product/ProviderMediaPanel.tsx。后端1661 passed/28 skipped、前端构建/预算、strict33/33及独立底座复核通过；无真实生成或生产迁移。

部署依赖：仅支持local素材存储；AICS_GENERATION_RECEIPT_KEYS为显式key-ID到64位十六进制稳定密钥的JSON映射，AICS_GENERATION_RECEIPT_KEY_ID选择活动ID（密钥不得进仓库）。启动不自动建任务表；缺schema/key返回明确不可用。迁移需另获授权并明确target f7d000000001，不能用head顺带启用待授权F8。普通启动方式不变，无新外部依赖。

2026-10-01持久生成任务修订：用户同意先修订OpenSpec，方案已归入[模型能力路由](openspec/changes/add-model-capability-routing/design.md)5.2，拟仅新增一个ProviderGenerationTask表，分两批完成本地CLI一次提交/原job恢复/私有结果校验和人工接受入既有MaterialRevision。已确认的是修订范围，不是业务apply或本地生产迁移；旧“零新表”仅对配置/资产/Workflow真源继续成立。规格确认后实施，付费验收/默认媒体路由/生产库迁移另授权；无新代码、依赖或启动变化，F7/F8仍未完成。

供应商协议核查批（2026-10-01）：已取得MiniMax全球H3 create/query，明确V2 URL与V1 file_id两条恢复链；Google Interactions REST steps与SDK便利字段、Omni/Veo两协议、xAI image/video状态已对齐[适配契约](openspec/docs/项目文档/FE_F7_PROVIDER_ADAPTER_CONTRACTS.md)。此前“H3创建读取失败”为历史；native实际dispatch/认证/持久任务/完整license与验收仍未完成。纯文档改动，不启用模型、改默认路由或消耗额度，无新依赖/表/迁移，启动方式不变。

视频恢复审计（2026-10-01）：CLI支持异步任务查询，但当前独立生成入口没有持久任务记录，只有线程池和成功预览内存缓存，重启不能恢复原job。Workflow Attempt不能直接替代独立素材任务；需要先确认持久任务规格修订，不能用假Run或配置表绕过零新表约束。本轮仅诊断/文档，无新代码、依赖、表、迁移或供应商调用；F7/F8仍未验收完成，启动方式不变。

MiniMax官方协议差异收口（2026-10-01）：TTS改用官方完整hd/turbo型号，拒绝系列简称及10000字符以上输入；ASR声明和实际WAV帧时长均限制500秒且不得超过请求上限。官方image/TTS/ASR及旧视频查询/下载证据已记入[Provider契约](openspec/docs/项目文档/FE_F7_PROVIDER_ADAPTER_CONTRACTS.md)，H3创建/认证版本/原任务恢复/完整路由与真实验收仍未完成。未改默认路由，无新依赖、表、迁移或付费调用，启动方式沿用。

MiniMax图片型号实测纠正（2026-10-01）：固定本地dry-run证明当前CLI实际request.model=image-01；binding、发送前与图片runtime hash现校验该实际型号。仅提取白名单model，不展示原始request/headers；不匹配或缺失证据不发送。下方“精确型号仍需解决”是本次修复前记录；任意型号选择、认证版本、实际生成与完整路由仍未完成，不支持的型号继续unavailable。无配置/凭据文件读取、无生成额度消耗或默认模型改动。

MiniMax参数与血缘纠正（2026-10-01）：Video/TTS不再忽略参考素材后发纯文本请求；参考素材或未支持模型在发送前返回unavailable。当前Video只实现MiniMax-H3、MiniMax-Hailuo-2.3的纯文本输入，其余需参考素材的型号不标可执行；TTS/Video默认型号显式传入CLI。8个非法输入及3个未支持型号零网络探针通过；完整参考素材模式仍待实现，不当作产品方案缩减。CLI image暂无独立model选择参数，精确模型绑定仍需解决，不把任意登记型号视为已执行。无新依赖/表/迁移、默认配置改动或付费调用。

MiniMax ASR协议转换（2026-10-01）：固定 `asr-1.0/srt/sentence` 输出转为已有 `status/transcript/cues`，仅接受经既有解码验证的WAV；严格拒绝缺时间戳、重叠/越界、无效时间格式和超长文本，不补造时间。结果仍是建议，须由已有显式保存流程接受，不改Master。MP4音频提取、认证版本绑定、完整路由与真实账号验收未完成；无新依赖/表/迁移、未消耗配额。

MiniMax 输出限制最新修复（2026-10-01）：先前 capture_output 并非硬上限，现改为 stdout/stderr 合计512 KiB的有界读取和deadline，超限/超时结束当前进程组并保持Unknown，不重发；媒体读取限制30 MiB+1。零供应商探针及93项既有回归通过，strict/Ruff/diff通过。完整路由、ASR cue、原视频任务恢复和真实验收仍待完成，下面“缺输出硬上限”为本次修复前状态。无新依赖、迁移、生成额度消耗或默认路由变更。

最新状态纠正（2026-10-01，以此为准）：下述 F8 身份列/迁移/HS256 仍为未接受草案，未取得规定的独立 schema 确认，不激活或升级本地生产库；F7 前置仍未关闭，F8 不计完成。MiniMax 本机 `mmx 1.0.27` 帮助已核对，但现有适配草案尚缺完整 dispatch、输出流硬上限、ASR cue 转换、视频任务恢复和认证版本绑定，不能称完整 executable/verified；默认媒体优先级仍待用户选择。最新后端复跑 1661 passed / 28 skipped / 8 warnings，不等于产品闭环验收。未提交、推送、部署、生产迁移或消耗生成额度；依赖及启动方式未增加。

F8 生产身份第一批（2026-10-01）：已加入现有 User 的 `identity_issuer + identity_subject` 稳定映射和 `f8a000000001` 加法迁移；production 模式使用配置化 HS256 JWT，拒绝 Header/default-user/auto-create，角色只取数据库。production lifespan 不自动建表或写入 seed，需显式 auth/schema-head 配置；health/readiness 使用安全 reason code 和非成功状态，metrics 使用 route template。当前仅本地实现，未配置真实 issuer、未部署、未运行生产迁移。

CPA 厂商/模型登记方案（2026-10-01）：[add-provider-model-registration](openspec/changes/add-provider-model-registration/README.md) 已进入 apply。登记页、CAS 持久化、模型手动补录/发现、Gemini 默认及功能/工作流选择已实现；复用 SystemSetting/CAS，不新增表/迁移/依赖。CPA 已保存为本地登记配置，但 `/models` 实际返回 401，因此不能称为已验证可执行；未发起付费生成请求。工作流异步模型选择与执行 provenance 正在收口，原有显式路由保留。

模型能力/插件路由（2026-10-01）：[add-model-capability-routing](openspec/changes/add-model-capability-routing/README.md) 已获 apply 授权。配置切片与Registry-based共享resolver、带服务端签名的frozen plan/revalidate核心已实现；active User安全只读，编辑仅admin，Settings按需加载。Workflow/Production消费者、真实供应商适配和浏览器验收仍TODO，不能把配置或Registry fixture当真实 executable/verified。当前签名process-local，重启/跨worker需显式replan；生产key/rotation未完成。两大批20项，无新增依赖/表/迁移/启动变化；真实付费验收另授权，Commons暂缓、微信Unknown不重试。接口与验证见 change README，复用 SystemSetting，不复制 Registry 真源。

原生模型适配器（2026-10-01）：`apps/api/app/services/native_model_adapters.py` 已加入 Google/xAI 的版本化协议描述和 MiniMax 的明确 unavailable 注册；默认不加载，需显式 `AICS_ENABLE_NATIVE_MODEL_ADAPTERS=1` 才进入 Registry。当前只做无网络 binding-state/request contract，尚未接入实际供应商 dispatch。精确模型 ID、凭据引用、base URL 和 capability 必须同时满足才可执行；CPA 当前仍按 OpenAI-compatible chat 处理，不能因模型名称自动获得生图/视频能力。协议边界见 [Provider Adapter Contracts](openspec/docs/项目文档/FE_F7_PROVIDER_ADAPTER_CONTRACTS.md)。

MiniMax 本地 CLI（2026-10-01）：`apps/api/app/services/minimax_cli_provider.py` 提供受控 `mmx` Registry Provider，覆盖 CLI 已确认的文字、图片、视频、语音合成和转录命令族；需显式设置 `AICS_ENABLE_MINIMAX_CLI=1` 才加载。应用只传固定参数数组，读取受控临时输出并复用预览→人工接受→MaterialRevision链路；经用户授权后仅受控读取官方配置并生成不可逆 credential epoch，不执行任意脚本，不把帮助信息当作账号/配额/真实生成验证。未执行真实生成或消耗配额。

验收身份纠正（2026-10-01）：产品开发身份header为X-Studio-User；Commons探针使用的X-User-Email未生效，实际走默认管理员，不证明显式身份或用户隔离。Commons保持暂缓；F8 0.1/0.7启动门槛仍有效，无auth/依赖/启动方式变动。

生成接入核查（2026-10-01）：现有配置真源是SystemSetting image/models/plugins；真实媒体注册含OpenAI图片实现，Video/TTS/ASR尚无真实注册。Gemini/Grok/MiniMax需对应协议适配，不能仅替换模型名。复用现有预览/显式接受/MaterialRevision链路；本轮未读取实际配置或凭据、未付费调用，无依赖/启动变化。

最新范围决定（2026-10-01）：用户暂缓Commons，停止其网络排查与导入调用，保留可选/未验证状态，不计验收通过。普通创作素材优先生成，真实截图/新闻照片/事实证据不可用生成内容替代；Gemini/Grok/MiniMax接入须先核对实际生成API/插件配置。F7仍97/105、F8未apply，依赖与启动不变。

最新Commons网络恢复（2026-10-01）：用户授权当前Clash订阅仅追加两个素材域名排除，备份/语法/幂等/唯一差异校验通过；已从UI重新激活并回读生成配置，公网DNS及原host TLSv1.3通过，全局DNS覆写仍false。以下Commons Fake-IP失败为历史。真实素材导入仍待验收，F7保持97/105、F8未apply；未动微信Unknown、业务依赖/启动/生产数据，不公开发布。

最新F8前置核查（2026-10-01）：当前F8仍0/100，尚未apply。隔离只读探针复现health故障200/原始异常和动态metric路径；当前Header默认用户/自动建号、startup写库、仅exports MinIO及本地媒体访问仍需F8实现。issuer/subject→existing User绑定需先审定，不从token email/role推断。F7真实门槛保持97/105，未改VPN/微信unknown或生产；本轮无依赖/启动变化，证据与待办见findings.md/task_plan.md。

最新公共素材真实验收（2026-10-01）：正常产品search接口实际返回502，零素材/verification。系统DNS确认Commons API/media为198.18.0.214/215非公网地址，既有安全策略拒绝；10.2未完成、F7仍97/105、F8未apply。临时测试库/素材目录已回收，微信unknown对账库未动；未改VPN/代码/依赖/启动方式，不重试微信，不公开发布。后续需先恢复这两个素材域名的公网解析，再验证真实bytes导入，不能用夹具关闭真实门槛。

最新本地门禁收尾（2026-10-01）：12项既有lint问题按兼容契约清理，六文件规范化AST相同、独立只读APPROVE；fresh后端1629/28 skipped/9 warnings、TS/Vite/FE-P1、全应用Ruff、strict31/diff、16原生PG及完整迁移往返通过，临时测试容器/卷已回收。F7 10.7关闭，97/105；真实微信仍token成功/封面未知，未重试，F8未启动。无新依赖/启动变化、未push/deploy/生产迁移。以下“全app Ruff12未通过”为历史结果，当前证据见[本地门禁](openspec/docs/项目文档/FE_F7_FINAL_LOCAL_GATES.md)。

最新未知上传排障（2026-10-01）：修复官方Delivery及显式回读丢失固定transport诊断的问题，未来失败只保存白名单code和严格bool/null提示，不写原始异常或凭据，不改变unknown/claim/禁止重试。4项RED→GREEN、初批110相关回归及最终full1629/28 skipped/9 warnings通过，两次独立只读复核APPROVE；当前变更Ruff和strict31/31通过，全应用Ruff仍12项既有问题。上次上传仍未知，本批没有再次读取凭据或发送微信请求。沿用既有表/依赖/启动方式，F7/F8仍未完成。

最新真实短稿尝试（2026-10-01）：已批准810字节“系统联调测试，请勿发布”稿件，经产品API冻结审批后只执行一次官方Delivery。token成功，封面上传asset_0未确认；Target/Attempt=1/1保留unknown/reconciliation_needed，未进入create/read、不公开发布、不自动重试。完整草稿箱验收未通过，F7 96/105、补充17/20、F8未apply。无业务代码/依赖/启动变化、未push/deploy/生产迁移。证据及对账TODO见[短稿验收](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)；以下“真实请求0”为历史记录。

最新整阶段本地复核（2026-10-01）：修正后最终全后端1625/28 skipped、TS/Vite/FE-P1、17原生PG及完整F7迁移往返通过，临时容器/卷已回收。全应用Ruff仍有12项HEAD既有问题，36个改动Python文件通过；不混称全PASS。独立Delivery复核APPROVE，Security复核提出Connector执行代码身份与Commons interning指纹漂移，4 RED后最小修正、81相关通过，独立修正复核APPROVE，10.9关闭/F7现96/105。用户已批准明确“请勿发布”短稿/封面，真实请求仍0；F7/F8未完，依赖/启动不变。证据与TODO见[整阶段本地门禁](openspec/docs/项目文档/FE_F7_FINAL_LOCAL_GATES.md)。以下等待测试稿确认的说明为历史。

最新短稿验收入口（2026-10-01）：`apps/api/scripts/accept_wechat_short_draft.py` 只接既有隔离产品库和精确已审批Candidate，默认预检rollback，显式execute才走官方prepare/Attempt/execute；不创建/迁移库、不启用一般合同、不用旧CLI。固定批准的两份账号配置只进当前进程，显式身份key必须提供。独立复核提出SQLite URI路径、参数回显、准备后异常三项缺口，4个RED后修复；修复后full1620/28 skipped/8既有warnings、其后追加Unknown后23入口回归/Ruff通过，独立窄复核APPROVE。strict31/31及diff通过。测试稿/封面确认待用户回复，无真实账号请求。依赖/产品启动方式不变，验收步骤和恢复边界见 [短稿验收](openspec/docs/项目文档/FE_F7_SHORT_DRAFT_ACCEPTANCE.md)；F7/F8及全产品验收仍未完成。

最新短稿实验接入（2026-10-01）：内部显式管理员授权原子准备精确Target/Attempt，短期签名绑定账号/Candidate/hash/actor/runtime；每步复用live锁和claim，DNS/TLS完成后再验有效期，worker启动持久防重。普通HTTP授权仍拒绝、一般合同gate保持false，不生成一般verified。103相关回归、1598后端/28 skipped、16原生PG/guard、OpenSpec strict31/31、Ruff/diff通过，独立本地窄复核APPROVE。真实账号请求仍为0，2.8未完成/17/20不变，inline保守上界会拒绝，不能冒充长文或真实平台验收。无新表/依赖/迁移，启动方式不变。

最新实验基础：既有wechat_official_render.py已提供<2048 UTF-8字节正文和URL展开保守上界纯校验，6 RED→19 render回归通过，范围Ruff通过。尚未接入受限scope/Delivery/transport，也未真实请求；inline上界当前会拒绝，不冒充内文图片验收。一般合同gate仍false，启动/依赖/迁移不变。

最新短稿实验授权（2026-10-01）：用户批准指定既有公众号最终HTML UTF-8正文<2048字节的token/上传/草稿创建/回读实验，禁止公开发布和长文放行。例外已归入active OpenSpec，受限产品scope实现/真实验收仍待完成，一般合同gate不变，17/20不提前勾选；无新依赖/迁移或启动方式变化。

最新网络复测（2026-10-01，用户重启VPN后）：微信官方域名返回公网地址，直接连接该次解析地址、使用原域名SNI的TLS证书校验通过；没有发送HTTP或账号请求。DNS不再是当前阻塞。以下DNS失败说明保留为历史，不证明订阅脚本是恢复原因。官方正文限额冲突仍未解除，Publisher合同gate保持关闭，真实草稿验收/F7/F8仍未完成；依赖与启动方式不变。

最新Clash最小修复：用户批准当前订阅脚本追加api.weixin.qq.com排除，原文件已备份，语法/幂等/配置结构验证通过；保持全局DNS覆写关闭、8项上游与其他配置不变。生成配置尚未重应用，需用户在当前订阅打开扩展脚本并保存后再验DNS/TLS；未验证真实公众号，未变更本项目依赖或启动方式。

2026-10-01用户已授权复用new_media/WeWrite现有账号进行真实公众号草稿箱测试，不公开发布。配置存在且账号一致，但官方域名实际解析到198.18.1.55，公网安全预检拒绝；另有正文限额合同待确认。尚无账号API/上传/草稿调用，不算真实验收通过。依赖与启动方式不变，详情见progress.md；不要将凭据写入仓库。

最新能力矩阵已按2026-10-01实际descriptor刷新：官方账号隔离Publisher已加载，合同gate仍false；Video/TTS/ASR暂无loaded实现。纠正“官方实现不存在”的旧说明，明确实现/配置/真实验证三层。F7仍95/105、补充17/20、F8未apply；整阶段官方本地安全只读复核APPROVE，真实验收/提交/归档不代关。不改业务/依赖/启动方式，不探测账号或读取secret。详见[能力矩阵](openspec/docs/项目文档/FE_F7_CAPABILITY_MATRIX.md)。

最新2026-10-01本地验收：跨项目共享Profile真实PG竞争通过，相反锁序mutation能精确检出；准备后凭据轮换及跨角色/用户账号拒绝补齐。补充方案17/20，14PG/guard、1PG迁移、82相关、1564后端/26 skipped、41隔离UI、build/性能/strict/Ruff/diff通过，独立本地增量复核APPROVE。剩余真实平台/阶段提交/授权归档未关，F7/F8未完成；无业务/依赖/迁移或启动方式改变，本輪测试库/Vite已回收。以下14/20等为历史。

最新原生PostgreSQL验证：新增`apps/api/tests/test_f7_wechat_official_postgresql.py`，6项真实事务竞争/撤权锁等待与7项连接隔离guard通过；账号迁移往返与绑定竞争另1项通过。仅transport夹具，无真实公众号调用，临时库已回收。现有启动方式不变；opt-in必须使用localhost15439/aics_account_test、postgresql+psycopg且URL无query。跨项目共享profile锁顺序仍TODO，补充方案仍14/20、F7/F8未完成；最终全量与复核见progress.md。

最新双账号与恢复批：同角色A/B官方Delivery→Receipt隔离及A轮换不影响B已验，修复草稿Receipt被旧逻辑误记为发布历史；Review新增已知草稿显式回读、running中断人工对账，归档禁用，无create/自动重发。API80定向、9项隔离恢复UI与构建预算通过；最终全量/独立复核见progress.md。范围仍14/20，PG/真实账号等TODO未关闭；只修改既有service/Review/验收脚本，无新依赖/迁移，启动沿用。

最终收口追加Receipt未决Attempt的DB锁/新鲜查询，封住stale目标状态旁路；ZIP/package既有v5 action gate不放宽，UI禁下载。最终1554 backend/19 skipped、68定向、36隔离UI、TS/Vite/FE-P1/strict31/Ruff/diff及修复复核APPROVE；无真实调用或提交推送，F7/F8未完成，临时验收服务已停止。

最新内文图片Delivery验收：补充方案14/20，真实带图Master→适配→冻结审批→隔离上传/回读验证精确字节与固定HTML槽位，cover后inline撤权/文件变化拒绝后续create。Delivery定向18 passed；全量/窄复核结果见progress.md。无业务规则/依赖/迁移变更；双账号、PG竞争、恢复UI与真实平台仍TODO，F7/F8未关单。

事实驱动的内容生产系统：把结构化数据、研究笔记、文件、URL、人工观点整理成 **FactPack**，面向抖音 / 小红书 / 公众号生成内容，经事实校验与人工审核后导出；公众号可进一步自动写入官方草稿箱。

长期产品目标以 [`03_ai_content_studio_PRD.md`](openspec/docs/03_ai_content_studio_PRD.md) 为准；其中 §3 的三渠道是首选样本，§3.1 已补入原对话整理的 11 平台文章/图文 V1 目标，并保留抖音脚本。`04_ai_content_studio_execution_plan.md` 是旧版执行参考，边界澄清稿见 [`docs/AI_CONTENT_STUDIO_REQUIREMENTS_REFINED.md`](openspec/docs/项目文档/AI_CONTENT_STUDIO_REQUIREMENTS_REFINED.md)。

### FE-F7 能力集成与交付（本地实施中）

最新官方Delivery批：`wechat_official_delivery.py`接入审批后exact官方账号、durable私有claim/逐步live锁、partial metadata及严格回读；新增`POST /delivery-targets/{id}/official-readback`只读已知草稿ID、不再次create。崩溃需人工exact Attempt+依据对账，not_delivered后才允许新编号显式执行；旧候选无render拒远端且不补字段。十五本地链路/SQLite双连接prepare、156定向、1543全后端/19 skipped、构建预算/strict31/31/Ruff/diff及独立修复复核通过，补充方案13/20。PG授权/执行竞争、双账号完整Delivery、恢复UI/浏览器和真实验收仍TODO；F7仍95/105、F8未开始。无新依赖/表/迁移/真实请求/commit/push/deploy；启动沿用，API复跑`tests/test_f7_wechat_official_delivery.py`。以下10/20为历史。

最新官方传输批：`wechat_official_transport.py`提供token/精确图片上传/草稿创建/回读五类有界单次请求，固定公网IP+原host TLS，不代理/重试/重定向；`wechat_official_render.py`只替换冻结资源槽并严格比对回读。URL错误脱敏与代码指纹失效经RED→GREEN和独立窄复核通过。新全后端1528 passed/19 skipped、141定向、构建/FE-P1、strict31/31、Ruff/diff通过，补充方案10/20。DB/CAS Delivery接入、真实账号与F7/F8终验仍TODO，远端gate仍false；无新依赖/表/迁移、真实请求、commit/push/deploy。启动沿用，复跑API `tests/test_f7_wechat_official_transport.py`；以下9/20等为历史记录。

最新收口：Settings和Identity账号连接统一遵守服务端完整祖先层级read_only；品牌/角色/账号归档都禁写，缺状态也禁写。最终1501后端/19 skipped、139定向/1 skipped、15账号+12冻结预览UI fixture、构建预算、strict/Ruff/diff及独立复核通过；补充方案9/20。官方transport/Delivery、missing-render远端gate与真实验收仍TODO，F7仍95/105、F8未开始。无新依赖/迁移/真实账号动作或push/deploy，启动沿用；以下13项/1498为本轮修复前记录。

最新Settings批：渠道分区可选择所属“角色/账号”，复用`CapabilitySettings.tsx`→lazy `AccountPublisherPanel.tsx`，viewer只读、管理员显式保存，账号A/B配置隔离；读取不取token/secret，不探测。既有账号脚本13项、冻结预览脚本12项隔离门禁及全后端1498/19 skipped、构建/预算/strict31/31通过。Batch A独立复核待结论，官方transport/Delivery和真实验收仍TODO。无新依赖/迁移，依赖与启动沿用；复跑`F7_ISOLATED_ACCEPTANCE=yes NODE_PATH=<Playwright依赖目录> node apps/web/scripts/fe-f7-account-binding-ui-acceptance.mjs`，需本机隔离Vite15391。

最终本轮图片链路窄复核APPROVE，12项隔离UI门禁通过（403/字节预算/哈希/LAN/实际decode），原有全量1498/19 skipped结果不因fixture转为真实平台verified。补充方案保持6/20，Batch A整体/官方transport/Delivery/Settings及F7/F8终验仍TODO；原始规格包保留。无push/deploy/生产迁移。

当前公众号正文图片适配已本地实现：`channel_variant_documents.py` image block、`channel_variants.py`精确source/素材映射、`wechat_official_render.py`冻结HTML位置槽，Review/本地ZIP复用实时权利。`OfficialArticlePreview.tsx`+`previewByteHash.ts`提供LAN兼容哈希校验和隔离图片预览，不改manifest。最新全后端1498 passed/19 skipped、10项UI fixture、构建预算/strict31/31/范围Ruff通过；完整Publisher/F7/F8未完成。无新依赖/迁移，启动方式沿用；复跑API `tests/test_f7_wechat_official_render.py tests/test_f6e_freeze_v5.py`，UI仍使用下述15391隔离脚本。此前inline TODO记录为历史，真实上传/readback仍TODO。

最新审核预览子集：`apps/web/src/product/OfficialArticlePreview.tsx`显示冻结公众号HTML、hash、素材槽和不可用原因，sandbox/CSP隔离脚本与外部资源；旧候选无字段不变。补充方案仍6/20，inline定位、完整交付及真实平台尚未完成。沿用依赖和启动方式；UI夹具脚本`apps/web/scripts/fe-f7-official-preview-ui-acceptance.mjs`需隔离Vite15391和`F7_ISOLATED_ACCEPTANCE=yes`，不调用微信。当前55项后端定向、构建/预算及独立窄复核通过，不把旧全量作为本轮结果。

最新补充方案6/20：账号级runtime/短期token缓存、独立implementation/account验证指纹已通过隔离回归与窄复核。新服务`apps/api/app/services/wechat_official.py`需要每账号环境凭据引用及对应VERSION，另需跨worker稳定的`AICS_WECHAT_RUNTIME_IDENTITY_KEY`；只说明变量名称，不在UI/文档保存值，缺失不可用。读取库存不读secret，新official远端仍恒不可执行。`wechat_official_render.py`已将正文/cover子集在v5审批前冻结，inline位置和前端预览仍TODO。全后端1487 passed/19 skipped、构建预算/strict31/31/范围Ruff/diff通过，本轮无新迁移/依赖/业务表、浏览器重跑或真实账号动作。沿用原启动方式；复跑`cd apps/api && .venv/bin/python -m pytest -q tests/test_f7_capability_persistence.py tests/test_f7_wechat_official_render.py tests/test_f6e_freeze_v5.py`。

账号关系已确认：一Persona可有多个账号，每个真实账号只属于一个Persona，不跨角色共享。[官方草稿Publisher补充方案](openspec/changes/add-account-bound-wechat-draft-publisher/README.md)已获本地apply批准。用户确认权限开放，并批准将官方正文限额冲突保留为远端执行门槛；本地绑定、账号级安全配置与Identity面板已实现，新增加法迁移f7c000000001仅在隔离SQLite/PostgreSQL验证，默认库/生产库未升级。configured不是verified，未取token/上传/创建草稿。实际全后端1478 passed/19 skipped，构建预算及8项UI fixture gate通过；runtime/render/Delivery与真实验收仍待完成，F7/F8未关单。

账号接入文件：`apps/api/app/services/content_identity.py`、`apps/api/alembic/versions/f7c000000001_account_platform_identity.py`、`apps/web/src/product/AccountPublisherPanel.tsx`。最终9项UI fixture gate通过，新增历史导航草稿恢复；补充方案5/20。沿用原启动方式和依赖，凭据只用账号级环境引用，不写入文档。复跑：`cd apps/api && .venv/bin/python -m pytest -q tests/test_fe_f3b_content_identity.py tests/test_migrations.py`；真实PG门禁须显式指定隔离测试库。

剩余门槛复查（main@c216e41）：真实bootstrap的Video/TTS/ASR实现列表为空；Commons新请求仍被非公网DNS拒绝。公众号账号绑定且不改稿的新实现方案尚待选择，真实账号/付费Provider动作未授权。F7仍95/105，F8前置不变；仅记录证据，不新增依赖/迁移或修改启动方式。

最新安全收口：F7 typed入口及实际素材搜索/生图包装入口的非法输入只返回固定安全422，普通CRUD不改；ASR显式保存最终receipt/runtime与commit共用进程配置guard，漂移回滚Master/refs/event。61定向、最终全后端1485 passed/2 skipped与独立两项窄复核通过，构建/FE-P1/strict30/30/范围Ruff通过；无新依赖/业务表/迁移，启动不变。复跑：`cd apps/api && .venv/bin/python -m pytest -q tests/test_f7_media_acceptance.py tests/test_f7_asr_suggestions.py`。F7仍95/105，真实Provider/账号、阶段终验和F8未完成，不以本地测试代替外部验收。

最新迁移实测：独立PostgreSQL16.15实际验证到f7b000000001，四项往返/旧验证保留/两类历史拒降级通过，不使用旧f7a结果代替新迁移。临时容器已回收；真实Commons搜索被当前DNS非公网198.18.0.41拒绝，尚无下载/导入成功。详细证据与未覆盖范围见[最新迁移与公共来源验收](openspec/docs/项目文档/FE_F7_MIGRATION_REVALIDATION.md)。没有新代码/依赖/迁移，启动方式不变，F7仍95/105、F8未apply。

当前本地任务95/105：三项安全缺口整批修复并通过独立窄复核；旧workflow新发布一律要求Delivery Router、typed读取逐跳绑定验证IP/TLS原host、媒体accept最终runtime复检与当前进程配置串行。新增实际门禁150定向/1470全后端（2 skipped）、build/FE-P1、strict30/30通过，范围Ruff保留已存在workflow告警例外，详见[本批验收](openspec/docs/项目文档/FE_F7_BATCH_B_ACCEPTANCE.md)。无新依赖/业务表/迁移，原启动方式不变。七脚本52项本地浏览器历史证据未在本批重跑；实际渲染/本地ZIP与fixture区分见[浏览器再验收](openspec/docs/项目文档/FE_F7_BROWSER_REVALIDATION.md)。真实供应商、账号绑定公众号上传、整阶段终验和F8仍待完成，不能把窄复核当F7通过。

- 最新调用前权利修复：`provider_media.stage`持有project/source/parent权限锁至受控Provider调用结束，finally释放DB后再缓存；SQLite撤权先赢时零供应商调用。两个失败回归后修复，125定向/1448全后端（2 skipped）、构建预算/strict/Ruff/diff通过；不借本批关闭整阶段review或真实外部验收。复跑 `cd apps/api && .venv/bin/python -m pytest -q tests/test_f7_media_acceptance.py`；完整环境和限制见[共享媒体记录](openspec/docs/项目文档/FE_F7_BATCH_B_ACCEPTANCE.md)。没有新增依赖/迁移/业务对象或本批浏览器结果。

- 受控读取与能力矩阵（F7 94/105）：现有typed Connector和Commons在读取前拒压缩；Connector总deadline跨redirect/body/空响应，不改legacy direct safe_fetch。11新回归、84定向、1446全后端/2 skipped、构建预算/strict/Ruff/diff及窄复核通过；无新依赖/迁移，复跑 `cd apps/api && .venv/bin/python -m pytest -q tests/test_f7_capability_persistence.py tests/test_f7_material_search.py tests/test_f7_openai_image_provider.py`。结构、真实实现/fixture/外部未验证、默认旧库抽查与长期TODO见 [能力矩阵](openspec/docs/项目文档/FE_F7_CAPABILITY_MATRIX.md)。WeWrite真实账号绑定和不可改稿上传仍缺失，Video/TTS/ASR真实实现/平台验收不能由协议替代；F8未apply。默认旧库未迁移，不误称运行/生产已升级。

- 已配置图片原生路径（F7 92/105）：管理员现有 AI 生图设置明确选择 OpenAI 与支持的 exact model/size/HTTPS `/v1`/key；现有素材生成按钮进入私有 PNG 预览，人工权利确认后才写精确版本，不改 Master。实现位于 `services/openai_image_provider.py`，复用 Registry、stage/accept 与现有 UI；无新依赖/表/迁移，原生设置不写 WeWrite 全局配置。单次调用、无重试/回退、public-IP pin、响应/时间上限和轮换失效；全后端1435/2 skipped、52定向、构建预算/strict/Ruff/diff与窄复核通过。报告 [原生图片接入验收](openspec/docs/项目文档/FE_F7_NATIVE_IMAGE_ACCEPTANCE.md) 含配置/复跑命令；真实付费厂商与账号验收仍TODO，未做新版浏览器验收，不把 Mock transport 称外部verified。

- 人工对账闭环：Unknown 保留原 Attempt，核验说明只提交/保存 SHA-256 摘要；最新 Attempt 校验、目标锁、重复决策幂等，确认已交付原子新增精确人工 Receipt，不自动写已发布历史/verified 或重发。错误输入固定安全原因，不回显秘密；源码独立窄复核与五项 UI fixture browser gate 通过，非真实账号验收。接口沿用 `delivery.py`，UI 在 ProjectReviewCenter，复跑 `F7_ISOLATED_ACCEPTANCE=yes NODE_PATH=<Playwright依赖目录> node apps/web/scripts/fe-f7-reconciliation-ui-acceptance.mjs`（需隔离 Vite 15671）。本批无新增依赖/表/迁移；当前 F7 91/105，全后端1407/2 skipped、定向109、构建预算/strict/Ruff/diff通过；阶段外部验收继续待办。

- 媒体 Renderer 范围闭环：管理员明确核对真实 stage 后记录 renderer/schema/channel/form/MIME 的 24h 验证；editor 可走独立输出入口，每次调用与接受重验 current Master/runtime/Profile/rights/expiry/revocation。撤销留史，不改素材/Master；per-stage lock 与 registration DB lock 关闭 cache/DB 反向等待和撤销提交窗口。库存保持 not_probed，只展示记录和请求权限。实际 Graphic 13 browser gate、1400 全后端/2 skipped、106 定向、预算/strict/窄复核通过；F7 90/105，真实 Video Renderer 和外部 Provider/Publisher 不冒充完成。接口、目录和复跑见 [`docs/FE_F7_MEDIA_RENDER_SCOPE_ACCEPTANCE.md`](openspec/docs/项目文档/FE_F7_MEDIA_RENDER_SCOPE_ACCEPTANCE.md)。

- Graphic Studio 前批 UI 已接通：安全只读库存、实际 PNG 预览、明确权利接受、精确项目素材重读、本地 final binding、单独 Master save / 人工确认；接受后读失败不重复接受，dirty/历史/viewer 禁止渲染，迟到结果丢弃。前批十项 Chrome gate、全后端 1374/2 skipped，当前范围验证/editor 执行已由上方新批扩展。历史验收见 [`docs/FE_F7_GRAPHIC_RENDER_UI_ACCEPTANCE.md`](openspec/docs/项目文档/FE_F7_GRAPHIC_RENDER_UI_ACCEPTANCE.md)。

- 本地图文 Renderer 实现：`graphic.chromium@1` 显式配置 Node/Playwright/Chromium/字体后按当前 Graphic v2 画布生成真实 PNG；不默认使用 Codex 私有 runtime，不自动 verified/attest，不修改旧 Text/Video 路径。当前单字体仅 normal/400，缺字或样式拒绝而非替换。配置/启动和限制见 [`docs/FE_F7_LOCAL_GRAPHIC_RENDER_ACCEPTANCE.md`](openspec/docs/项目文档/FE_F7_LOCAL_GRAPHIC_RENDER_ACCEPTANCE.md)。精确范围验证现已由上方新批接通，真实 Video 仍 TODO。

- 需求背景：让数据源、模型/素材能力与远端 Publisher 只有在精确版本、配置、账号及动作范围真实验证后才可执行；本地包不冒充远端发布。
- 目录结构：标准变更在 `openspec/changes/fe-f7-capability-integrations-delivery/`；统一 Registry 为 `apps/api/app/services/content_harness/registry.py`，安全验证模型/服务在 `apps/api/app/models.py`、`apps/api/app/services/capability_integrations.py`，加法迁移为 `apps/api/alembic/versions/f7a000000001_capability_verification.py`。
- 已完成：十类新 Registry kind 保持旧版本解析；CapabilityRegistration/CapabilityVerification 分表和留史拒降级；内部 Publisher 范围/指纹/撤销判定；Connector 失败与 WeWrite 子进程错误安全原因码。受控 API Data Source 已通过注册 ID/版本映射到精确 Endpoint，管理员可配置并做真实 GET 探测，验证后可手工拉取或由 Data Node 执行；只读清单不触发网络。该路径逐块限制响应体至 1 MB、每页 500 条且最多 20 页，单次请求至多 10 秒；旧 Connector 路径保持原样。快照只含映射后的 Fact 字段，数值变化即使陈述不变也会产生新快照并使下游 stale；配置或凭据版本变化、空结果/失败探测或后续拉取失败都会使旧验证不可执行，成功重探测或显式新 profile 版本才可恢复。
- 第一批接入：Settings 既有数据源/渠道分区新增 lazy 能力面板；可保存 API profile、显式探测，并在 Data Node 选择固定版本执行。只读库存不读秘密配置、不发网络；失败追加准确 scope 验证失效，普通旧 pull 成功不恢复验证。v5 公众号已具备冻结正文/标题与真实 PNG/JPEG 封面的确定性投影，但现有 WeWrite 会改稿且不能证明实际账号绑定，因此新远端交付仍未开放，Settings 明示 unavailable、API 人工确认也不能放行。真实公共 GET 已生成 Source/Fact/DataSnapshot；没有真实远端发布。
- 第二批接入：`provider_media.py` 提供有界、操作者隔离的临时预览与显式许可/权利接受，接受才原子保存既有 MaterialRevision 和可选项目引用。新素材库与旧生成入口共享 lazy `ProviderMediaPanel`，不会自动入库或改 Master。媒体按真实字节解码；来源素材在事务内锁定并重验权利。服务重启后预览失效，不冒充持久状态。新增 Pillow 依赖，视频验证需本机 ffprobe/ffmpeg；接口没有已加载的合格 Provider 时明确 unavailable。
- 搜索批已完成：`material_search.py` 实现受控 Wikimedia adapter、安全短期候选和明确下载；Assets/旧素材搜索共用 lazy `ProviderSearchPanel`，接受仍复用素材权利边界。最多 10 候选、1 MB 元数据/5 MB 媒体，只有精确确认来源许可与完整署名后才保存版本；不自动改 Master。验收见 `docs/FE_F7_SEARCH_ACCEPTANCE.md`。
- Renderer 批已完成：`renderer_capabilities.py` 复用实际 Text v1/v2 adapter，管理员在生产页明确渲染验证，Settings 投影安全范围；注册实现与事件 scope/Profile 指纹分离，绑定实际 callable。新增 `f7b000000001_renderer_scope.py` 仅拓宽既有验证 CHECK，保留旧行/索引/FK，留存 Renderer 证据时拒降级。Graphic/Video 仍标人工成片，不伪装自动可执行。验收见 `docs/FE_F7_RENDERER_ACCEPTANCE.md`。
- 共享消费 / 配置指引已完成：Text 配图与 Video timeline 引用同一个搜索接受的精确 MaterialRevision，撤权阻断两者 checks / freeze；Settings 模型分区独立 lazy ProviderGuidancePanel 只读显示五类协议与配置指引，已加载不等于可执行 / verified，不提供假 Save。验收见 `docs/FE_F7_SHARED_MEDIA_GUIDANCE_ACCEPTANCE.md`。
- 媒体 Renderer 基础契约：`media_renderers.py` 提供管理员明确 media-render-previews，绑定 current Master/hash/context/Profile/canvas 和 exact installed renderer；接受复用原 stage/raw/accept，真实解码字节只写 upstream MaterialRevision/项目引用。来源权限/CC BY、读取前30MB、安全路径、重复层去重及提交前撤权有回归；不生成 Master/自动 attestation，也未装入假的 renderer。见 `docs/FE_F7_MEDIA_RENDER_BOUNDARY_ACCEPTANCE.md`。
- 待完成/TODO：F7当前95/105；legacy远端旁路、DNS绑定、accept runtime竞态与本批validation/ASR窗口已窄复核关闭，真实供应商/账号及整阶段终验仍待完成。PostgreSQL迁移已实际验证，不代表业务并发/跨worker配置验收；Commons被非公网DNS拒绝，WeWrite新远端runtime保持unavailable，F8未apply。
- 关键设计决策：只存安全身份与证据摘要，不存 secret、原始响应或签名 URL；验证事件追加，配置变化/撤销让旧验证失效。F6E canonical/归档尚待单独授权。
- 依赖与启动方式：沿用 `apps/api` 既有 Python 环境、FastAPI 和 Alembic；测试在 `apps/api` 运行 `.venv/bin/python -m pytest tests/test_f7_capability_persistence.py tests/test_migrations.py -q`。只在隔离库执行迁移；不推送、部署或执行生产迁移。

### FE-F6E 渠道变体检查（本地实施验收完成；规格归档待授权）

本地前端已接入 Matrix 限量只读建议/所选 Unit 确认、Production 独立 lazy Variant 面板，以及按冻结目标和渠道系列工作的 v5 Review。Variant 可预览、显式保存、回看版本/差异、运行检查并冻结；预览与重试不写业务对象。图文卡片的准确图片和口播脚本的估算 SRT 在 Review 有区分展示，交付仍只允许人工本地包。前端构建、首包预算、跨形态隔离浏览器与最终门禁已通过；不代表真实平台发布。

本地后端已走通 Graphic v2→小红书真实图片包、Video v2→抖音脚本/估算 SRT 包，以及带精确 FactPackItem 引用的 Text v2→公众号文章/X Thread/X Single 人工包；图片/B-roll 均按精确素材字节入包且撤权后禁止再取。抖音脚本不要求已有成片，但直接 Video v4 冻结仍要求真实最终渲染。同系列 Variant 保存与 v5 Freeze 的双连接并发防重、跨项目 raw-ID 和归档只读边界已有后端回归；五形态本地包已保留准确媒体、引用和非空披露声明。v5 审批要求精确来源 warning 的人工处置，历史包下载会重验后续来源检查；同一候选的不同账号授权与 unknown 对账状态互不覆盖。全形态隔离浏览器已验收。未启用远端发布。

- 需求背景：一个已保存的渠道变体只有在来源 Master 当前、必要检查有效，且目标形态/素材/证据检查通过时，才可能进入后续 Candidate v5 冻结。
- 目录结构：`apps/api/app/services/channel_variants.py` 负责项目授权后的 Variant 历史、只读来源门槛和追加式检查；`channel_adapters.py` 负责五种受控形态的确定性成品投影；`candidates_v5.py` 装载并构建 v5 清单，`project_review.py` 提供冻结；规格位于 `openspec/changes/fe-f6e-channel-variants-content-matrix/`。
- 已完成：来源 Master 的上下文与检查状态进入 Variant `ready` 投影；`variant_package` 验证受控 Adapter 的确定性成品投影并记录哈希。v5 manifest builder 已接服务端 DB 快照和项目级 Freeze；仅当前且已通过检查的 Variant 可冻结，重复请求幂等，旧 Draft/Master/Workflow 来源列保持空。v5 内容审批按 Variant 系列判定当前性；交付授权仅允许本地包/人工交接，ZIP 从冻结 v5 内容和实时验证的精确素材字节生成，不回退旧 schema。已有授权可读取历史包，但仍须通过实时公开权利与来源完整性验证。Review 后端现从冻结 v5 内容投影文字/图片卡片/脚本、检查与同系列差异，媒体预览读取精确版本并实时验证公开权利及字节；Project Versions/Overview 保留同 Unit 多渠道系列及未知交付优先级。Matrix 新增限量、授权、无写入的建议 API，确认仍须走现有 Unit API。Variant 历史可按同系列稳定 ID 比较改动；模型建议的真实 `LLMRun` 经显式保存和冻结二次校验，只冻结安全摘要。Text v2 原稿的未改动段落引用可按精确 FactPackItem/checksum/range 映射至公众号文章和 X；引用被静默丢弃或位置变动时拒绝确定性继承。
- 待完成/TODO：F6E canonical 主规格同步/归档待单独授权；Matrix 真实成本/价值估计及远端 Provider 属后续范围，不以未知估值冒充排序。Matrix 历史表现只展示同渠道同形态且实际存在的指标覆盖，不生成跨平台评分；无指标与无历史分别标为 missing/unknown。模型辅助适配已接现有 Provider/LLMRun：建议只读，显式接受保存时核对当前来源/Profile/Adapter、操作者及 canonical 输出哈希；无可用或合格 Provider 时返回不可用，不伪称适配成功。
- 关键设计决策：channel-neutral Master 的目标平台检查由 Variant 承担，不以 v4 直接冻结资格替代来源门槛；检查结果追加保存，读取时仍进行实时来源与权限漂移判断。v5 清单只接受服务端提供的有界 canonical 快照，绝不沿用 Draft/Master 作为 Candidate 来源指针。
- 依赖与启动：沿用现有 FastAPI/SQLAlchemy 环境；在 `apps/api` 运行 `PYTHONPATH=. .venv/bin/pytest -q tests/test_f6e_freeze_v5.py tests/test_f6e_candidate_manifest_v5.py` 进行定向回归。本切片不增加依赖或迁移；Matrix 服务位于 `apps/api/app/services/project_matrix.py`、路由位于 `apps/api/app/routers/project_read_models.py`。

### FE-F0-F1 前端产品骨架（2026-09-27）

- 需求背景：以 [`AIContentStudio_产品战略与总体架构蓝图_NorthStar_V2_2026-09-26.md`](openspec/docs/AIContentStudio_产品战略与总体架构蓝图_NorthStar_V2_2026-09-26.md)、[`AIContentStudio_Frontend_Product_Contract_V1_2026-09-27.md`](openspec/docs/AIContentStudio_Frontend_Product_Contract_V1_2026-09-27.md) 和 V5 原型为方向，本切片按 [`AIContentStudio_WORK_HANDOFF_FE-F0-F1_2026-09-27.md`](openspec/docs/AIContentStudio_WORK_HANDOFF_FE-F0-F1_2026-09-27.md) 建立项目驱动的前端入口；不表示 PRD 全部完成。
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

- PRD/需求背景：补全生产前的“为什么现在做”决策层和日常工作台。Opportunity 不是 Topic；Home 是现有业务事实的 Projection。长期契约见 [Opportunity 主规格](openspec/specs/content-opportunities/spec.md) 与 [Home 主规格](openspec/specs/content-home-workspace/spec.md)，另四份 FE-F0/F1、FE-F3A、FE-F3B、FE-F4 主规格已同步。实施记录见 [FE-F5A 归档](openspec/changes/archive/2026-09-28-fe-f5a-home-opportunity/proposal.md)，完整步骤见 [实施计划](openspec/docs/项目文档/superpowers/plans/2026-09-28-fe-f5a-home-opportunity.md)。
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

### FE-F6E Channel Variants + Content Matrix（本地实现与隔离验收完成，待主规格同步/归档授权）

- PRD/需求背景：North Star 要求在可复用 ContentMaster 与审批候选之间形成真正的渠道适配层；原先缺少持久 ChannelVariant，Project Matrix 只能直接管理 ContentUnit。F6D 门禁与 F6E 独立规格复核已通过，F6E 正按标准 change 做 backend-first 实施。
- 目录结构：`openspec/changes/fe-f6e-channel-variants-content-matrix/` 包含 proposal、design、tasks、新 ChannelVariant 规格及 Matrix、Production Core、Project 读模型、Review、FE-P1 五份 delta；`apps/api/app/models.py` 与 `apps/api/alembic/versions/f6e000000001_channel_variants.py` 承接四表及 Candidate 链接，`apps/api/app/services/channel_adapters.py` 和 `channel_variant_documents.py` 承接 Profile 能力边界与五种 canonical payload，`apps/api/app/services/channel_variants.py` 与 `apps/api/app/routers/channel_variants.py` 承接项目级历史读取、非持久化适配预览、Variant 写入和检查。用户原总包不改。
- 已完成：规格界定非写入 Matrix 建议、追加式 Variant/精确引用/检查、Candidate v5、Review/Approval/本地包分派与旧 v3/v4 保留；已标记 superseded 的 V1 交付变更只作为七个历史场景和 PRD §15/§16 的保留验收来源，不重新激活、不冒充已验收。2026-09-29 独立 SPEC 反馈后补定五个边界：版本化 canonical Variant payload、首批 v2 Master→form/`artifact_kind` 兼容矩阵、v5 唯一 Variant source pointer 与缓存投影列校验、复用成功 `LLMRun` 的安全血缘，以及 superseded 状态。旧 `x_thread/thread` 保持 v3/v4 行为但不作为 v5 目标。v5 跨渠道授权比较冻结 Variant 目标而非来源 Unit 渠道，仍保留身份/账号约束。已完成 F6E 0.3/0.4 基线与旧 V1 验收义务映射（见 `findings.md`），未将其视为功能验收。首批计划内加法模型和迁移已落地，含四个 Variant 表、Candidate nullable 链接及精确 published Profile 版本 FK；SQLite/临时 PostgreSQL 迁移门禁已通过。公众号文章、X 推串与单条已有保守的 Text v2 确定性适配器；公众号文章可显式选择或继承项目可见的精确封面引用，X 仍限无素材子集；小红书图文仅对 F6C 已验证真实最终 render 开放；项目级 Variant 历史、适配预览、追加式保存及精确 Fact Boundary citation 已接通。
- 第二轮 SPEC 反馈补充：v5 Candidate 当前性按稳定 `(unit_id, variant_key)` 系列判断，不由整个 Unit 最大 Candidate ID 决定；三渠道预先冻结后可任意顺序审批/授权，同系列新版本仅替代本系列，真实 Master/context/profile/rights/check 漂移仍阻断，v3/v4 保持原闸门。已写入 design/tasks 与三份相关 delta，独立 SPEC re-review 已通过。
- 第三轮 SPEC 窄修：v5 `ContentAsset` 仅 `channel_variant_revision_id` 为来源 FK；既有 `draft_id`、`topic_brief_id`、`mother_revision_id`、`content_master_revision_id`、`workflow_run_id` 均须为空。工作流血缘从 Variant→精确 source Master→冻结 manifest 读取，不用 Candidate 运行 FK 参与分派/当前性；Review/Approval/Authorization/Package 遇污染字段须拒绝。独立 SPEC re-review 于 `main@6f5e022` 给出 APPROVE。
- 验收结果：项目级 Variant 检查、五种受控形态的 byte-exact 本地包、v5 多系列审批/授权、v3/v4 独立当前性及 Project Overview/Versions 已落地。隔离浏览器通过 Matrix 选择、Text 三形态、Graphic 真渲染、Video 脚本、审批/授权/ZIP、未知对账、素材撤权、归档只读及异步候选切换竞态；详见 [`docs/FE_F6E_ISOLATED_ACCEPTANCE.md`](openspec/docs/项目文档/FE_F6E_ISOLATED_ACCEPTANCE.md)。全量后端、TypeScript/Vite、FE-P1、OpenSpec strict、Ruff、SQLite/PostgreSQL 隔离迁移及三方独立复核均通过；本地包不等于平台发布。
- 待完成/TODO：F6E 的 canonical 主规格同步与归档须单独授权；真实账号/Provider/远端发布留 F7，生产身份与部署留 F8。旧 V1 七场景及 PRD §15/§16 的真实 Topic/全渠道门槛未因此自动完成。无 push/deploy/生产迁移。
- 关键设计决策：无渠道 Master 是显式 source-only 路径；Matrix 选择不会在 Candidate Approval 前创建 DeliveryTarget；渠道适配在 Candidate v5 冻结前完成，Publisher 不改已批准内容，未知交付仍须对账。ContentAccount 自由格式 profile 不证明目标平台所有权；本地包仍须校验账号活动/归属/单元绑定和冻结目标，但只能标为人工交付，远端动作须后续 F7 精确验证。
- 依赖与启动：沿用当前 FastAPI、React、Alembic；F6E 加法迁移 `f6e000000001` 已在代码中，未执行生产迁移。无 push/deploy/canonical 同步或归档授权。

### FE-F7 Capability Integrations + Delivery（标准 OpenSpec 已进入本地 apply）

- PRD/需求背景：North Star 要求 Model/Tool/Data/Search/Image/Video/TTS/ASR/Renderer/Publisher 成为可替换且可验证的真实能力；注册或配置存在不等于可执行，更不等于特定账号的远端动作已验证。
- 目录结构：[`openspec/changes/fe-f7-capability-integrations-delivery/`](openspec/changes/fe-f7-capability-integrations-delivery/proposal.md) 含 proposal、design、105 项任务，以及新增 Capability 规格和 FE-F2/System Assets/Settings/FE-F4 四份 delta；用户总包源稿保持原样。实施复用 `apps/api/app/services/content_harness/registry.py`、`data_source_plugins.py`、`connector_service.py`、`materials.py` 与 `delivery.py`，不重造其真源。
- 已完成：规格审计、十类 Registry 扩展、两张能力/验证表及加法迁移、内部精确 Publisher 验证判定、旧自动草稿执行旁路关闭、Connector/WeWrite/PublisherResult 错误与结果安全投影；本地全量后端 1207 passed、OpenSpec strict 30/30，均只是 F7 第一批阶段门禁，不是 F7 终验。
- 规格预校准：“保存来源 URL”仅允许经过正向验证的稳定公开引用地址；签名、带凭据或过期抓取/预览地址不能落入 `MaterialRevision.source_url`、元数据、审计或 API。无法证明安全时保留有界来源标识与单向哈希。这仍是尚待实现的 Provider 接受契约。
- 待完成/TODO：F6D/F6E 已完成本地实施验收；F7 正在按两大批 apply。Provider 适配、完整隔离浏览器与真实账号验证仍未完成，缺凭据则保持 unverified。
- 本地 ASR 批：Video-only lazy 面板已接上有界转录建议、拒绝/本地接受/显式 Master 保存和安全血缘；最多十分钟来源、15 分钟 actor receipt，重新核对当前项目可见性、精确哈希和 model-use 权利。单次 Provider 调用最多两个未结束任务、30 秒响应期限，超时保持 unknown、不重试、占用槽位直至任务终止；不声称能取消远端任务。全后端 1291 passed / 2 skipped，隔离浏览器四 gate 与独立窄复核通过，详见 [`docs/FE_F7_ASR_ACCEPTANCE.md`](openspec/docs/项目文档/FE_F7_ASR_ACCEPTANCE.md)。F7 80/105；真实 ASR adapter/凭据尚未验证，无新表或迁移。
- 关键设计决策：复用现有 DeliveryTarget/Attempt/Receipt 和 MaterialRevision；Provider 响应仅是不可信候选，用户显式接受并通过字节、来源、许可和权利检查后才可入库；Publisher 消费已批准冻结成品，不临发布时改内容；unknown 必须对账。关闭旧 `allow_unverified_auto_draft` 对新远端效果的绕过是明示的兼容性行为变化，历史可读。
- 依赖与启动：沿用当前 API/Vite 启动方式。F7 加法迁移 `f7a000000001` 已在代码中并经隔离 SQLite 测试，未执行生产迁移；不 push/deploy，不同步 canonical 或归档。

### FE-F8 单机生产运行可靠性与运维（正式范围82/82完成）

- PRD/需求背景：这台电脑上的个人正式生产易启动、易排查、可恢复；最终SQLite＋本地素材＋loopback，不要求服务器化/多用户登录或对象存储。
- 目录结构：[`openspec/changes/fe-f8-production-readiness-operations/`](openspec/changes/fe-f8-production-readiness-operations/proposal.md)保留proposal/design、100原记录及两份delta；82正式项、18范围外未验证。资料在`docs/FE_F8_*.md`、既有runbooks/恢复脚本；原始包不改。
- 已完成：本地素材hash、脱敏、日志/审计关联、真实readiness、出站隔离/Unknown不重发、SQLite＋素材恢复、三形态五渠道本地闭环、确定性Golden和独立复核；既有1660 passed/28 skipped、Web/预算、strict34/34、Ruff/diff证据保留，不冒称本轮重跑。
- 待完成/TODO：canonical同步/归档需另行授权；18条JWT/Secret Provider/MinIO/新增远端验收是范围外记录，不阻断正式使用，也不自动安排后续实施。
- 关键设计决策：复用User/Role、MaterialRevision、Run/Attempt/Review/Receipt；保留当前技术APP_ENV、身份、凭据、Worker与真实数据；配套恢复hash一致；ZIP/公开发布与契约/模型质量按证据分别判断。
- 依赖与启动：无新增依赖/迁移/配置体系，沿用顶部入口及[运行手册](openspec/docs/项目文档/runbooks/production-readiness.md)；此轮不改运行环境、不推送部署/主规格归档。

### FE-F6C Graphic Production Studio（本地实施 74/74；待主规格同步与归档授权）

- PRD/需求背景：North Star 的图文生产不是图片附件；F6A 仅有 `graphic.master.v1` JSON 壳。标准提案在 [`openspec/changes/fe-f6c-graphic-production-studio/proposal.md`](openspec/changes/fe-f6c-graphic-production-studio/proposal.md)，完整实施计划在 [`docs/superpowers/plans/2026-09-29-fe-f6c-graphic-production-studio.md`](openspec/docs/项目文档/superpowers/plans/2026-09-29-fe-f6c-graphic-production-studio.md)。用户原始总包保持原样。
- 目录结构：标准 change 包含 proposal/design/tasks、Graphic 新规格以及 Production Core、Review、前端性能三份 delta；后端 `apps/api/app/services/graphic_documents.py`、`graphic_master_checks.py`、`graphic_master_diff.py` 复用现有 Master/Ref/Check/Candidate 链，前端 `apps/web/src/product/GraphicStudioModel.ts` 与 `GraphicStudioShell.tsx` 按 Graphic 路径加载，`apps/web/scripts/check-bundle.mjs` 核查静态依赖边界。
- 已完成：按 `main@670dd49` 校准 F6C 的 77 项可验证任务和 Scenario。`graphic.master.v2` canonical 文档/adapter、精确图层素材与证据 locator、按画布顺序的真实手工 render、v1→v2 显式 fork 均已实现；旧无 schema Graphic 保留 v1。exact image profile 规则和四类专业检查已接入；语义/视觉不足仅 warning。Graphic-only UI 已有画布增删复制重排、可缩放/选择的阶段预览、图层几何/样式/裁剪/形状/锁定、exact 共享素材插入/替换、文字证据绑定、每画布最终图片绑定、published Profile preset、显式保存与历史升级/差异。前 12 个可见媒体层经鉴权和 SHA256 校验才预览。隔离 SQLite 与真实浏览器已完成两画布保存/刷新、Brief/事实边界变化使旧 Master stale、精确证据绑定、手工渲染确认、八项检查、Candidate v4、冻结双图预览、警告处置、审批与本地包授权；ZIP 双图顺序/哈希与冻结清单一致，未回填发布。归档单元的 Graphic 输入/保存/检查/冻结均只读；第二单元的并发写入后，旧页面保存显示 409 且本地编辑未冒充落库。重复素材兼任图层/最终渲染时的 ZIP 重名已按失败回归修复；新旧 Candidate 回读与结构化差异保留各自冻结文字和检查哈希，Review 检查名称不再丢失。全后端在排除本机无效 `NO_PROXY/no_proxy` 后为 951 passed/2 skipped；相关定向 97 passed，前端模型 20/20、TypeScript/Vite/FE-P1、OpenSpec strict 26/26、相关 Ruff 与 diff-check PASS。
- 待完成/TODO：独立复核已在 ChatGPT 实际读取 `main@2891bac` 后给出 SPEC 与前端 APPROVE；后端前轮 APPROVE 继续有效（未改后端业务代码），任务 74/74。本轮全后端新跑 951 passed/2 skipped，前端构建/FE-P1、OpenSpec strict 30/30、F6C 相关 Ruff 通过；额外全库 Ruff 有 23 个既有问题，不属于本切片完成声明。原 F6C 真实 Provider 接收/许可/血缘要求明确移交 F7，执行/结果响应脱敏及负向测试已进入 F7 active 规格但业务能力尚未实现。项目接口和 Graphic 工作台仍诚实显示未验证自动渲染不可执行；人工图片确认不代表已验证 Renderer 或视觉语义。不能把 F6C 通过等同整个 North Star 完成。主规格同步/归档另需授权，不 push/deploy/生产迁移。
- 关键设计决策：旧 Graphic v1 显式 Fork；画布顺序与输出一一对应；未验证 Renderer/Search/Image 不冒充可用；GraphicStudioModel 仅在 Graphic 工作区动态加载，通用 Production/Text/Video 静态闭包由构建门禁隔离；小红书旧 `image_note` 当前是 text-classified，F6C 不暗中改类，跨渠道适配由 F6E 承接。
- 依赖与启动：沿用现有 FastAPI/React、MaterialRevision 与生产工作台；目标零新表/零迁移。使用本 README 既有 API/Vite 启动方式，先在隔离数据库做验收。

### FE-F6A Production Core（本地验收完成，五份主规格同步并归档）

- 需求背景：在现有 Workflow/Run、Candidate v3、Review 与 Delivery 链路上增加不可变 `ContentMasterRevision`，让文字、图文、视频共用明确的主版本和上下文血缘；不替换旧引擎，不新增远程发布能力。
- 目录结构：后端 `services/content_masters.py`、`production_modalities.py`、`candidates_v4.py`、`production_validation.py`、`production_packages.py` 承接保存、适配、冻结、live gate 与本地包；既有 Review/Outputs/Overview/Versions 接入 Master。前端 `ProductionWorkspace` 拆分 Header/Canvas/Inspector/AssetDrawer/MasterPanel 和三个 lazy StudioShell；迁移为 `f6a000000001`。
- 已完成：214/214。手工 Text（无 Draft/Topic/Mother/Run）→ checks → Candidate v4 → exact-hash Approval → Delivery Authorization → ZIP；Graphic/Video 经真实文件及精确输入的人工 render attestation 走同一闭环。上下文/CAS/幂等、live rights/evidence/checks、跨 Unit 项目素材、输出血缘、三形态 Review、Master Versions/Overview、历史只读和 Workflow debugger 均已验收。
- 验收：后端 753 passed（206 项 F6A，6 项既有 warnings）；TypeScript/Vite、FE-P1、strict24/24、Ruff/diff 通过。隔离 SQLite 与真实 PostgreSQL16 up/down/up 通过；浏览器 20.1–20.14 和三项独立 review 全部通过。/projects 224.68 kB raw / 72.86 gzip，Production 254.44 / 82.27；无 TipTap/XYFlow 首包泄漏。完整证据与边界见 [FE_F6A_FINAL_ACCEPTANCE.md](openspec/docs/项目文档/FE_F6A_FINAL_ACCEPTANCE.md)。
- 关键设计决策：Workflow/Master dirty 与保存独立；冻结历史不自动跟随身份/Brief/Boundary；新审批/授权要求 current Master，已有授权只交付原冻结历史且仍受撤权/字节/检查 gate；v4 失败不回退。图文、视频不计算假文本相似度；最小壳不冒充专业编辑器。
- 规格收尾：2026-09-29获单独授权后，新增 [Production Core主规格](openspec/specs/production-content-master/spec.md)，更新FE-F2/F3A/F3B/F4四份主规格；实施记录归档至 [F6A归档](openspec/changes/archive/2026-09-29-fe-f6a-production-core-content-master/proposal.md)。29个delta要求块准确同步，40条旧要求/149个旧场景保留，原始包及9份归档文件未改。
- 待完成/TODO：F6A已完成规格生命周期收尾；F6B及以后不执行，须先有具体方案并确认。仅本地提交，未push/deploy/生产迁移；不把本地验收当作生产就绪。
- 依赖与启动：复用现有 FastAPI/SQLAlchemy/Alembic/React，无新增运行依赖；启动沿用下方命令。迁移与验收只在新临时数据库执行，禁止用于未授权开发/生产库。AI Workflow 浏览器验收使用显式 mock provider，不代表真实外部服务验收。
- 开发方式：按用户授权直接在本地 main 实施和提交；不因单 Agent 跳过规格、回归与独立只读评审。

### 当前产品链路（2026-10-25 起只保留新版本）

```text
内容机会 / 数据接入 → 项目（选题、任务书、来源与事实边界）
  → 作品（文字 / 图文 / 视频）
      文字、图文：内容方案页「写作方式」开关 —— 平台模型（内置创作流程）或第三方模型（经 MCP 写稿）
                  每次生成留一个版本，采用即定稿，要调整就复制一份
      视频：第三方模型经 MCP 主导，七步一页（选题与资料 → 导演稿 → 素材 → 配音与音乐 → 小样 → 成片 → 交付），成片通过即定稿
  → 主稿版本（Content Master）→ 审阅中心（候选 v4 / 渠道变体 v5、审批、交付授权、回执）
```

- 素材：项目素材放移动硬盘的项目文件夹，通用素材放 Mac 本地通用素材库；复用别的项目的素材用快捷方式；小样 / 成片不算素材。
- 旧版本（选题、稿件、母稿交接、旧审核、旧内容资产、独立工作流页等）只做过测试、从未发布，已整体删除；新版本仍在用的旧后端（数据接入、模板、来源与证据包、交付、创作流程引擎）保留，页面已搬进新结构。见 `openspec/changes/archive/2026-10-24-remove-legacy-version/`。

## 快速启动（历史开发/首次初始化参考）

当前单机生产日常维护使用顶部入口与[运行手册](openspec/docs/项目文档/runbooks/production-readiness.md)，不对真实库重复seed、迁移或重新配置。下方首次安装/开发命令仅适用于独立环境，不是正式启动前置。

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

> 历史开发代理参考：fake-ip可能影响URL/Connector地址校验。当前单机生产不为名称改变SSRF_ALLOW_PRIVATE或现有代理配置；保留各能力的精确目标/SSRF边界，任何放宽须另行诊断授权。字面技术production分支的限制不构成改写当前配置的理由。

### 服务器扩展参考（非当前适用，不执行或作为待升级计划）

下方compose/PostgreSQL/MinIO/代理仅适用于另行选择并授权的服务器扩展，非当前本机正式使用前置，不因此复制其配置。

服务器扩展部署（docker compose 全栈）：`docker compose up -d --build` 一键起 postgres / redis / minio /
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

### 设置

分区：模型与 AI（厂商与模型、用途路由、生成能力与插件、兜底模型与生图）/ 数据源（含数据接入 Connector）/ 渠道 / 规则与模板（含模板中心）/ 团队与权限 / MCP 接入 / 存储位置 / 自动剪辑 / 配音 / 能力方法库。Secret 一律脱敏回显，保存即时生效。

### 外部 API 数据接入（Connector）

「设置 → 数据源 → 数据接入」配置量化平台等外部 API：base_url + 鉴权（密钥只存环境变量名，值不落库），
Endpoint 定义拉取路径与 JSON→Fact 映射（statement 模板 + fields 字段引用），
「立即拉取」后数据进入来源库走正常确认流程：

```bash
curl -X POST http://localhost:8000/api/v1/endpoints/1/pull -H "X-Studio-User: editor@studio.local"
# 定时拉取（生产交 Celery ingestion 队列或外部 cron）
```

### 运维

- 当前正式运维以[单机生产手册](openspec/docs/项目文档/runbooks/production-readiness.md)为准，多副本/容器仅为非当前适用的扩展参考。
- 监控：显式`GET /api/v1/health/ready`检查DB/schema/素材/必要队列与Worker，不自动探测模型；存活用`/api/v1/health/live`，旧health兼容；metrics使用有界安全标签，
  每个响应带 `x-trace-id` 并输出 JSON 结构化访问日志
- 多副本指标聚合：Prometheus 按 replica 逐个抓 `/metrics`（service discovery 自动发现实例），
  指标自带 `instance` label 天然区分副本；**不需要** Pushgateway——它适用于批任务，长驻服务抓取即可
- 异步队列：`.env` 设 `TASK_QUEUE_ENABLED=true` + Redis（`CELERY_BROKER_URL`），
  Connector 拉取走 `ingestion` 队列；`make worker` 启动 Celery worker（compose 部署含 worker 服务）
- 数据库迁移：仅独立开发/首次初始化可make seed；当前生产日常启动不执行seed/迁移，另行获准schema扩展才用make migrate
  （`alembic upgrade head`，已在 PG 16 实测），后续 schema 变更用 `alembic revision --autogenerate`
- 备份恢复：当前SQLite＋素材同快照；make backup仅数据库、保留7份，不构成完整备份。配套流程及范围外PostgreSQL参考见
  `docs/runbooks/backup-restore.md`
- **常驻服务（launchd）**：API 与 Celery worker/beat 由 launchd 管理（崩溃自动拉起、开机自启）：
  `launchctl list`查看两个aicontent标签，必要重启用`launchctl kickstart -k gui/$(id -u)/com.aicontent.api`；完整停止API/Worker见运行手册，不用make stop替代；
  日志在 `logs/api.log` / `logs/worker.log`；运行时密钥集中在 `apps/api/scripts/startup/runtime.env`
  （600 权限、已 gitignore，DreamO token 过期只需改这一个文件后 kickstart worker）
- **数据保留**：beat 每日 03:30 自动清理——llm_run 超期清空大字段（行保留 30 天）、audit_log /
  export_record 留 90 天、终态 workflow 运行留 30 天，库体积有界
- **拉取节奏**：Connector 端点内容指纹去重（无变化不新建 Source）；beat 扫描 300s；端点周期在
  数据接入页可调（仅手动 ~ 每天）

### Golden 夹具

`apps/api/evals/goldens/`：Identity / Content 质量基线，Content 夹具从 `apps/api/evals/golden_cases.json`（30 个受控事实场景）取用例。

### 接真实模型

`.env` 设置：

```text
LLM_PROVIDER=openai_compatible   # 兼容 minimax / openai / 任意 OpenAI 风格网关
LLM_BASE_URL=...
LLM_API_KEY=...                  # 只放环境变量，DB 不存明文
LLM_MODEL=...
```

业务层只面向 `LLMProvider` 协议；`MOCK_INJECT_UNFACT_NUMBER=true` 可让 mock 注入一个
FactPack 外数字，用于验证事实检查能拦住无来源数字。

## 目录结构

```text
apps/api/
├── app/
│   ├── models.py            # 数据模型（项目 / 作品 / 主稿 / 素材 / 来源事实 / 候选交付 / 工作流运行 …）
│   ├── routers/             # HTTP API（content_projects / content_masters / materials / sources / fact_packs /
│   │                        #  connectors / templates / delivery / project_review / settings / edit_agent / creative_mcp …）
│   ├── services/            # 业务服务（video_chain / article_chain / project_folders / storage_locations /
│   │                        #  workflow_engine / creation_recipes / candidates_v4·v5 / delivery / creative_mcp …）
│   │   ├── content_harness/ # 渠道注册与渠道方法插件、渲染器、发布器、节点插件
│   │   └── generation/      # LLMProvider 协议与各家 provider
│   ├── tasks/               # Celery 任务（数据接入拉取、工作流推进、保留期清理）
│   └── llm/                 # Prompt 与领域知识
├── alembic/versions/        # 迁移（最新 legacy0001：删除旧版本表）
├── evals/                   # golden_cases.json + goldens/
├── scripts/                 # MCP stdio 桥、剪辑派发、启动与运维脚本
└── tests/
apps/web/src/
├── App.tsx / api.ts
├── components/ui.tsx        # 基础组件
└── product/                 # 全部页面与组件（工作台、项目、作品七步、审阅中心、素材库、设置 …）
    └── project/             # 项目页各标签
openspec/                    # 规范：specs/ 主规格，changes/ 进行中，changes/archive/ 已归档
docs/runbooks/               # 单机生产、备份恢复
```

## 关键决策

1. **第一设计原理：平台定结果，不定步骤**——AI 负责想和做，人负责判断和拍板，平台负责记账和展示；只锁结果（事实有来源、素材有权利记录、没人点头不发布、每步可追溯）。
2. **视频由第三方模型经 MCP 主导**：平台不调用自己的模型，只记录并在导演稿、小样、成片三处停下等用户；成片通过即定稿，调整走复制一份。
3. **文字 / 图文两种写作方式**：页面开关选平台模型或第三方模型；每次生成都是一个版本，可删除（当前、定稿、被引用的除外）。
4. **一页一件事**：流程按步骤分页、上一步 / 下一步推进，准备做成桌面端；高级工具不进流程。
5. **只留一个版本**：新版本在用的旧后端保留并搬进新结构，只属于旧版本的页面、后端、数据表全部删除。
6. **素材存放**：专有素材跟项目放移动硬盘，通用素材放 Mac 本地；平台只读检测硬盘、每个文件只完整校验一次、剪辑素材只复制一次，减少对硬盘的访问。
7. **建表走 Alembic**：迁移在全新库与已有库都必须能跑通；删除类迁移在表非空时中止。
8. **Connector 鉴权凭据只存环境变量名**：值运行时从进程环境读取，不落库不入日志。
9. **模板只增不改、单版本生效**：变更 = Clone 新版本再发布；同渠道至多一个 published。
10. **DreamO 复盘看板走标准数据服务**：Connector 映射 v2（stages）把 4 张看板转成高信号事实，指纹去重；方法论与指标字典在 `app/llm/knowledge/`，用于事实检查的误读红线。

## Persona Creative Studio 当前验收状态（2026-10-08）

- 2026-10-09最新：`add-persona-creative-studio`150/156。科技完整Audio Recipe在隔离副本完成实际5分24秒音频、受限素材接受和QC通过；生活新CPA请求Unknown后停批，人工试听/全模态与独立质量/生命周期仍分别开放。实际串接修正不改正式数据/配置/服务；继续沿用本机启动方式与依赖，[当前回执](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。本节下面为早期验收状态。
- 两个 Starter Persona 的真实 Text 样本已分别通过用户人工确认。
- 本次已在隔离 SQLite + 本地素材副本中完成 MiniMax `image-01` 与 `speech-2.8-hd` 的两角色真实 provider/material 回接；证据见 [PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md](openspec/docs/项目文档/PERSONA_GRAPHIC_AUDIO_REAL_ACCEPTANCE_2026-10-08.md)。
- 真实图片/音频结果尚待用户做创意质量确认；完整 Graphic deterministic compose/render/QC 与 Audio QC/ASR Stage 仍是后续验收项，不以 provider 连通代替。
- 当前不写正式 SQLite/正式素材库，不做正式 Persona 初始化、发布、push 或归档提交。

## TODO（按优先级）

1. dsh 沙箱限制：skill 无法写 `~/.wewrite/runs/`，产出暂落 `.wewrite-scratch/`（待沙箱放行或路径迁移）
2. DeepSeek API key 尚未配置（`~/.dsh/env.local` 留空，MiniMax 已可用）
最新Commons续验（2026-10-01）：真实产品搜索200/7候选，下载stage 502、未导入；后续搜索502，API域名DNS再次为198.18.0.15。前次网络恢复不是持续验收，10.2不关闭，F7仍97/105、F8未apply。临时库/素材已回收，无业务代码/依赖/启动变化，微信未知上传不重试。详见progress.md。
2026-10-18 **商品实拍任务书与阶段方法留痕方案待确认**：同一change补充第10节，产品承接脚本确认、逐镜拍摄任务/原片审阅/补拍和版本记录，Skills承接阶段判断；旁白可后置，旧AI路线保留。新增8项待批准，既有范围50/58，含提案50/66；仅文档与strict验证，无业务实现或正式数据变化。[方案入口](openspec/changes/improve-product-keyframe-preproduction/README.md)。


2026-10-19双角色媒体实跑：科技/生活各4张图文与生活音频已本地交付；科技TTS未知回执尚未取得音频，不能宣称四条全通过。详见openspec/changes/archive/2026-10-19-redesign-studio-task-navigation/README.md追加验收。未公开发布，优化工作台和模型配置保留。

科技音频当前阻断已于2026-10-19同参数复现为MiniMax Token Plan额度用尽；模型与原音色未改，待额度恢复后完成剩余验收。详见上述验收目录最新记录。

科技音频最新状态（2026-10-19）：额度恢复后原音色/模型在run24完整生成、ASR、QC和本地交付通过，包为output/20261019_AI科技实作/tech-audio-project35.zip；旧额度阻断记录保留为历史。保留未直接试听及ASR字幕待校对边界，未公开发布。
