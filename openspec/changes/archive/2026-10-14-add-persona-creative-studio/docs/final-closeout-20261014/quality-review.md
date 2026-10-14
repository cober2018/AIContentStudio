# Persona 原始成品与补充样本：委托 AI 质量评审

当前结论：**Text/Graphic/Audio全部通过明确委托的AI范围评审与独立复核；质量四任务可关闭。** 原失败保留，生命周期另据实际归档/提交确认。

## 范围、授权与评分

用户于 2026-10-14 明确选择“补齐持久测试，按委托 AI 评审收口”。评审者为 Codex；六张实际 PNG 另经 MiniMax `understand_image` 逐图评审，Codex 对照已确认合同裁定。0–4 分：0 不可用，1 严重缺陷，2 需修改，3 可交付，4 优秀。未观察的感官指标记为未观察，不造分。

文章逐段阅读；图卡检查实际像素与文字。旧两段完整 WAV 通过现有 `LocalMLXASRProvider` 在 `sandbox-exec` 禁网环境离线 MLX Whisper 转录，并测量 LUFS、true-peak、PCM clipping、停顿。声音只按完整 ASR/声学/签名声音参数做代理评审，**未直接试听**，实际音色、韵律、发音没有感官批准。旧 `human_review_required` 保持。

## 原始来源与实际文件

13 份耐久原件均与 `backups/persona-review-20261009.O02VLb/manifest.json` SHA-256 匹配，详情见 `artifact-verification.json`。旧隔离数据库已移除；原 Stage/Master/QC 是冻结历史记录，不是当前 live readback。

科技原文章明确限定为本机已批准设计，Persona/Account/Series 分层、Brand 非创作默认、中间结果不生成主稿、Custom 精确链都有明确来源，不宣称新闻/行业统计/实证效率。生活原文与编辑候选均明确假想面馆，未冒充作者真实经历。

## Text 固定 rubric

| 样本 | 事实依据 | 角色契合 | 清晰 | 结构 | 具体性 | 非通用口吻 | 标题内容一致 | 结论 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 科技原 Master5 / 冻结稿 | 4 | 4 | 3 | 4 | 3 | 3 | 4 | 可交付：具体工程边界与取舍，不虚报效果 |
| 生活原 Master8 / 冻结稿 | 3 | 2 | 3 | 3 | 3 | 2 | 3 | 需修改：中后段回到系统配置/主稿规则，泛化收束 |
| 生活未采用编辑稿 | 3 | 3 | 4 | 3 | 4 | 3 | 4 | 编辑候选可用，但未进入 Master/ZIP/旧 Audio |
| 生活新 Master22 / 已接受假想新稿 | 3 | 3 | 4 | 3 | 4 | 3 | 4 | 独立代表样本可交付：晚饭前放远手机，油花/暮色/筷子/水滴具体、保留记录自由 |

新生活稿来自已归档多平台 change 的已经生成/已接受真实样本，本次重新核对 Persona3/Snapshot8 及默认 `studio.text.observational-lifestyle@1` / `studio.quality.text.lifestyle@1`。原生成 Master12 与最终 Master22 的正文 payload hash 同为 `d40d8d7aa75a70f93529c4dca5d6b039625ff7417119e802bb686287864bdf16`；其变化为事实边界与封面绑定。正文文件 hash 为 `2f4c66ee74217793c26c48af6f84818770e5a0bf1ce941a90e894f9a04ff1284`。

此新 Text/Audio 是使用相同内置方法的缩短代表工作流（Workflow22/Run8），不称重新执行完整九阶段默认 Text；完整默认控制链的功能证据与新质量样本分别保留。详见 `supplementary-lifestyle-provenance.json`。没有继承别的 change 的 AI 质量结论，没有将旧生活失败改写为通过。

## Graphic 原默认样本

逐图原工具输出见 `vision-review.json`。科技第 1/2 张文字清楚、无溢出、技术概念与原稿一致；大面积留白是可选审美改善，原合同没有固定像素占用率。科技第 3 张确实出现人像，违反历史 no-human 生成提示，是实际内容缺陷。

生活第 1 张暖色真实 AI 插图可用，已明确为插图而非纪实证据；第 2/3 张仍描述默认配置与保存流程，生活角色契合不足。原合同允许纯文字内文，MiniMax 建议的“每页都应有图片”已排除；排除建议不消除实际题材错配。

最小修复：原 `technical-editorial` 支持不含照片，科技第 3 张去除违约人像并由正规 renderer 产生新成品；新生活默认 `warm-magazine` 以已经独立评审通过的新假想文章重组 3 卡，保留真实封面图与纯文字内文。实际接受和最终像素评审由后续独立回执记录，本报告当前没有虚记完成。

