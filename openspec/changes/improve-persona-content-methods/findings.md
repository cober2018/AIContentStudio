# Easel 方法与适配结论

## 接手续做发现（2026-10-20）

- 卡片计划两轮都把“转人工”画成第4种情形，根因在已采用的上游视觉方案层级，不在卡片阶段；只返修下游会反复继承。修上游并让下游按stale重查是最小正确范围。
- 视觉方向没有页/段/时间定位，无定位整阶段反馈不会进入重做提示；本次改用合同允许的本次`instruction`覆盖，属登记变项。
- 卡片“定位返修”在现有工具中仍是整阶段重做（预览已标current_stage_full_output），未定位页可能退步（card-1重新出现“置信要求”）；验收必须逐页复看，不能只看被定位页。
- 图文合成器按原层高度排版，人工缩短文字会留下不均间距；三张卡下半部大面积空白是排版密度问题，按设计只作诊断不作硬门槛。
- Unknown attempt会永久阻止同一step新调用，现有合同没有正常解除路径；这是有意的安全设计，继续需用户决定（新run或接受已有Master）。
- 同一项目里做A/B时，渲染PNG被系统自动挂为项目共享素材，后跑的一方会读到并模仿另一方版式；必须先解除渲染产物的项目共享引用。
- 共享素材只给模型kind/hash时，AI插画会被当成实拍（A19已修，仅角色域）。
- 文字AI阶段不产出引用，含日期等数字的稿件会被角色质检拦下，需人工补引用；补引用要同时写正文citations与evidence定位。
- 定位反馈里补入的事实必须先进事实包；事实边界一变，整条run的采用都会失效（正确保护），之后可用Master级检查交付。
- 创作方法、导演包准备、规则质检阶段都贴着128KiB快照上限；事实包从3条到5条就足以越线（A20/A21修两类，质检阶段仍开放）。
- 科技角色的capability-memory方法会在自动续接时遮蔽节点@2；生活角色不会。
- 复用原题的本次覆盖要只留通用合同部分，否则会把原题结构带进新题（科技新题音频曾被带成“三类评估建议”）。
- 服务端日期检查按UTC；台北凌晨录入当天as_of会被判为未来。

## 进入 OpenSpec 方案的实际核对（2026-10-19）

- 用户明确先审方案；当前 canonical 是六项既有 capability，未新设业务模块。正式规格只读，本次写 change delta。
- 当前角色入口代码确为 `goal/plan/make/review/delivery` 五步；商品仍为独立六步。方案仅增加角色子任务，不将前文用户视角六个动作实现为新引擎。
- `PersonaReferenceStylePanel` 实际位于 `CapabilityMemoryPanel.tsx`，现有正常表单需要填 source/material ID和hash，并且观察枚举未含audio；方案列出选材/预览和音频兼容扩展。
- catalog 已含 evidence/angle/text/graphic/audio/video 方法，starter已有文字九阶段和图文四阶段；增强现有新版本，不再造“已存在”的方法入口。
- 保存/执行/反馈与默认采纳已有规范；需要验收实际请求和差异保存，不以文档存在替代运行证据。
- MCP 图谱工具在本会话工具清单中不可用，采用相关文档和已定位文件的有限阅读，没有全量代码扫描。
- `main@8539806` 加大量在途变更；本轮只写本目录及旧研究跳转/根README说明，保留21项相关代码指纹。数据库未访问/修改，不声称完成正式数据保全验收。
- OpenSpec 已安装且能生成/验证提案；初始CLI遥测因网络不可达报错，后续用命令级 `OPENSPEC_TELEMETRY=0` 完成本地检查，不改用户设置。

## 核心架构
发现→策划→制作→发布→归因。Profile 分 identity、style、audience、platforms、preferences、memory，各阶段按需使用；反馈是可复用经验，不是聊天流水。可借鉴阶段化上下文，但我们继续区分角色、账号、品类、SKU 与单次作品，不把商品变为角色。

## 角色内容工作台补充（2026-10-19）

用户已明确：角色内容工作台是主要参考对象，商品仅为适用能力的分支。以下是补充建议，不是已批准的实施任务。

### 现有基础，避免重建

