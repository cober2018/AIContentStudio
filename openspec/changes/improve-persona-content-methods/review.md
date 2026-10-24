# 研究与提案复核

## 2026-10-20 接手Agent续做（交回主Agent独立总验收）

| 编号 | 真实问题与证据 | 处理 / 边界 |
| --- | --- | --- |
| A17加载 | 最终版源码hash与交接一致；无running/claimed（仅既有Unknown129/155）后按原launchd命令加载，ready=true，见 `independent/a17-final-api-reload.json` | run25/refine空override预览就绪：longform@2、humanize@2各在执行prompt出现1次，定位反馈到达，路由rev13/gemini-3.8-flash-high不变，见 `real-samples/tech-text-B-refine-quality1-inherit-preview.json` |
| A18 | 科技图文visual返修后cards步骤被正确标stale，但rework_context仍把针对旧attempt151的定位反馈（事件330）从attempt154快照带入重查预览，违反spec“失效目标的反馈不得静默套到新修订” | `stage_feedback.rework_context` 在步骤为stale时不再带入旧定位反馈，原反馈留在旧尝试历史；修后重查预览located_feedback=None。相关既有检查624通过（`independent/a18-api-checks.txt`），按原命令重载（`a18-api-reload.json`）。Ruff剩2条均为此前相邻改动行（import排序、235行未用变量），未扩大修改 |
| Unknown155 | GET仍unknown/possibly_dispatched；只读库见同时刻LLMRun186 failed/stage_provider_failed、无正文 | 同一step任何新调用由guard返回409 `stage_unknown_reconciliation_required`，reconcile只封running，无正常解除路径。未重发、未换key/模型；run27精修后链停止，需用户决定。见 `real-samples/life-text-B-refine-unknown155-readback-20261020.json` |

### 真实产物评审（技术 / 内容 / 角色认可分列）

| 作品 | 技术 | 内容质量（实际阅读/逐张看图） | 角色认可 |
| --- | --- | --- | --- |
| 科技文字B Master78 rev3 | refine157→title158→final159→final_quality160八项pass；本地包content.md hash=final渲染hash `693cb570…`，target8待人工回填，未发布 | 157明显回应定位反馈：同一假设问句贯穿输入/预期/判定/缺失/冲突，转人工与置信度表述正确。仍编造冲突例具体地点、预期要点“携带身份证件”及“输入载荷/合规交付/合理降级”术语；一次返修额度已用，人工3块词句定点编辑（`tech-text-B-refine-edits.json`），不归因Skill。结论：较原Master61在“具体例子贯穿”上改进，需人工小改 | 待用户 |
| 科技图文B Master80 rev2（3张） | visual返修161（本次instruction覆盖，已记变项）→cards重查162→card-2定位返修163→compose164→Master79（人工6层文字编辑）→3张PNG实渲染并绑定→quality166 七pass+1覆盖warning；本地包3张PNG hash与实看一致 | 根因：已采用visual137把“转人工”列为第4种情形、三要素写成箭头流程；161修正。163修好card-2但整阶段重做又把“置信要求”写回card-1，自动质量记**未通过**，人工定点修正。逐张看图：手机可读、无裁切、card-1三框并列无箭头；需改：三张下半约一半空白、封面“评估设计/模型参数”未表达对比、转人工分支仅文字未图示、card-2第2/3条间距不均（人工缩短文字沿用原层高） | 待用户 |
| 生活图文B Master82 rev2（4张） | P38按原P36同一方式接入同一Material71（AI情境示意，A/B同允许素材）；visual167把71称“真实摄影素材”→修A19后visual168正确定性；cards169→定位返修170→compose171→Master81（人工3层编辑）→4张PNG实渲染绑定→quality173七pass+1覆盖warning；本地包4张PNG+封面素材hash一致 | 叙事工具→心理门槛→设想场景逐页推进，来源边界压到一句，改善原“页2主要是免责”。169把写给作者的制作约束印成读者要点，定位返修已去除；170又新增无依据产品细节（立柱/倾角调节）与笔误，自动质量记**未通过**，人工定点修正。逐张看图需改：封面插图偏小且画的是窗边笔记本而副标题说画架、无AI示意标注；正文卡下半约45%空白；card-3“合上即可收起”暗示可折叠无依据 | 待用户 |

### 同条件 A 基线（原 @1 方法，未编辑，按原样采用）

