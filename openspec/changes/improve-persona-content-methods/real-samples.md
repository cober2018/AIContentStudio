# 真实文字与图文样本登记

本文件为本需求唯一真实样本登记；持续计划、进度与总评由主 Agent维护。当前已运行真实模型并保存回执；科技正文已有未接受初稿，图文尚未完成PNG，不作整组质量通过结论。

## 范围与执行规则

- 原科技 Project35 / Unit41、43 / Master61v4、73v4；生活 Project36 / Unit42、45 / Master65v4、74v3全部只读，原样本只作缺陷依据。
- 独立项目通过正常 API新建，复制原 Brief、冻结事实包、空知识选择及基础角色；正常创建明确命名的 A/B作品。两角色分别比较，不互相排名。
- A 使用当前方法@1；B仅将适用方法升至@2及其必需的兼容输出合同，原生成参数、角色风格、模型路由保持。原产物经过人工编辑，完整同条件生产链未能证明，不能强标为严格 A；各形态只补一次同配置 A。
- 每个候选一次生成；遇具体内容/合同缺陷最多定点返修一次。Unknown保留回执，不盲重发，不改模型。技术、内容质量、用户风格采纳分别记录。
- 来源、Brief、角色及工作流完整安全快照在 `evidence/real-samples/original-*.json`；新操作/请求/回执在同目录，`operations.jsonl`逐项记录。原15表明确定义指纹沿用主 Agent的 `evidence/independent/before-real-samples-preservation.json`，旧14表序列化未复现的内容结论保持未知。

## 生成前的问题与成功标准

| 角色/形式 | 实际缺陷依据 | 本轮成功标准 |
| --- | --- | --- |
| 科技文字 | 原Master61v4大量抽象小标题、定义与检查清单；读者需要跨多节自行拼出可用的判断方法 | 一个具体的明确假设示例贯穿输入、依据、判定及异常；建议/事实/未知界限清楚，避免空泛术语和未经验证的因果保证，至少解决结构或具体性的一项问题 |
| 生活文字 | 原Master65v4单独长段解释未亲测/测评缺席，并在设想场景后重复效果边界，打断观察节奏 | 自然具体、以小场景推进；必要来源归属不丢，但不反复免责声明；设想明示，不编造亲历、使用效果或购买建议；保持原Brief900–1200字目标 |
| 科技图文 | 已查看原8张PNG中的科技页1–3：并列定义/类别被串成顺序，页4主要是声明 | 每页一个解释目的；并列/对比/条件分支与内容语义匹配，不把类别画成因果流程；完整组图逐张检查、手机可读、不裁切溢出 |
| 生活图文 | 原页2主要是来源/免责；页3标题窗台、正文沙发/长椅且无场景图；整组视觉叙事不足 | 页与页有推进，每页场景/文字一致、视觉承担信息；必要边界保留而非占据叙事中心；完整组图逐张检查、手机可读、不编造实物使用经历 |

以上在真实B生成前登记，后续按位置记通过、需改或未检查，不以评分替代产物评审，也不作统计或转化率因果结论。

## 对照题目与冻结来源

| 角色 | 同题 | 输入冻结 | 新主题（未参与原风格提炼） |
| --- | --- | --- | --- |
| 科技2 | 从 Demo 到可用：先写清怎样才算答对 | 原Brief39 checksum `2d95276c8654e1d58e563a525db60ce67901f446c1b3d9eebf648c17fb0e931f`；FP4v1 checksum `1bf156e77eb1620b96a024a4a9bf948bb7099ad60cfb4fee9a0441de7d94e3e9`；原知选rev0空集合。事实包是创作方方法建议，不能当独立验证的工程结果 | 机会19：ESP32-iPhone-Agent的硬件输入/画面路径与工程边界；按既有原文证据及授权进一步冻结，未执行新题生成 |
| 生活3 | 画两笔之前，能不能少准备一点 | 原Brief40 checksum `8b235c8c80be3c1d2c69d6541017de7e82d2c6764e4483a2cdd1cd849712b33a`；FP6v1 checksum `1a611e4d882f00e5ee948eb6dad82aa33285847bc2cf6418c68213cd0d55824c`；原知选rev0空集合。仅归属Colossal产品介绍、不证明实测效果 | 机会7：走进针孔暗箱，只看一会儿不必留下照片；按既有原文证据及授权进一步冻结，未执行新题生成 |