正式规格已包含：
- `persona-creative-configuration`：四种形态的角色配置、阶段开关、实际执行留痕。
- `studio-creative-skill-pack`：方法与风格预设分开、按需参考资料、来源记录；已有 Easel-inspired method design 场景。
- `creation-recipe-stage-control-loop`：中间策划产物、阶段交接、反馈与显式保存有效配置。
- `persona-reference-style`：参考观察、采纳版本、新主题对照和用户风格确认。
- `obsidian-knowledge-context`：专业内容与写作风格用途分开，选定资料版本可追溯。

这是规格核对，不代表本轮对以上实现重新验收。下一步应逐项核对“规范—实际请求—成品”，优先补质量差距，而非再造角色配置或工作流。

### 值得补充到方案的具体考虑

1. 角色既有方法选择与风格配置应共同构成可用默认方案。通用方法可共享，科技/生活在取材、叙事、视觉和声音上分别配置；不为每个角色复制整套 Skills。
2. 在制作前明确本次给谁看、回答什么问题、核心观点与依据、目标平台及形态。共享已确认的内容和来源，但文章、图文、音频、视频分别策划，避免直接拆字数或机械朗读。
3. 用用户认可的样稿/样图/样片及不希望重复的反例校准风格，说明具体喜欢什么；用新主题检查方法能否迁移。借鉴表达，不继承参考作者的身份和经历。
4. 每阶段只读取相关、允许使用的知识片段和风格参考；本轮不扩展 Obsidian 授权范围或自动导入整库。专业背景、已核实事实与风格样本各有用途。
5. 正常页面聚焦当前任务、结果和下一步；方法、模型、参考版本折叠为可追溯详情。失败或质量不足应能定位到一页图、一段文案或一段音频再返修，复用既有阶段控制。
6. 反馈先绑定当前产物和版本，再由用户选择是否作为该角色/栏目/形态的长期偏好；不把一次修改自动推广为全局规则，也不把播放量单独当作质量标准。
7. 首批验收同时区分技术可用、内容质量和角色风格认可。固定题目、资料与模型比较方法变化，再用新题验证；占高/留白等量化指标只是诊断，不能强迫每种风格填满页面。

建议用户流程：选角色与本次形式 → 选题/资料 → 确认内容方向 → 分形态制作 → 审阅交付 → 反馈。此为用户视角说明，复用已有工作流真值，不要求新增六步引擎或一次生成全部形态。

## 方法映射
| 上游方法 | 本平台适配 | 不直接搬用 |
|---|---|---|
| card-design + carousel planner | 每页先定阅读目的和图形结构，再锁配色、字体、排版，渲染后检查 | 固定页数、强制好奇钩子、硬填满画面 |
| style-transfer + text-polisher | 事实不变的风格调整，与清晰度、证据、具体性检查分开 | 删除不确定性、机械删副词或套口头禅 |
| ecom-details-image | 先选购买驱动力，按已知商品事实安排场景/细节/证据，并锁定商品与整套视觉 | 默认大量商品图、强制优惠/紧迫感、虚构背书或未拍到的结构 |
| short-drama | 人物/场景/道具索引、逐镜依赖、首尾连续性、真实时长、逐镜重试与检查 | 全部 AI 图生视频、照搬原生音频策略、把低 ASR 阈值当商品事实验收 |
| audio-mix | 旁白、配乐、音效分轨，按旁白压低配乐，保留时间定位 | 强制配乐或改变现有音色配置 |
| auto-short-video | 产物分离、可替换镜头、逐阶段检查 | 逐句图片缓动作为商品默认片型；静默跳过必需声音 |
| profile + memory | 版本化风格与经验，按适用范围使用 | 一次反馈自动成为全局规则 |

## 对现有平台最有价值的改进顺序
1. 图文：分页叙事、按内容选择关系图/对比/数据/场景，而不只是文字列表；渲染后可定位返修。
2. 文字：把风格转换与质量检查拆开，保留事实、证据和原有选区边界。
3. 视频：将连续性和素材索引融入已有拍摄任务书；实拍素材不够时明确补拍，逐镜定位问题。导演方法与 Resolve / AE 执行适配分开。
4. 声音：独立音轨与可选配乐策略，检查整体混音和字幕时序。