| 作品 | 技术 | 内容质量（实读/逐张看） |
| --- | --- | --- |
| 科技文字A Master85（run29） | 9阶段全链；quality仅“必然”warning（工程代价陈述）；final_quality八项pass；本地包content.md=渲染hash `510a7ae6…` | 术语密集、编号小标题、无贯穿具体例子；转人工列为第四类、以“置信度得分过低”为转人工条件——原登记缺陷全部重现 |
| 科技图文A Master87（run30，4张） | visual首次183因A/B污染作废（见下）；隔离后184→cards185→compose→Master86→4张PNG→绑定87→quality188；本地包hash一致 | card-1四框连线成流程且第4步“转人工分支判定”；card-3“置信度不足时触发降级”；封面几乎全空；card-2是与文章无关的通用流水线 |
| 生活文字A Master90（run31） | 全链；quality/final_quality八项pass；本地包=渲染hash `30d11b3a…` | 自然、有设想场景；但仍有一整段“非独立测评/未验证”说明（原缺陷重现），编造“木质装置”“页面明确展示的折叠”，final开头与第二段重复同一场景，约1560+字超原Brief900–1200。自动事实检查未拦这些编造 |
| 生活图文A Master96（run32，4张） | visual198→cards→compose→Master91→4张PNG→绑定96→quality202；本地包hash一致 | 结构与B相近；要点多为空泛标签；card-1仍有“转述自…”来源提示要点；封面标题与窗边笔记本插图不对应；无编造 |

**A/B 比较（各角色独立，不互相排名；随机单次样本，不作因果/统计结论）**

| 角色/形式 | 预登记问题是否解决 | 变项与归因限制 |
| --- | --- | --- |
| 科技文字 | B解决“一个假设例子贯穿输入/预期/判定/异常”和“转人工/置信度”表述；A均未解决 | B的改善主要发生在定位返修157，且B初稿与精修后各有一次人工编辑；不能全部归因@2方法。script阶段启用为已登记方法变项 |
| 科技图文 | B三要素并列、三种情形+转人工为动作；A重现流程化与置信度问题 | B经上游视觉方案本次instruction覆盖、定位返修与6层人工编辑，属组合变化对照；两者都有下半大面积空白 |
| 生活文字 | B（Master76，初稿+一次人工编辑，因Unknown155未经精修/终稿）与A终稿不同阶段，不能严格对照 | 需用户决定是否为B新开run完成精修链 |
| 生活图文 | B要点更具体、叙事推进更清楚；A更空泛但编造更少 | B有定位返修与3层人工编辑；两者封面图文不对应（同一允许素材限制） |

### 音频 A/B（同源正文：科技Master61、生活Master65；原模型/音色/rate全部回读一致）

| 作品 | 技术（实际回执） | 内容 / 声学（机器检查，未人工试听） |
| --- | --- | --- |
| 科技音频B U55/run33（spoken-adapt@2、voice-director@2） | spoken首次203因`stage_secret_or_control_forbidden`失败（原音频当时同一失败）；按原音频实际生效的本次指令覆盖repair1成功→voice→TTS speech-2.8-hd/lengdan_xiongzhang/rate1.0，194.0s→本机ASR 82段→QC warning；本地包 `real-samples/audio/tech-audio-B/` | 去标点相似度0.977，14处同音转写误差，无漏读；RMS -23.1dBFS（LUFS未测），无削波，首尾静音<0.2s。口语稿三类情形+转人工为动作、置信度表述正确，“首先/其次/最后”把并列说成顺序 |
| 科技音频A U56/run34（@1） | 同一覆盖（原音频实际条件）→TTS同参数190.6s→ASR→QC warning；本地包同目录A | 相似度0.980，13处同音误差；内容与B接近，同样说明置信度不等于正确率。A/B口语差异小，不宣称改进 |
| 生活音频B U57/run35（@2） | 无覆盖（与原生活音频一致）→TTS speech-2.8-hd/chunzhen_xuedi/rate1.0，161.3s→ASR→QC warning | ASR输出繁体，ICU繁简归一后0.975；英文名Lap Easel/Colossal识别异常，**发音需人工试听**。免责集中为一段+一句，篇幅约843字 |
| 生活音频A U58/run36（@1） | 同上，217.3s；声音方案建议rate0.98但实际仍按原配置1.0 | 归一后0.983，一处“如果”转写缺失；反复免责三处，约1141字。B在预登记的“反复免责”上有改善 |

系统QC的“位置字符差异率”受标点/繁体影响很大（0.02–0.82），不能单独作结论；本次相似度为主Agent去标点+ICU繁简归一后的序列比对。四段均**未人工试听**，感知质量待用户。

### 新主题迁移（未参与风格提炼；仅B）

来源：平台 `/sources/url` 服务端读取原文（source 138 README、139 Colossal），主Agent实读后写来源核验文本（140/141/142），抽取→改写为归属转述→确认→事实包：科技FP7（3条）→v2 pack9（补2条README闭环细节），生活FP8（2条）。新项目P39（科技）/P40（生活）只引用机会19/7，不改原机会状态。