## 实际执行

`///` 1. 只读冻结原作品、Brief/知识/事实包、模型参数与renderer，并登记缺陷和标准。

`///` 2. 正常API创建独立试验项目/作品，保存原工作流克隆；A@1、B@2，不改角色默认。

`///` 3. 每次运行先预览并核对实际路由/方法/参数，再正常run与按准确hash采用；先科技和生活正文B，再完整PNG。

`///` 4. 将正文与逐张实际PNG交主 Agent质量复核；有具体缺陷只做一次定位返修。随后完成一次A及有条件的新题B。

`///` 5. 回读实际保存版本、产物hash/配置/本地包，供主 Agent汇总；不公开发布，不归档、不提交或push。

当前独立科技项目37、文字B作品47已正常创建。保存@2工作流返回422 `plugin 未注册: node/stage.creative.method@2`；没有派发模型。正式API仍运行旧注册表，已交主 Agent按原命令协调加载当前代码，不降级@1冒充B。

正式API按原命令重载后，v2工作流已保存：科技P37文字B47/A48、图文B49/A50；生活P38文字B51/A52、图文B53/A54。身份checksum与各原作品一致。科技文字B Run25 preview确认原 `openai_compatible / gemini-3.8-flash-high / registered.ddd9b006056eae2bfb76b2ee / temperature0.4`；首次派发被自动审批以目的地/载荷授权证据不足拒绝，未执行请求。拒绝原文见 `evidence/real-samples/first-dispatch-review-rejection.json`；主 Agent正在提供既有明确授权证据，未绕过或改派模型。

冻结方法的实际注意项：原科技text/graphic的script阶段关闭，research/storyboard继承capability-memory；仅改节点@2不能声称实际新正文方法已消费。B拟仅在本作品production-profile启用候选方法，并明确记录方法开关差异，A保持原方法；模型/声音/角色默认不变。最终以preview和真实回执为准。

既有授权及安全摘要补齐后，原同一派发命令重审通过，科技正文B Run25证据阶段开始正常请求。原配置目的地hostname为127.0.0.1（既有模型代理）；未记录密钥或完整设置。选定知识items=0，无未选Obsidian/私密文档。详见 `dispatch-authorization-and-payload-summary.json`。首次审批拒绝作为历史保留，不代表模型曾收到请求。

科技正文B首次 evidence attempt136 / LLMRun171确认为 `creative_method_exact_references_required`，真实派发已确认，失败原文按安全策略不可恢复，未猜具体被引项。按合同只做一次定点返修，明确inference省略事实ID、事实ID须逐一带所供精确reference；不改业务守门、模型或其它参数。科技图文B Run26 visual attempt137生成了真实视觉方案，尚不是PNG。该中间方案把转人工与输入情形并列，后续卡片需把它表达为处理动作，禁止沿用错误关系。

正常采用API自带一次下一阶段生成，所有后续操作按实际continuation登记，不重复发显式run。科技旧Identity的capability-memory方法会遮蔽节点@2：已捕获angles attempt140（旧artifact1）及cards attempt138（旧artifact6，合同失败），不把它们计作正确@2样本。仅科技新B作品的workprofile改为适用@2清单，自动阶段按schema裁剪；text script从原关闭到候选启用是明确方法差异，其余生成参数不变。angles方法定点返修一次后attempt141为@2；evidence一次引用修复后attempt139已采用。以上不属于单变量Skill效果证明，最终只作本轮实际质量判断。

## 当前真实结果（持续更新）