这是一份研究建议，不表示这些改进已获实施授权。首批宜用同一条已核实文章做旧版/新版图文对照，再决定默认配置；商品继续采用已确认的四段实拍任务，不增加无目的镜头。

## 规则不一致与质量限制
card-design 文档与审计脚本的占高阈值存在差异，脚本采用 0.80；因此需要自有可解释门槛，不能简单照抄。商品详情页的强制图数、统一字体组合和背景轮换是偏好，不是普适准则。上游所谓高转化与自评分不视为实证。

## 源码索引（固定版本）
- [README.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/README.md)
- [LICENSE](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/LICENSE)
- [docs/skill-function-mapping.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/docs/skill-function-mapping.md)
- [profiles/_template/README.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/profiles/_template/README.md)
- [skills/builtin/card-design/SKILL.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/card-design/SKILL.md)
- [skills/builtin/card-design/scripts/card_audit.py](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/card-design/scripts/card_audit.py)
- [skills/builtin/card-design/EASEL-META.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/card-design/EASEL-META.md)
- [skills/builtin/skill-carousel-planner/SKILL.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/skill-carousel-planner/SKILL.md)
- [skills/builtin/style-transfer/SKILL.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/style-transfer/SKILL.md)
- [skills/builtin/text-polisher/SKILL.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/text-polisher/SKILL.md)
- [skills/builtin/ecom-details-image/SKILL.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/ecom-details-image/SKILL.md)
- [skills/builtin/ecom-details-image/references/pdp-sequences.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/ecom-details-image/references/pdp-sequences.md)
- [skills/builtin/auto-short-video/SKILL.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/auto-short-video/SKILL.md)
- [skills/builtin/auto-short-video/EASEL-META.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/auto-short-video/EASEL-META.md)
- [skills/builtin/short-drama/SKILL.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/short-drama/SKILL.md)
- [skills/builtin/audio-mix/SKILL.md](https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/audio-mix/SKILL.md)

## 开发自检边界（2026-10-19）

2026-10-20接续收口：只压缩method重复正文不足以容纳真实定位反馈。A17最终仅对原超限且可证明相同的persona/@2/master-propose快照去重审计正文及prompt_sections，完整执行prompt/creative栈/manifest仍保存；UTF-16位置供现有前端还原原分层。正常小形状/历史hash不变，不抬高全局容量。只读真实反馈重放30项证明完整GenerateRequest及input_hash不变，claim封套99587B。代码、服务已加载版本和真实样本质量必须分别交接，不能用早版20项结论冒充最终版或正式续执行。

2026-10-20真实续验发现：accept-master/accept-creative/accept-result会自动派发一个后续就绪阶段；调用说明和证据必须包含此副作用，不重复显式run。仅改工作流节点@2仍可能被继承capability-memory方法遮蔽，B需要仅本作品的明确配置并核对真实method_stack，错方法尝试保留，不算正确@2样本。两份真实初稿都有事实/保证退步，编辑修正与模型原生能力分开。日期规则仅证明日期出现于冻结资料，日期所指角色仍由现有语义审核核验；as_of不被正文旧日期替代。

- 关闭文字阶段或关闭两个试验方法时，草稿请求没有长文/精修 `@2` 正文。请求 JSON 里仍能看到蓝图节点默认的 `studio.text.longform@1` skill_ref。这是配置引用，不是方法正文；3.6 不能据此勾选。
- 角色导演准备若再从节点配置加载方法，会把未选中的 `@1` 正文送进专业请求。修复后角色域使用冻结方法栈；商品域没有改成同一条路径。
- `data-preservation-recheck.json` 不能当作正式数据已被改写或仍然一致的证据。可用的只是行数复验。
- 隔离请求使用 Mock 模型。技术通过、内容质量和用户是否采纳角色默认风格仍然是三件不同的事。

- 试用配方钉住的Run在automatic续接下每节点回执仍为@2（auto-continue-probe.json）；@1回退只发生在默认v1定义或阶段选择含继承capability-memory方法时，这是冻结语义而非缺陷，B样本仍需仅本作品显式配置并核对真实method_stack。
- checks节点快照的master payload原来有三份相同拷贝（context、__current_master__、上游边），这是图文质检超限的主因；去重后单份payload+压缩分段即可容纳四卡真实体量。payload_ref先例来自audio_qc，不改变AI阶段的prompt内容。
- freshness的“未来”判断必须以操作者本地日为界：UTC上界会把台北凌晨录入的当天日期误判为未来；本地日末上界不影响过期排除，也不放行真正未来日期。