| 作品 | 技术 | 内容质量 |
| --- | --- | --- |
| 科技新题文字B U59 → Master102（本地包content.md=渲染hash `0df1fac3…`） | run37：evidence→angles→outline→draft（定位返修228）→quality（Master98补引用后通过）→refine（退步，定位返修232）→title→final→终检因引用丢失拦下；补引用后语义检查又拦下三处README细节（不在FP7）。补FP v2并更新事实边界后，run37所有已采用阶段按设计失效（accepted_context_changed），未重跑整链，改用正常的Master级检查（Master102：七pass+UTC日期warning）后本地交付 | 初稿把“开发板直接读像素”写错核心链路，返修后正确（板上不解码→BLE→App解码，动作经BLE回传→USB HID），并讲清指针回位校准、等画面稳定、断链续跑；限制讲成取舍，来源归属清楚，无实测/成功率断言。精修曾删掉已核对的链路，返修恢复。小问题：“画面流转”与“眼睛”重复。迁移结论：结构方法（眼睛/手/大脑、限制即取舍）可迁移；但两处关键事实错误/退步靠定位反馈修正 |

新发现：① AI 文字阶段合同不让模型返回引用、服务端也不自动映射，含日期等数字的稿件每次都会被角色质检“数字无引用”拦下，需人工补引用（Master98/101/102）；② 我在定位反馈中引入README细节时没先入事实包，属主Agent流程疏漏，已按正常流程补FP v2；③ 事实边界变更会使整条run的采用失效，这是正确保护，但意味着“补一条事实”需重跑全链或改用Master级检查；④ 服务端日期检查按UTC当日比较（台北凌晨仍是前一天），as_of=当天会被判“非当日”。

| 编号 | 真实问题与证据 | 处理 / 边界 |
| --- | --- | --- |
| A20 | 科技新题evidence阶段（creative.method、显式@2）在事实包5条时冻结快照133831B>131072B而报stage_value_too_large；A17压缩只覆盖master.propose | A17严格去重扩到角色域`stage.creative.method`（同样仅builtin@2、正文严格相同、只在原本超限时触发）；继承到capability_memory时仍拒绝。只读探针修前FAIL/修后OK；833项相关既有检查通过，重载见 `independent/a20-reload.json` |

### 新主题其余形态

| 作品 | 技术 | 内容 |
| --- | --- | --- |
| 科技新题图文B U60 → Master104（4张） | visual237→自动cards238被capability-memory遮蔽且合同失败→显式@2 cards239合同失败（claims引用未列入references）→登记合同修正覆盖repair1 240→合成被几何检查拦（card-0标题溢出）→card-0定位返修241→合成→PNG渲染绑定；run阶段质检预览超128KiB（见下“仍开放”），改用Master级检查七pass+覆盖warning后本地交付 | 每条都带README引用，card-1数据流顺序图语义正确、card-2改为并列分组；需改：英文节点“AssistiveTouc/h”截断、首条要点后间距偏大、漏“首次刷写需Mac” |
| 科技新题音频B U61 | 源Master102；首版口语稿受我复用的原题覆盖（含“三类评估建议”）污染，改为只留通用合同后repair1；TTS 209.1s原配置；ASR相似0.956 | 一处转写多出“第二是”，需试听确认是否重复朗读 |
| 生活新题文字B U62 → Master108 | 生活evidence为current模式；我录入as_of=台北日期10-20被UTC判为未来而不合格，更正为10-19并以pack10重绑边界后正常；全链八项pass，本地包hash一致 | 自然、具体、以拍照惯性→装置→日常凝视推进；“没去现场”一句、设想明示；初稿两处超出报道（传感器/存储介质、漫长展期）人工删改；1386字仍超900–1200目标约15% |
| 生活新题图文B U63 | visual258要求一张合规授权的封面摄影（不得冒充现场/不得用新闻原图），P40无可用素材；**未采用、停在视觉方案**，不静默改纯文字封面 | 需用户提供素材（见素材清单） |
| 生活新题音频B U64 | 源Master108；TTS 162.3s原配置；ASR归一后0.964 | 英文名（Colossal/Pneuhaus/MODE）识别偏差，发音需试听；“首字母p不发音”是模型推测 |

### 视频：A/B 导演计划与新题计划（均未派发执行、无MP4）