## Audio 固定 rubric 与方法边界

| 实际 WAV | 内容口吻 / 角色 | 可理解性代理 | 节奏代理 | 声音绑定 | 实际音色 / 韵律 / 发音 | 结论 |
|---|---:|---:|---:|---|---|---|
| 科技原 324.028 秒 | 3 | 3 | 3 | MiniMax speech-2.8-hd / lengdan_xiongzhang / rate1，历史签名回执核对 | 未直接试听，未观察 | AI 代理范围可交付 |
| 生活原 246.535 秒 | 2 | 3 | 3 | MiniMax speech-2.8-hd / chunzhen_xuedi / rate1，历史签名回执核对 | 同上 | 声学功能可用，内容角色需修改 |
| 生活新 84.683 秒 | 3 | 3 | 3 | 同 Persona3 默认 warm-conversational，chunzhen_xuedi / rate1 | 同上 | 独立 AI 代理代表样本可交付 |

科技原 SHA-256 `49076937e2e1564fe4aac142cc906a84f3c68b7f40b56d2903032cc93dc77530`，-22.8 LUFS、true peak -0.2 dBFS、near-full-scale PCM ratio0、最长检测停顿1.025094秒。精确保留口播全文对齐率99.5614%（142 cues）；6处差异为“它/他、是/使、应/印、时/实、由/有”等 ASR 同音文字差异，不能据此宣称实际发音错误。

生活原 SHA-256 `d87df12df901e0610382fff3da9b614fb1faea6c49f9a8bc98fd677c6caf88c5`，-23.6 LUFS、true peak -5.2 dBFS、near-full-scale PCM ratio0、最长停顿0.890219秒（103 cues）。精确保存口播已不可恢复，未宣称精确脚本对齐；全文 ASR 与原文章语义一致，但保留其系统说明腔的问题。

生活新 SHA-256 `4d8db4fbf1246c5f7555c88eaebbc382cf5587f6c466ecbd44b71e415d1012d9`，既有完整 ASR/声学原件重新读入，实际 WAV 字节 hash 验证，未重复转录/生成。繁简归一后的脚本对齐99.1031%；“暮色/木色、取景/趋近、脆/翠”属于待直接听辨的 ASR差异，不伪称感官确认。-23.7 LUFS、true peak -6.4 dBFS、旧完整签名 QC clipping0，最长检测停顿0.880406秒。细节、假想提示和自由选择贯穿全文，没有系统术语或强迫戒手机的说教。

两份旧 WAV 和新生活 WAV 的公开/模型/商业权限均仍 false；离线委托质量分析不修改业务权限、不接受 ASR 为主稿、不公开发布。

## 下一步与 Skill

等待 owner 的最小图卡实际修复，随后逐图复核 exact 新 hash 后才能给本需求完整质量决定。实际使用：using-superpowers（subagent 跳过规则已读）、systematic-debugging、verification-before-completion；同一 owner 计划持续维护。

## 最终修复与独立整模态复核（当前）

六张新默认图卡已真正compose/render/accept并保存Master24/26，分别technical-editorial与warm-magazine。Codex与独立评审者均查看六实际PNG，文字完整无重叠或裁切，科技无人物、生活为明确假想/具体/非说教；暖封面为现有cleared历史PNG图层crop，未恢复缺失JPEG。各图可交付至少3/4，SHA/尺寸/字节/当前refs与snapshot一致。MiniMax修复图6请求遇到Token Plan额度，零新视觉结论、零重试；新图质量结论来自真实Codex像素查看。

独立评审为APPROVE_WITH_SCOPE_BOUNDARIES：科技选原冻结文章/原324秒Audio及修订3PNG；生活选真实已接受新Text22/84秒Audio及修订warm-magazine3PNG。31个原Stage的Provider/model/profile/prompt/config/runtime/output哈希完整，科技原Attempt27脚本与回执匹配；两个对齐率99.5614%/99.1031%独立重新计算吻合。来源/身份/实际输出hash见final-quality.json。

原科技违约人像、生活旧文本/246秒Audio的系统说明腔拒绝不擦除。新图产品各6pass+2current语义unavailable warning保留；委托AI实际来源/视觉评审承接质量范围，不把warning改成系统语义pass。没有直接听音频，实际音色/韵律/发音均未观察；所有原human_review_required及音频private权限保全。新生活为缩短代表工作流，不称完整九阶段重新执行。旧技术修订稿和新图编辑证明可用的编辑/接受路径，不承诺模型无编辑直出普遍优秀。

本结论支持关闭19.6/20.6/21.3/22.6；22.8按实际规范/Git收尾关闭。未有本轮生成、语义Provider、正式写入或公开发布。