2026-10-20 视频素材提示来源（用户纠正后核实）：用户要求素材场景/提示词必须由平台在脚本、分镜阶段提示，而非人工手写。核实代码与规格：①角色 recipe 的 `studio.video.shot-director`（v1/v2）规则为"没有素材就让 asset_requirements 为空"，缺口只写在自由文本 `unknowns`，没有结构化素材需求，也不产出图片描述；U65–U70 六份计划实测 asset_requirements 全为空。②平台已有的素材提示在 Video Studio 镜头制作环节：镜头 `production`（web_video / grok|gemini）→ 确认参考图 → AI 辅助写"据图动态提示词"（非 web_video 镜头为"素材描述"）→ 人工网页交接 → 回传接受；真实样本从未进入这一环节（只做到导演包）。③此前手写的 Grok 提示词文件已删除，不作为平台能力或验收证据。④视频底座规格已明确：Resolve 主剪、AE 仅做需要的动效包装（edit_contract 含 resolve_project / ae_project）。是否把 shot-director 改成输出结构化素材需求属范围扩大，待用户确认；未确认前不改代码。

2026-10-20 读《NorthStar V2 蓝图》后的对照：§23/§41 素材必须保留 prompt、generation_info、rights、hash，§24 视频血缘含 shot_plan→source_assets，§21 图/视/文平级且可互相派生，§33 Skill 降级、不能当业务真源，§37 支持 Replace Asset/Override Instruction，§39/§57 人工是一等节点、结果未知先核对，§51 外部能力（Grok/Gemini 网页、Resolve、AE）是可替换工具。据此：素材需求与描述应由平台合同和 Image/Video Engine 产生并带血缘，手写提示词会丢失血缘；shot-director 把"无素材则 asset_requirements 为空"只写在 Skill 文本里属于层级错位，记为相对蓝图的缺口，是否在本 change 内修另行确认。运行事实（只读库）：平台已有 provider_generation_task 图片任务——openai.compatible/grok-imagine-image 4 条 accepted、minimax.cli/image-01 4 条（2 accepted），所以静态参考图可由平台原生生成；Grok 视频仍是人工网页交接。原生 xai/google 适配器需 AICS_ENABLE_NATIVE_MODEL_ADAPTERS=1，当前 launchd 未设置，未使用。

2026-10-20 用户确认口径与"开辟者—裂变"目标：已按确认把 5.4/5.5 验收改为"平台引导链路+留痕"，并在 creation-recipe-stage-control-loop 增量规格新增"Shot plans surface material needs through the platform"（strict 校验通过）。用户进一步明确平台最关键能力是把顶级模型跑通的路径沉淀为模板，供低成本模型在相似主题上复现。现状：平台有阶段级 save-adjustment/adopt-recipe/Capability Memory（单阶段配置补丁+反馈/尝试证据），未核实存在"整条路径"的模板导出/复用；本轮开辟的路径知识（显式@2、spoken 阶段指令覆盖、cards 引用修正、引用 citations 结构、事实包先于定位反馈、渲染产物 A/B 隔离、media 暂存名额、UTC as_of）只在 evidence/real-samples/stage-overrides.json 与本文件中，没有进入平台。此为新能力，范围超出本 change，需另行 /opsx:propose。

2026-10-21 用户调整优先级：模板沉淀与低成本模型复用是平台要具备的能力，但当前聚焦是先由我（顶级模型）把整条流程真实跑完、效果做好；跑出最好的第一版之后，再考虑做成模板并逐步提升其他模型照模板的效果。因此暂不发起"路径模板"新提案；本 change 剩余项按"整链跑通+成品质量"推进，过程中继续把每步方法/覆盖/反馈/人工修改留痕，为以后模板化留素材。