| 计划 | 结果 | 内容 / 素材缺口 |
| --- | --- | --- |
| 科技B U65（script@2→显式shot-director@2→master→prepare，包3） | 4镜55s，shot-plan.v2带连续性/声音/内容依据/未检查项；导演包确含accepted_shot_plans(attempt266) | 全为动态图解、无素材需求；shot-3仍高亮“置信度阈值” |
| 科技A U66（当前继承方法，包4） | 4镜47s，v1无连续性/声音字段 | 自造8个不存在的素材文件名（.aep/.svg/.mp4）作为需求；同样含“置信度” |
| 生活B U67（自动续接正确用@2，包5） | 4镜24s，v2 | 需授权的书桌/速写本/公园长椅/晨光静物实拍或空镜，计划已标明缺口 |
| 生活A U68（包6） | 3镜37s，v1 | 无素材需求字段，缺连续性/声音安排 |
| 科技新题B U69（包8） | 5镜99s，v2；prepare首次因快照超限失败，A21修复后生成 | 全为动态图解；“未实测”类缺口写明 |
| 生活新题B U70（包7） | 4镜38.5s，v2 | 图解为主，末镜需窗外光影空镜授权素材 |

B 在计划层面普遍更完整（连续性、声音、内容依据、显式缺口），A 有编造素材名；但两角色B真实成片均**未做**：科技需动态图形制作（AE/Resolve Fusion）并为视频脚本单独配音，生活需授权实拍/空镜。按设计保持5.4待完成，不用幻灯片占位冒充。

### 本轮新增修复与开放问题

| 编号 | 问题与证据 | 处理 / 边界 |
| --- | --- | --- |
| A21 | 科技新题导演包准备（professional.prepare，无方法栈）快照超128KiB（context 38.7K+sections 37K+prompt 36K） | 角色域、无方法栈的prepare只把与完整prompt逐字相同的分段改为位置引用；商品不变。只读探针FAIL→OK，846项检查通过，重载见 `independent/a21-reload.json` |
| 开放-1 | 科技新题图文run质检阶段（stage.checks）预览同样超128KiB（4卡、12条逐字引用、5条长事实）；规则阶段无可压缩的重复 | 未修；改用正常Master级检查交付。需主Agent判断是否作为缺陷继续处理 |
| 开放-2 | 科技角色（persona2）的capability-memory方法（artifact6）在自动续接/空覆盖时遮蔽节点@2（cards、shots），生活角色不出现 | 本轮B均显式@2执行并记录；是否属配置预期或缺陷需用户/主Agent决定 |
| 开放-3 | 每用户8个、15分钟的媒体暂存名额：已接收的暂存仍占名额，连续渲染4张+采用音频会429 | 等待过期规避；未改 |
| 开放-4 | 服务端日期类检查按UTC当日：台北凌晨as_of当天被判“非当日/未来” | 本轮按UTC日期录入更正；未改检查 |

### 需用户提供或决定（素材清单）

1. 生活新题图文封面：一张你拥有或可授权使用的照片（柔和自然光、窗边光影或静物，非装置现场），或明确同意用平台AI生成一张“情境示意”插画并标注为示意。
2. 生活视频B真实小样：书桌/合上的速写本/铅笔、公园长椅或窗边软椅、晨光下翻开的随笔本等授权实拍或空镜（约4段，每段6秒左右）；或确认可用AI示意图替代并标注。
3. 科技视频B真实小样：确认是否允许用Resolve（必要时AE）把计划中的动态图解做成成片，并为视频脚本单独做一段原音色TTS；如有AE模板/图标素材可提供。
4. 生活新题视频（若后续要成片）：窗外光影/白墙树影空镜授权素材。
5. 生活文字B：Unknown155（run27精修）无正常解除路径——请决定“为U51新开run重走精修链”或“接受Master76v1作为本轮B并本地交付”。
6. 试听：10段音频（A/B×2、新题×2）均未人工试听，尤其生活英文名发音、科技新题疑似重复一句。
7. 角色默认：看过A/B与新题实物后，逐角色/形式决定是否采纳@2为默认（6.2）。

A/B隔离：B渲染PNG被系统自动挂为项目共享素材，A的visual183读到并要求沿用“tech-graphic-B-m79”版式。已用正常DELETE解除B（及之后A）渲染图的项目共享引用，B的Master绑定/本地包不受影响，visual183作废；见 `real-samples/ab-isolation-detach-render-refs.json`。同项目内做A/B时必须先隔离渲染产物。

| 编号 | 真实问题与证据 | 处理 / 边界 |
| --- | --- | --- |
| A19 | 共享素材进入提示只带kind/mime/hash，模型把AI情境插画71写成“已授权真实摄影素材…展示画架实态”（visual167） | 仅角色域在共享素材条目附source_kind/title，并在角色域规则写明ai_generated是示意不是实拍/使用证据；商品上下文不变。相关624、图文156、商品53项既有检查通过，重载见 `independent/a19-checks-and-reload.json`；修后visual168正确定性 |