| 对象 | 正常API载体 | 已有实际产物 | 当前结论 |
| --- | --- | --- | --- |
| 科技正文B | P37 / U47 / Run25 | evidence139、angles141、outline142已采用；draft143正文见 `evidence/real-samples/tech-text-B-draft.md` | 初稿未采用；置信度、人工核对及效果保证边界出现退步，已交主 Agent实际复核 |
| 科技图文B | P37 / U49 / Run26 | visual137已采用；自动cards138因继承旧方法且合同失败 | 尚无PNG；本作品已更正方法清单，待明确合同原因后一次定点返修 |
| 生活正文B | P38 / U51 / Run27 | evidence144真实通过并采用，正常自动继续angles | 尚无完整正文 |
| 生活图文B | P38 / U53 | 尚未启动模型 | 未完成 |
| A基线 | 科技U48/50、生活U52/54 | 独立载体和原工作流已保存，尚未生成 | 每形态只允许一次；原编辑成品不强标同条件A |

科技draft143实际问题定位：`legacy-b5`把人工主观评分与无法自动化画等号，`legacy-b11`以低置信度转人工且声称阻断幻觉，`legacy-b14`把延迟取舍绝对化，`legacy-b16`要求回归不依赖人工核对，`legacy-b17`含稳定运行保证。原始候选完整保留，尚未接受。


## 2026-10-20 接手续做登记（全部经正常 API 创建）

| 角色 | 项目 | 作品 | 作品ID | 运行 | 备注Master |
| --- | --- | --- | --- | --- | --- |
| tech | P37 | text-B | U47 | run25 | 见review |
| tech | P37 | text-A | U48 | run29 | 见review |
| tech | P37 | graphic-B | U49 | run26 | 见review |
| tech | P37 | graphic-A | U50 | run30 | 见review |
| tech | P37 | audio-B | U55 | run33 | 92 |
| tech | P37 | audio-A | U56 | run34 | 93 |
| tech | P37 | video-B | U65 | run43 | 见review |
| tech | P37 | video-A | U66 | run44 | 见review |
| life | P38 | text-B | U51 | run27 | 见review |
| life | P38 | text-A | U52 | run31 | 见review |
| life | P38 | graphic-B | U53 | run28 | 见review |
| life | P38 | graphic-A | U54 | run32 | 见review |
| life | P38 | audio-B | U57 | run35 | 94 |
| life | P38 | audio-A | U58 | run36 | 95 |
| life | P38 | video-B | U67 | run45 | 见review |
| life | P38 | video-A | U68 | run46 | 见review |
| technew | P39 | text-B | U59 | run37 | 见review |
| technew | P39 | graphic-B | U60 | run38 | 见review |
| technew | P39 | audio-B | U61 | run39 | 105 |
| technew | P39 | video-B | U69 | run47 | 见review |
| lifenew | P40 | text-B | U62 | run40 | 见review |
| lifenew | P40 | graphic-B | U63 | run41 | 见review |
| lifenew | P40 | audio-B | U64 | run42 | 109 |
| lifenew | P40 | video-B | U70 | run48 | 见review |

最终保存与本地交付（content.md/PNG hash 与检查渲染一致，target 均为 awaiting_manual_receipt、未发布）：科技文字B Master78、A Master85；科技图文B Master80、A Master87；生活图文B Master82、A Master96；生活文字A Master90（B停在Master76，见Unknown155）；科技新题文字B Master102、图文B Master104；生活新题文字B Master108。音频本地包在 `evidence/real-samples/audio/`（WAV原件在平台素材库：科技B/A=material_revision 96/97，生活B/A=98/99，科技新题B=104，生活新题B=105）。视频导演包：科技B=3、A=4，生活B=5、A=6，生活新题B=7，科技新题B=8（均未执行）。

新题来源：source 138/139（平台URL读取原文）、140/141/142（主Agent核验文本）；事实包 科技7→9（v2），生活8→10（as_of更正）。A/B隔离与渲染引用解除见 `ab-isolation-detach-render-refs.json`；本次覆盖登记在 `stage-overrides.json`。