2026-10-21 科技新题成片实跑（P39/U69）发现：
- Master合成阶段缺陷：`stage_master_proposals._video_plan` 只接收beats，模型不给duration_ms时每镜默认1500ms、单镜上限15000ms，且固定 voice=none、subtitles空；分镜计划20/18/21/16/24s的真实时长、旁白和字幕都没进Master114（7.5s）。已用人工修订Master117（user_edit，平台留痕）补正，未改代码。
- 视频旁白必须按视频脚本单独出：原音频素材104是长文口播（209s），不对应视频脚本。新建旁白单元U71（源=Master114脚本，种子Master116）走平台音频链：spoken@2→voice→TTS→ASR→QC，得素材106（166.1s，speech-2.8-hd/lengdan_xiongzhang/rate1.0，−23 LUFS，无削波）；ASR相似0.938，差异为大小写/同音/数字写法，"README"英文读音待人工试听。voice阶段实际方法为capability-memory 5而非@2（既有遮蔽问题再现）。
- 视频脚本860字按该音色约166s，远超分镜计划99s；旁白驱动时长，镜头边界按ASR对齐：0/33.3/65.0/98.9/125.0/166.1s，字幕59条（≤25字，文本取已采用口播稿，时间取ASR）。
- 平台素材提示缺口实证：form-assistance 对 `shots.*.production.prompt` 一律走"据已确认参考图写动态提示词"，无参考图时全部 blocked（会话19）；平台没有"按镜头需求起草出图描述"的环节，与本change新增需求"Shot plans surface material needs through the platform"一致。
- 同题图文Master104的4张卡（3:4、文字为主）不适合作镜头源：直接上166s竖屏时间线会变成幻灯片，违背平台视频方法"不得把不足素材默默做成单图幻灯片"。
- 2026-10-21 已按用户选择补平台缺口（task 3.7）：`form_assistance.run_attempt` 对已保存为 api_image/ae 的镜头，`shots.*.production.prompt` 不再要求参考图，改按镜头目的/脚本/项目依据起草出图描述，并把已保存 aspect_ratio 与镜头时长随 `material_need_targets` 交给模型；web_video 仍走"先确认图再写动态提示词"。首版漏传画幅时模型写成16:9（会话20），补传后会话21五镜均为9:16、无文字、标明示意。现有相关检查：无表单助手测试；视频文档72项通过；正式API已重载并实调验证。
- 平台出图（Grok image，9:16，每镜2候选）10张均为720×1280 JPEG，无文字、配色统一；成片需放大到1080×1920，AE中会略软。按平台视频方法，镜头选图须用户确认，未代选。
- 2026-10-21 成片执行发现：①Resolve字幕烧录默认样式（约100px、两侧裁切）脚本不可调，改在AE按同一字幕时刻烧录，Resolve保留字幕轨并单独交付SRT；②SetRenderSettings中任一键无效（VideoQuality需整数码率）会使整次设置失败，且残留上次的BurnIn设置，导致首版粗剪双字幕，已删除重渲；③Resolve AAC尾部补零使音轨166.165s，超出平台35ms时长容差被拒，按平台原生说明用流复制限定到166.1s，原生渲染保留在work/；④AppendToTimeline对字幕忽略recordFrame，须在空时间线先放字幕；⑤本会话无AE MCP，改用AE原生ExtendScript（DoScriptFile），仍为原生图层/关键帧。
- 粗剪已知问题（待人工审阅后经新Master进入精修）：响度−11 LUFS（单声道旁白在立体声轨+3dB，精修改+6dB）；4处字幕断句（截|图≈89.7s、一|千零四十≈143s、"在移动|Agent"≈162s、"模型 API 的"≈121s）；源图720×1280放大后略软；无配乐（方法允许）。未经人工试听。
- 2026-10-21 用户评审第一版粗剪：流程通、搭配可以；文案不够好；画面像PPT、不高级；素材过少（仅生成图做底）。已确认后续手段优先级：①平台功能（含提升平台能力）②网上找素材 ③代码生成视频素材（仅作素材）；特效/剪辑方案靠大模型，不足再找skills。
- 2026-10-21 用户授权：项目自身 GitHub 演示视频/截图可用于第二版，仅本地评审、注明出处、不公开发布；入库时权利记 public=False、commercial=False。
- 2026-10-21 第一版文案弱的根因（已核实）：①角色视频档案的script阶段enabled=false，第一版脚本阶段method正文为空，studio.video.script@2从未加载；②脚本阶段拿到的是图文Brief（目标为“工程解读文章”）；③内置script@2只讲结构与授权，不含开头钩子、留存、竖屏时长、口语节奏。第二版用作品级制作配置开启方法+阶段指令覆盖解决，未改代码。
- 平台缺口（待用户决定是否立项）：视频工作流的脚本/镜头阶段看不到项目素材目录（shared_asset_refs只给图文合成工作流且要求公开图片），模型无法引用已入库实拍；镜头计划把素材号写进reference_index即被拒（stage_creative_output_invalid），只能写在文字字段。阶段指令覆盖上限约2KB；创意阶段失败时不保存原始输出，只留validation_code；Master阶段不带方法覆盖时因继承四个脚本方法超限（stage_value_too_large）。
- Master引用受限素材须model_use_allowed=true或public；首登记为false的实拍需重新登记（素材112–115→117–120，音乐26→121），旧修订保留未用。
- 2026-10-21 第二版剪辑发现：①作品级production_stages会整体替代角色剪辑阶段方法，只写script会让导演包剪辑方法为空（use_capability返回invalid_arguments，receipts为空）；需把六个剪辑阶段一并写入。②导演包要求每镜有source素材，纯动效镜头也需底层素材。③编辑清单timeline每镜只能登记shot的单一来源，多来源镜头的剪辑表只能放在附加字段footage_cuts。④Resolve脚本接口可开对白电平器但无限幅器：TTS峰值因数约20dB，+6dB即真峰值+2.2dBTP削波；不削波版本为−21.4 LUFS/−1.6 dBTP，响度提升到−14需Fairlight限幅（人工或后续平台能力）。⑤作者演示源片有卡片位移与“sped up”标签，入出点须逐段核对。
- 2026-10-21 平台改进实施发现：①素材库文件被刻意要求单一硬链接（防止同用户执行端写穿素材库），故输入改用APFS写时复制克隆而非硬链接/软链接（用户选定）；②materialize_inputs原不提交会话，审计行会丢失，已补提交；③输出元数据只允许扁平字符串，响度读数以紧凑JSON字符串保存，执行端自报的loudness被丢弃；④作品当前Master较大（如Master124/119）时，规划阶段预览整体超过128KB被拒，与素材目录无关，另记待处理。
- 2026-10-21 角色默认采纳发现：script阶段同时启用@3与三个写作记忆时，方法正文在解析结果中重复约5处，加素材目录后单次阶段约136KB，超过128KB上限（stage_value_too_large）；按用户意图只启用@3、其余保留关闭后可用。阶段解析结果重复携带方法正文是128KB超限的共同原因之一（另见大Master超限），待另行处理。
- 2026-10-21 超限定位：阶段解析快照统一受128KB限制。实测（库副本）角色2新作品脚本@3+三方法133KB；成片U72脚本/镜头/Master/导演包261/228/259/185KB，Master在context、upstream、提示词、提示分层各一份（约27KB×4），提示分层整份重复提示词；现有压缩只认内置@2方法。即使去掉全部重复U72仍约157KB，故立项 raise-resolved-stage-snapshot-bound（解析快照上限调到512KB，其余上限不变），待用户确认。
- 2026-10-21 已修：解析快照上限改为512KB（raise-resolved-stage-snapshot-bound，hash同步）；U72各规划阶段与角色2@3+三写作方法均可预览。角色2修订7恢复写作方法4/6/8与@3同开。
- 2026-10-22 角色基础阶段配置（数据修订，未改代码）：阶段一旦配置，平台只用该阶段列出的方法、丢弃节点自带内置方法（`freeze_production_stages` execution_rule）。旧配置导致：研究只剩能力记忆#1、图文分镜丢失visual-director/card-plan、视频导演包节点零方法、文字/图文/音频脚本阶段关闭后草稿无任何方法。现每阶段=平台内置方法(@1，视频脚本/分镜沿用@3，终混加director-package@1)+自有方法#1–#12；按节点输出格式自动过滤，已逐节点核验。角色2→修订9，角色3→修订3；角色3关闭“讲解：从问题到机制”和“包装：AE分层镜头”（两者按科技样片调校），可在创作配置中打开。修订前快照在会话草稿目录。