## 2026-10-20 真实样本与续验

- A14 独立复验通过：StageHistoryPanel 的按钮和发送入口均遵守 allowed_decisions；原生TTS/专业执行不允许 rerun 时无POST，commented仍可保留本作品意见。15项定向检查与原6项回归通过，见 `evidence/independent/stage-history-final-recheck.jsonl`。
- 隔离正常页面的只读、归档、Unknown回读、375px和零写入通过；明确保存默认产生新修订且保留模型/音色/其它字段；31条参考可翻页、精确读原文、保存带原因反例候选。见 `browser-boundaries.json`、`browser-default.json`、`browser-reference.json`。这些均不代表正式角色风格已获用户采纳。
- 原15表在新样本前已只读备份。复读14张内容/历史表的原有行全部一致；system_settings仅既有后台的discovery.heartbeat和discovery.catchup_clock变化，其余11项一致。见 `original-db-rows-preservation.json`。不再用旧序列化不明的hash推断保全或损坏。
- 实际阅读科技draft143与生活draft147全文，确认模型初稿存在未核验效果、自动评测和置信度表述退步。已阅读两份逐块编辑差异，编辑修正不计为Skills原生提升，后续精修与对照仍待。

| 编号 | 真实失败与证据 | 修复范围 / 验收边界 |
| --- | --- | --- |
| A15 | quality148把“不应追求绝对零风险的理论架构”误判为投资承诺，text_fact阻断，其余检查通过 | 限定否定风险目标短语，不允许同句其它正向承诺漏检；Topic显式禁语保持 |
| A16 | quality149把Colossal发布日期2026-10-13判作无依据日期；FP6正文明确该日、as_of为10-19回读日 | 检查允许FactPack正文明确日期，as_of继续单独用于“今天/当前”的时效检查；不得借正文旧日期宣称当日事实 |
| A17 | 科技quality152正常采用后自动refine报stage_preview_failed；继承预览135463B超过128KiB，而显式单方法可用 | 重复method审计正文仅在超限且与完整执行栈严格相同时转hash，保留完整manifest/执行正文与同一GenerateRequest；不放宽大小门禁或删启用方法 |

失败回执见 `evidence/independent/real-stage-failures.json`。本次修复沿用已批准的真实流程检查与事实门禁范围，不新增生成能力或改变模型配置。

### 交接时最终复核（2026-10-20）

- A15/A16：19项边界探针和Python/代码复核通过，正式质量重跑152/153已读。科技8项无blocker、保留一条“绝对”warning并明确理由采用；生活8项pass。原失败148/149保留。语义正确性不由日期出现规则代替。
- A17最终版：主Agent独立运行只读真实反馈重放30/30，完整GenerateRequest/input_hash前后相同，原方法执行栈/manifest自校验/参数保持，claim封套99587B；UTF-16/emoji/空层能被实际UI函数还原；不等正文、商品/@1/混合、仍超限与临界超限继续拒绝。见 `refine-preview-bounds-final.json`。旧 `refine-preview-bounds.json` 的20/20属于仅method去重的中间版。
- TS定向复核由主Agent执行真实源码函数及原JSX：33个函数场景、36个渲染断言通过，见 `prompt-sections-ui-final.json`；这不是浏览器实页已加载最新版的证明。
- 最新源码601项相关既有检查（8项既有弃用warning）、Web类型/构建/bundle、两个Python文件Ruff通过。原14表旧行交接复读一致；见 `handoff-checks.json`、`handoff-current-state.json`。
- **代码与运行边界**：正式API已加载A15/A16与A17中间版，refine156实际生成成功；新增定位反馈再次超限后才写入最终分层去重，最终版尚未重载/执行。科技156未采用，定位返修仅保存反馈未新派发；生活155仍Unknown未重发。图文154仍有事实/关系问题，生活150缺图片，两组新PNG未完成。不能宣称完整真实质量通过。
- 已依用户要求写入同一 `development-handoff.md`，覆盖初始25项要求与下一步。最终验收仍须正常续执行、全部必需真实对照和用户默认决定；尚不归档。

## 2026-10-19 开发授权后的主 Agent 验收准备

用户已授权开发 Agent 按本方案实施，主 Agent 独立验收。以下是开发前的只读观察，未给新实现或新作品判定通过。

- 原件上下文经平台 MCP 实际读取：科技 Project35 的 Unit41/43/44、生活 Project36 的 Unit42/45/46。保存于 `evidence/independent/original-text-contexts.json`、`original-media-contexts.json`，包含当前 Brief、Identity、Fact Boundary、Master 精确引用。读取未生成或修改作品，也不证明旧样本与未来候选具备 A/B 可比性。
- 实际查看科技第2张图（文件索引1）：四类问答案件被以连线串成“正常问题—资料缺失—资料冲突—转人工”，容易把类别与兜底动作误解为同一顺序。后续应按内容选择正确关系，不以增加图形数量代替解释。
- 实际查看生活第2张图（文件索引1）：主要是器物介绍、报道归属和“非独立测评”等说明，给读者的生活启发较少；大块留白是现象，不以填满页面作为改进目标。
- 随后补看其余六张，当前独立静态图覆盖两组全部8张（各文件索引0–3）。科技前三页均使用相同串联方框，未体现“定义三项”“分类情况”“触发分流”的不同语义；第4页主要为边界声明。生活第1页有情境插画，后3页为同一文字模板，分页未充分利用场景和细节表达。未见明显溢出或文字被遮挡；这些现象不代表用户已否定风格，也不自动要求填满留白。
- 旧PNG和hash见 `evidence/independent/original-graphic-visual-review.json`。此前八图算法仅作辅助；本次静态图检查不扩大到音频试听或视频观看。
- 从开发前文件副本独立载入目录，冻结25项旧方法、16项预设、7项质量规则和2套默认蓝图的内容hash，见 `evidence/independent/original-catalog-hashes.json`；75个旧v1包文件当前与副本逐字相同。最终交付仍需再次比对，不能用此中途快照宣称最终保全。
- 独立验收将核对：完整请求方法开关及版本；选定知识/参考用途和权限；定位反馈与失效目标；默认采纳并发保护；五步入口及商品/模型/声音/历史保全；真实产物内容。开发探针和任务勾选不能替代该复核。

当前结论：**开发进行中，最终独立验收待交付。** 新角色默认仍须实际对照后由用户明确采纳。

### 开发中首轮问题与返修

| 编号 | 实际问题 / 影响 | 当前处置 |
|---|---|---|
| A1 | 定位返修意见的执行生命周期错误：最初会持续注入旧反馈；改为只认最新attempt后，又在claim新attempt时丢失旧反馈，第二次preview的hash改变 | 后端独立内存链复验：采用/targets/反馈/preview均200，run409 `stage_resolution_changed`、attempt2 `failed_before_dispatch`。需稳定跨claim且新结果成功采用后不重放；已再次转修 |
| A2 | 相同素材31个版本只返回v31..v2，虽有has_more但API/UI不能翻页；来源还在LIMIT后排除Obsidian，同名摘录可遮住有效来源 | 只读审查者内存探针复现；要求前置过滤与最小分页，待返修/复验 |
| A3 | 既有截图素材未包含在图像参考的查询/形态映射，正常已授权截图无法选用；直接精确引用也被拒绝 | 内存探针复现；要求兼容既有screenshot形态，待返修/复验 |
| A4 | 音视频引用统一使用raw入口，已接受的大于30MiB视频触发storage.read限制，无法预览 | 与现有raw和preview-session/Range合同核对；要求复用现有流式预览，待返修/复验 |
| A5 | v2参考的polarity/inspection若为对象或数组，直接集合成员判断抛TypeError，接口成为500 | 审查者隔离探针复现；要求先做字符串类型判断并返回可读422，待返修/复验 |
| A6 | 镜头方法@2首段强制返回video.shot-plan.v1，后段和新合同要求v2字段，模型指令互相冲突 | 主Agent实际读取新SKILL.md发现；要求以冻结合同区分v1/v2，不改旧@1，待复验 |
| A7 | 知识形态checkbox无条件清空unit_id；原单作品、单次授权保存后扩大到整个项目的相应形态/角色 | 前端审查者执行真实SelectionControls的临时Node探针复现；要求保留作品范围或明确另行变更，已转修 |
| A8 | 事实边界GET的网络/403/500错误被当作成功空结果，页面误报“尚未绑定” | 前端增量路径确认；要求区分读取失败/unknown和成功返回null，已转修 |
| A9 | 页面把最新项目知识称为当前作品实际使用资料；已有Run仍用冻结旧版，显示与执行输入不一致 | 隔离探针对照latest rev2含新笔记、Run rev1空集合确认；要求区分新运行选择和当前冻结输入，已转修 |
| A10 | 切换方法保留新方法不支持的参数（如longform的length），后端422而新表单没有清理入口 | 真实前端函数及后端参数校验复现；需按新方法允许字段保留兼容参数，同时保全模型/音色，已转修 |
| A11 | 同方法从longform@1试用@2时，原candidate_count=4因ref不完全相同而丢失，实际降为默认3 | 后端内存preview对照复现；仅证明生成数量参数丢失，不夸大为音色/模型改变；要求兼容版本参数继承，已转修 |
| A12 | 新v2镜头的continuity/sound/reference_index在生成Master后从专业导演包消失，剪辑执行器拿不到已接受的指示 | 无替身内存全链script→shots→master→prepare均200，Master请求有细节而prepare/package无细节；要求精确已接受方案传到导演包，已转修 |
| A13 | 阶段面板默认仍展开Workflow/checksum、plugin/schema与accepted hash，未落实design第1节“技术标识折叠、默认当前结果/问题/下一步” | 主Agent定点界面对照源码确认；只收起技术详情，不改阶段或执行合同，已转修 |

以上是开发期间的局部问题，不把尚未交付的整体功能判成最终失败。开发自述修复后仍需主 Agent 按实际文件和运行结果复验。

首轮参考审查未写任何代码或正式数据，探针为SQLite内存库/内存文件，v1样本hash与前态相同。审查范围文件hash已记录于 `evidence/independent/reference-first-review.json`；最终修复必须重新核验，不沿用本次hash作通过依据。

### 参考返修的独立服务层复验

主 Agent另写一次性标准输入探针，实际运行SQLite内存库：12/12通过，见 `evidence/independent/reference-recheck.json`。A2的31版翻页、精确修订查询、Obsidian在LIMIT前排除；A3截图查询与精确引用保存校验；A5对象/数组非法枚举返回422；撤权素材从列表排除且直接引用409均通过。A4这里只验证投影给出现有preview-session路径，尚未检查大文件真实流式播放或浏览器；A2的界面翻页也留待UI检查。A6实际重读方法文件已明确v1兼容与v2按冻结合同返回，不再强制旧信封；真实模型输出仍待样本。

反馈返修第二次独立复验：claim后的run已可200，但`succeeded`待采用状态又丢失冻结意见，`accept-master`报409 `stage_adoption_context_changed`。临时入口 `/tmp/persona-backend-review-probes.py feedback` 保留，待第三次修复后复验；第一次探针的临时node/config替身已移除，本次是无替身真实内存服务链。A7最新Node探针已保留unit_id，A8代码已独立区分unknown，浏览器仍待。本轮审查未改任何持久测试；共享测试文件存在相邻/外部变化，保留，不计为本需求新增成果。

### 第三轮后端独立复验

主 Agent在新进程直接运行审查者的四个临时入口，无替身、SQLite内存/Mock，均完成且输出已读：

- `backend-feedback.json`：A1初次采用、targets、反馈、preview、重跑、返修采用与最终preview全200；两个Attempt均succeeded，最终不再注入旧意见。A1本条文字主稿生命周期已通过，其它形态仍按各自验收覆盖。
- `backend-trial_parameters.json`：A11新旧同方法预览均ready，candidate_count=4、length=medium保持，未做真实模型调用。
- `backend-method_switches.json`：完整build_master_request中，继承/全关/单关/双开正文计数正确；关闭项0，启用项各1；阶段说明仅在适用继承路径1次。
- `backend-knowledge_scopes.json`：旧选择仅text，显式新选择graphic/video；商品排除；研究professional、声音style、确定性阶段无正文；撤权返回`knowledge_model_use_revoked`。

以上证据位于 `evidence/independent/`，验证具体服务链而非真实创作质量，不能代替第5组样本或用户风格决定。

### 前端定向独立复验

主 Agent重新执行只读审查者的临时Node探针，真实组件函数、后端投影与参数校验共6项通过，回执 `evidence/independent/frontend-final-recheck.jsonl`。A7保留单作品授权且旧选择仅文字；A8失败显示未知、成功空值才显示未绑定；A9当前Run冻结rev1与下次新运行rev2分开；A10兼容参数保留、不兼容参数清理，不兼容音频切换拒绝且保留原音色。409后保留方法草稿、合并最新模型/声音并重新预览，最终保存体通过真实后端校验。这里是内存组件/服务探针，尚不等同于浏览器操作或正式配置保存；文件hash随回执记录。

### 导演计划及新候选反馈复验

只读后端审查对A12修复局部复验通过，完整计划、冻结采用目标、Master ID/hash在prepare与导演包一致；伪造冻结引用、采用候选、Master来源均409，删除或篡改包内方案即使重算包hash仍被采用证明拒绝。出现新镜头候选时旧Master拒绝漂移。旧v1全链200且无新增字段。反馈A→未采用候选→新反馈B→第三轮运行/采用全200，新意见B进入preview与冻结快照，采用后不重放。证据已保存于 `evidence/independent/a12-{v2,v1,feedback-priority}.json` 和 `a12-final-hashes.txt`。这是内存隔离链和代码审查，不代表真实视频已剪辑或声音已试听。

### 主 Agent页面、传输与方法复验

- A13独立浏览器复验通过：角色五步切换保留作品及return_to，技术标识默认折叠，浏览器返回来源/前进回到作品正确。375px制作页和参考页无全页横向溢出，文本参考搜索/精确版本预览正常。零page error，124个业务请求全部为隔离5174的GET；没有向正式平台写入。阶段切换沿用原有replace导航，不要求浏览器后退逐阶段翻回。见 `browser-readonly.json`。
- A4独立传输探针通过：内存库中明确标注的合成accepted夹具，合法1秒MP4加free容器填充到31MiB；实际preview-session200、首/中/尾Range206、全量字节hash一致，无Cookie401、无效Range416、hash不一致及撤权409。见 `video-preview-range.json`。只证明超过30MiB传输链，无用户素材采用或真实视频质量结论。
- 两角色文字/图文/音频规划/视频AI节点的真实请求构造器，逐项检查继承、单项关闭、阶段关闭、启用，以及Identity与作品级覆盖。启用正文各1次、关闭0、旧阶段指导只在继承时进入。见 `all-form-chat-switches.json`。未派发模型；原生TTS、确定性排版及专业执行包按对应工具合同另验，不把提示类方法自动用于原生工具。
- 最终旧目录50项资源hash全部一致，75个旧v1文件逐字一致；见 `catalog-final-preservation.json`、`old-files-final-preservation.json`。正式库14表行数一致，但开工表hash的原序列化尚未复现，不能据此宣称整表内容保全或数据发生变化。原科技作品MCP回读Master61 v4及Brief/事实边界hash与开工独立记录一致。

## 2026-10-19 OpenSpec 提案检查

- 结论范围：仅方案结构和一致性检查，未实施、未运行真实生成或前端验收。
- `openspec validate improve-persona-content-methods --strict` 通过，回执 `evidence/proposal-strict.txt`。
- 六项现有 capability 增量：14条新增、3条修改；修改标题与 canonical 一致。所有增量均有场景，未直接写 canonical。
- 25项实施任务全部未勾选；CLI四类 artifact齐全只表示方案可供确认。
- 21个相关工作台/配置/服务源文件与提案前指纹相同；未对数据库做读取/写入，不把文件指纹当正式数据验收。
- 相对链接、尾随空白与任务计数检查通过，证据 `evidence/proposal-checks.json`；`git diff --check` 通过。
- 明确保留原角色五步、商品六步、模型/原音色/参数；新方法只供试验，默认采纳与用户风格决定单列。
- 收口修正：用户不采纳候选时不能把该项勾成默认风格通过，保留旧默认及未完成状态，除非用户明确调整范围。

### 计划文档独立复核

按 writing-plans 的文档复核步骤完成只读审阅，结论为未发现阻断提案的问题。六项补充均有页面、方法职责、增量规范和任务承接；科技/生活对照范围一致；原五步、商品六步、模型/音色/路由、历史和发布边界明确；试用与默认采纳分开。

剩余事实限制：旧样本是否同条件需实施核验；新schema具体兼容、局部返修与真实质量未验证；视频素材与用户风格决定可能使对应任务待完成。审阅未改文件、未运行模型或验证运行时功能。

当前结论：**方案可交用户确认，实施仍0/25。** 以下为此前研究证据，不能替代新功能验收。

## 已验证
- 固定源码 SHA，实际 Skill 文件数 114；README 徽标与当前目录计数不完全一致。
- 上游布局自检 5/5；现有八图检查 8/8 报警，底部空带约 31.7%–65.6%。
- 代码是横向边缘密度分析；能提示空带和重心，不能判断语义、审美及信息是否正确。不能为了通过阈值堆字。
- 前一轮图片流程与可读性验收不等于充分的视觉质量验收，本次发现补充了这一缺口。

## 未验证
未运行 Easel 全测试、全模型生成或发布；未评估所有 114 项；未验证转化率或全部样片质量。测试目录、README 展示和自评阈值不足以证明所有 Skills 已得到实际业务验证。

## 来源边界
根 LICENSE 为 Apache-2.0；各 Skill 的来源应单独检查。auto-short-video 元数据仍注明许可待核实；card-design 说明借鉴包含 AGPL 来源但未复制文件。这些是上游声明，不能据此作整体复制许可保证。当前仅研究方法。

> 2026-10-20 更正：上文"素材清单"第1、2、4项只是缺口描述，不是平台提示。平台在 recipe 镜头计划阶段只产出自由文本 unknowns（asset_requirements 全空）；素材描述/据图提示词由 Video Studio 镜头制作环节生成，样本未走到该环节。5.4/5.5 的素材应走平台该环节再提供，详见 findings.md 同日条目。第3项已由用户确认：视频通用底座为 Resolve 主剪 + AE 动效。
