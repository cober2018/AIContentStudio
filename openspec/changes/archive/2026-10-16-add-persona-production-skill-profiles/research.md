# 第三方创作能力核查（2026-10-16）

状态：源文件研究完成，未安装、未执行第三方Skill，未完成本机AE/Resolve适配验证。下表的“优先”指进入小样对比，不代表已成为产品默认。

核查方式：读取指定仓库README、LICENSE及相关SKILL.md/引用文档，以GitHub tree SHA固定本轮来源。只做任务相关阅读，不声称审计了整个代码库。无URL的vox-director、Paper-Cut、cut-video、aftr按下表仓库匹配；若用户原指不同同名项目，应按确切来源复核。

## 逐项结论

| 项目/固定快照 | 本轮读取的许可 | 价值与优先级 | 接入调整 |
|---|---|---|---|
| [imraywang/wewrite](https://github.com/imraywang/wewrite/tree/de69e06c2596a0f3e2b0eb3d6229f201d7559584) `de69e06c2596` | MIT | 优先候选：公众号写作/审阅/排版；learn 用于范文和改稿偏好 | CLI状态目录与公众号动作另适配；不让渠道风格覆盖角色，不自动发布 |
| [lijigang/ljg-skills](https://github.com/lijigang/ljg-skills/tree/2c82b3d06a2d84405ec971d21c64f71b6a8dd900) `2c82b3d06a2d` | MIT | 优先候选：read、explain、analogy、mechanism；按需card | 主分支偏org-mode，需选Markdown输出；无需26个全装 |
| [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills/tree/322346ded8129436b3f64707789a73e732ae24d9) `322346ded812` | MIT | 优先候选：hv-analysis深研、khazix-writer结构与表达 | writer明确绑定卡兹克身份，必须去除；深研PDF/篇幅与安装约定不直接照搬 |
| [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930) `f4518a8eab97` | MIT | 优先候选：中文精修，最后按需使用 | 不能改变事实/术语/引用或编造第一人称经历；不是保证绕过检测 |
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft/tree/13c74a707786872a18e3317e48c5c94011027620) `13c74a707786` | Apache-2.0 | 优先候选：少量镜头语法、运镜、声音和卡点方法 | Remotion实现改为AE适配，需重做渲染对照；捆绑媒体逐项核实 |
| [Vincentwei1021/video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft/tree/a7c29edfb2404612dde6a5a1c8aa94232e85625b) `a7c29edfb240` | PolyForm Noncommercial 1.0.0 + 作者声明 | 口播讲解匹配度高，待商业授权候选 | 当前LICENSE明确商业使用需预先授权；不直接纳入运营生产 |
| [cclank/lanshu-create-ai-presenter-video](https://github.com/cclank/lanshu-create-ai-presenter-video/tree/762d3ee42623b75a4ec63ad6aa61ace69d78ce6e) `762d3ee42623` | MIT | 优先候选：无数字人的styled explainer、MiniMax配音和词级对齐 | 现成渲染是HyperFrames；图形演绎需适配AE。数字人另依赖可用生成/口型供应商 |
| [Agentchengfeng/chengfeng-videocut-skills](https://github.com/Agentchengfeng/chengfeng-videocut-skills/tree/a33b43e08c34fa8beeb5e78498e852f4e80975a5) `a33b43e08c34` | Apache-2.0 | 优先候选：中文修字、删词账本、字幕语义与对齐方法 | 现版强绑定其Runtime、Studio和云ASR；只抽选方法适配，不能声称原插件直接跑Resolve |
| [louisedesadeleer/cut-video](https://github.com/louisedesadeleer/cut-video/tree/a5a87a64f381c62b8972a92132fb48015b0e50ff) `a5a87a64f381` | MIT | 备选：静音/语气词的候选剪点与停顿保留 | 默认偏激进、英文口头词、MFA依赖；不直接当科技口播默认 |
| [Alisa0808/vox-director](https://github.com/Alisa0808/vox-director/tree/6a85a7c341610442a6a5b1885e6e0217ab82a11f) `6a85a7c34161` | MIT | 局部风格候选：拼贴叙事与图先行 | 默认Atlas Cloud+图生视频；不照搬自动供应商调用，拼贴不是科技角色全片基调 |
| [aijiduonadegou/paper-cut](https://github.com/aijiduonadegou/paper-cut/tree/4b77204bcd609156cd10037bf82d615ccc100abd) `4b77204bcd60` | MIT | 局部风格候选：批准静帧后拆层、局部动效 | 现成HyperFrames实现需AE适配；只在解释内容需要时用 |
| [Arman-Luthra/aftr](https://github.com/Arman-Luthra/aftr/tree/628397d700d6282fe2be4d42f4a388392250947a) `628397d700d6` | MIT | 参考：文字动效预设、spec→render→review→revise循环 | 它也是一套AE桥接运行时，不是完整剪辑风格教材；不替换现有AE MCP |
| [op7418/guizang-social-card-skill](https://github.com/op7418/guizang-social-card-skill/tree/cf4b810fac1c73fb65a2bb31d8c9278d82cbc4c5) `cf4b810fac1c` | AGPL-3.0 | 储备：Editorial生活图文；Swiss也可能适合科技 | 不是单一生活风格；复制/修改分发要按许可处理，图库素材另核实 |
| [op7418/guizang-product-video-skill](https://github.com/op7418/guizang-product-video-skill/tree/18842e0f49a9eb2b8c00cc065ec37b314e235aaa) `18842e0f49a9` | AGPL-3.0 | 储备：产品宣传叙事和设计语言 | 本期不引入完整代码视频引擎；许可与商业许可文件另见上游 |
| [op7418/guizang-yingzao-skill](https://github.com/op7418/guizang-yingzao-skill/tree/58c9b8738858bae0ab2c669d0a0fead90d4a80c9) `58c9b8738858` | 未发现LICENSE | 储备：建筑/文化场所的艺术指导海报 | 当前树无LICENSE，不能据GitHub公开就直接复制进产品；也不是通用风格提取器 |
| [dontbesilent2025/dbskill](https://github.com/dontbesilent2025/dbskill/tree/3d7d41da1ed7c6b88805b8dca90f376069419c8d) `3d7d41da1ed7` | CC BY-NC 4.0 | 内容价值、标题开头、脚本和传播方法可研究 | 偏商业内容诊断；非商业许可，暂不纳入运营工作流，更不全局贯穿所有阶段 |
| [hypit-ai/hypit](https://github.com/hypit-ai/hypit/tree/dc2b7a8f31b1ef1443a79ca448548d69e3ceb6a0) `dc2b7a8f31b1` | 修改版Apache-2.0 + Hypit条款 | 优先试验：视频参考分析与证据采集 | 内部自用在其明示范围；多租户/对外托管/商业再分发有额外条件；不替换剪辑执行链 |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes/tree/0e9f380c2e2295db4b88945a77cfa81001ac5c27) `0e9f380c2e22` | Apache-2.0 | 储备：HTML/CSS视频引擎与音频/动效方法 | 本期无需作为生产必需依赖；借鉴方法与采用运行时分开 |
| [ayushozha/AdobePremiereProMCP](https://github.com/ayushozha/AdobePremiereProMCP/tree/36574e4920d56ae71efeb055ba8e2af827b2106c) `36574e4920d5` | MIT | 参考：dialogue-cut和look-effects等任务方法 | 名字对应的项目；只迁移剪辑意图，不装Premiere或逐工具映射 |
| [designbyfatur/PremiereMCP](https://github.com/designbyfatur/PremiereMCP/tree/cce19c2e631015f76e209977472316e56e0faf76) `cce19c2e6310` | MIT | 仅用于核对1027工具说法 | 与上述精确名称不是同一仓库；工具数量不代表方法质量或Resolve可用性 |

Remotion 是 React 编程视频引擎，官方文档见 https://www.remotion.dev/docs/ 。它可实现画面，但不能直接替代专业创作方法。用户已选 AE/Resolve，本期不增加 Remotion 运行依赖。

## Hypit能接在哪里

已读 `skills/hypit/SKILL.md`、`references/creation/reference-video.md`、`brief.md`。分析方法要求完整理解参考片，再把叙事、镜头、字幕、图形、声音行为关联到时间和语义。`media probe/cut/frames/tile/tiles/boundaries` 与 `transcribe` 是证据工具；`ANALYSIS.md` 和 `TIMELINE.md` 是Agent整理的理解，不是自动识别准确率已验证的模型输出接口。

建议只在“角色建立→视频参考提炼”接入可选分析适配，保留原片、转录、关键帧、时间码和未知项，转成平台已有版本化风格资产。其SVML/SVS/SVRUN完整制作运行时不进入本期主链。源文档的算法与工具组合支持细致分析，不能证明“完美复刻”；源实现、隐藏图层、原工程与声音混音参数无法仅凭成片完整恢复。提炼风格也不等于训练模型权重。

[具体参考分析文档](https://github.com/hypit-ai/hypit/blob/main/skills/hypit/references/creation/reference-video.md) · [Hypit许可原文](https://github.com/hypit-ai/hypit/blob/main/LICENSE)

## shotcraft、talkcraft与aftr的区别

- shotcraft以产品实拍页面/截图为视觉基础，包含镜头运动、卡点、声音设计、参考实现和QA。文件数/介绍有不同口径：本快照 `references/shots` 有125个Markdown，SKILL正文说124，仓库介绍提152；不可把这些都称为已验收可用镜头。逐项选卡才是可执行单位。
- talkcraft当前 `references/cards` 实际108个Markdown，SKILL也写108。以成品配音、词级时标、语义分镜和图层矩阵组织讲解，比产品宣传模板更接近科技解释类目标，但商业授权尚未解决。其默认持续运动/Apple范式不应自动覆盖用户录屏可读性。
- aftr包含4类文本动画预设和若干VFX指令，也有渲染后复核循环；这是可参考的动效与工程方法，不是完整的剪辑审美标准。真实AE路径需要AE内CEP面板；headless simulator是模拟器，不能代替AE实际出片验收。
- 移植时保留“为什么这样动、什么时候动、与哪句话对应”，在AE重建图层/关键帧/缓动，重新渲染核对。已有MCP可以运行必要脚本，不需要用户写React，也不能保证所有Remotion功能无损转换。

## 现成资源与用户目标的冲突

1. khazix-writer在开头明确要求以原作者身份写作；应提取通用写作步骤并换成已确认的科技角色，不能沿用他的身份和个人经历。
2. WeWrite learn明确区分本人/第三方范文，用于结构节奏而非挪用观点经历；适合复用为公众号参考和改稿反馈。其全局用户目录须适配成角色范围，不能让两个角色共享污染。
3. lanshu的styled explainer可独立于数字人使用，已有MiniMax路径与逐字演绎设计；但外部录音路径会估计时间，精度等级不能伪装为真实强制对齐。接入现有MiniMax渠道前仍需验证实际时间戳格式。
4. chengfeng-cut现版明确只产出删词账本，不切媒体；强绑定Runtime/Studio与云ASR。可以复用中文语义/词ID方法，但要明确这是自有Resolve适配版。
5. vox-director默认Atlas Cloud生成活海报，Paper-Cut默认HyperFrames拆层动画；两者均不是可直接插入AE的成品插件。
6. shotcraft声音文档明确有曲目无法逐曲反查、SFX来源待考；代码Apache许可不代表每段捆绑音频可无条件公开使用。首批音乐必须逐曲登记，不能一键整包导入。
7. 用户《文案到成片流水线》作为讨论参考：保留音频先行、声音/节奏/校色/后期分工；里面的固定镜头秒数、响度值、ASR误差和“素材库零版权风险”不作为已核实的平台硬标准。

## 第一轮建议试验

- 研究/文字：hv-analysis的横纵证据结构、ljg-read/explain，去身份的khazix-writer，Humanizer按需最后精修，WeWrite仅公众号阶段。
- 讲解与视频：lanshu的脚本/配音对齐方法、chengfeng中文删词/字幕方法、shotcraft三类镜头；Hypit独立分析参考。
- 同一主题比较关闭附加Skill/单Skill/组合，用事实保真、理解效果、角色一致性、返工时间判断保留项。
- 先得出科技角色暂定风格卡，再换一个新主题验证可迁移；由用户确认的结果才提升为默认。生活类Guizang和数字人放后续；talkcraft/dbskill不作为当前商业生产依赖。

## 补充：AE与Resolve原生方法候选（2026-10-16）

用户补充三个仓库，并进一步明确：Remotion/HyperFrames的创作方法应保留，但实际执行需要适配到AE/Resolve。仍为同一需求的选型补充，不是安装或apply授权。

| 固定快照 | 实际组成与价值 | 复用方式 |
|---|---|---|
| [yumehiko/ae-agent-skills](https://github.com/yumehiko/ae-agent-skills/tree/760cc5b135a0a5f5e5f3e7427ec51af35488d25e) | MIT；两个Skill：aftereffects-declarative、aftereffects-cli；另含ae-cli、CEP桥、scene schema和JSX实现 | 优先参考可重复场景装配、图层稳定ID、先验证后应用、局部修订与截图复核；适配到现有AE MCP，不整套另装桥 |
| [odaiouattara0022-del/davinci-resolve-skill](https://github.com/odaiouattara0022-del/davinci-resolve-skill/tree/71d243773caa34502666c4d53e0b0b050f069918) | MIT；一个入口Skill、四份API/工作流/调色/Fusion参考、连接与静音剪辑两个脚本 | 作为Resolve组合操作参考：素材导入→源片段装配→时间线回读；调色版本、字幕与渲染可选组合；按当前API适配 |
| [ChaiWithJai/davinci-resolve-claude-skills](https://github.com/ChaiWithJai/davinci-resolve-claude-skills/tree/cf7e4275f10d6d7b709a5c50155769715c8d14f0) | MIT；11个任务Skill，含录屏剪辑、人声清理、webcam调色、标题、导出、social-editor等 | 优先抽取语义剪辑、B-roll证据匹配、声音先行、分层工程交接、画面/声音QA；不引入Computer Use训练流程或固定广告风格 |

### 三者的互补关系

- **yumehiko提供场景装配办法**：新场景用声明式JSON描述素材/图层/关键帧/文本/布局，同ID再应用更新；已有人工场景用局部操作，避免整体重建。源文件明确区分merge、replace-managed、clear-all。我们仅优先保留受管图层更新与局部修改；全量清空不是默认组合动作。
- **odaiouattara提供脚本组合范例**：有真实ffmpeg静音检测→讲话片段→新Resolve时间线的代码，比单纯列API更进一步；但静音不等于无意义内容，仍需语义审阅和正常停顿。
- **ChaiWithJai提供制作判断方法**：先组织完整意思、给每次剪切原因、让B-roll证明口播、选择实际可用声音、保留可编辑音画分轨。这些方法最接近科技录屏与解释类作品；强绑定工作坊促销/竖屏/人物常驻的条款要换成用户角色标准。

### 已发现的直接搬用问题

1. yumehiko原Skill调用自己的ae-cli和安装目录，不能仅把命令名替换成MCP名称。需要映射参数与图层所有权、关键帧合并/替换语义、项目定位、回读。它主要解决实现与重复执行，不提供成熟科技视觉风格本身。若复制其桥接组件，还涉及THIRD_PARTY_NOTICES中的Adobe CEP许可；本方案不复制该桥。
2. odaiouattara的静音脚本按名称子串找到首个素材；我们的执行包已具有精确素材引用，应沿用精确引用。其AppendToTimeline只要返回非空就按整个batch计成功，存在部分返回被高估的可能；适配必须比对返回项目及最终时间线。参数应来自本次任务，而不是照搬固定噪声阈值。
3. odaiouattara示例使用TimelineItem.SetLUT；本会话Resolve 21.1工具提供的当前API索引在Graph上公开SetLUT。需按实际版本核对调用对象，不能以旧示例证明当前运行可用。
4. ChaiWithJai的`cut-screen-recording/scripts/auto_silence_cut.py`只遍历音轨片段位置并检查大于2秒的片段间隙，不分析音频波形，不检测片段内部静音，更不会自动删除。其Skill也明确它是保守辅助报告。
5. ChaiWithJai的音频/调色Skill包含大量GUI教程及“一律低频处理”“固定闪避幅度”等写法，不能作为所有TTS/真人录音的统一参数；先诊断实际源，再选必要处理并试听比较。其PDF页码引用是上游提供的线索，本轮未逐页复核官方PDF，不据此声称所有技术细节已验证。
6. 当前Resolve API索引可查到音量、Dialogue Leveler、NormalizeAudioLevel与Fairlight预设应用；本轮针对Ducker/EQ的检索未取得同等直接控制接口。此结论是文档检索范围，不是证明所有间接路径不存在。适配要区分“原生可脚本化”“已有已验证预设”“仍未解决”，不能把GUI步骤标成MCP已完成。

### 推荐固化的组合（归入原22项，不扩任务范围）

| 组合能力 | 输入 | 连续操作与验收 | 归属 |
|---|---|---|---|
| AE场景装配 | 素材、文字、角色视觉参数、镜头时段 | 定位工程→受管图层→排版/关键帧→表达式检查→预览→渲染 | 原4.3 |
| AE局部修订 | 精确图层/需修改参数 | 读取现状→只改目标→回读与参考帧比对 | 原4.3 |
| Resolve语义粗剪 | 精确源素材、逐词/句意范围、编辑决定 | 装配分轨→检查真实源范围/时间线起点→同步核验 | 原4.2 |
| Resolve人声与配乐 | 声音诊断、场景音乐方案 | 按需修复/调平→可选配乐淡化/闪避→成片测量与试听 | 原4.4、5.3 |
| Resolve镜头匹配 | 素材色彩信息、参考画面 | 基础校正→镜头匹配→角色风格→前后对照，保留版本 | 原4.4 |
| Resolve交付复核 | 主时间线、AE回片、输出要求 | 检查回片/分轨→导出→实际文件与可编辑工程核验 | 原4.4、6.2–6.4 |

这里是候选组合设计，不是已实现的新Skills。最小做法是在既有video-production-handoff下引用选定方法，稳定操作再保存为参数化可复用工具，不先建设完整通用scene编译器。

### 本机只读核对与证据边界

- 当前工具目录已经包含AE `ae_toolSearch`、`ae_toolSave`、`ae_toolUse`、`ae_skillUse`，说明已有保存/重放组合脚本和prompt-skill的接口设计；无需预先新建第二套AE工具库。本轮只查看描述，没有保存或执行组合工具。
- 请求读取`ae-execution-guide`返回`Mcp-Session-Id is unknown`；因此没有取得本轮AE执行指南或运行证据，不判定AE整体不可用，也不宣称适配完成。
- Resolve侧调用了get_whats_new和search_scripting_api，只读接口文档，没有修改工程。文档版本21.1；上游主要针对18+/20，需要小样实测后才标为可用。
- 外部源缓存仍位于`/tmp/aics-skill-research-20261016/`；读取README、LICENSE、两份AE Skill、Resolve入口、Chai的重点后期Skill，以及scene schema/关键实现、静音脚本、调色和交接参考。没有运行下载的代码、安装插件或修改软件设置。

## 已核对的平台接点

- `docs/CREATIVE_EXECUTION_MCP.md`：find_capabilities/use_capability只返回方法内容与记录使用，不安装或执行Skill。
- `openspec/specs/persona-creative-configuration/spec.md`：四模态配置、Persona根、版本冻结与whole-profile替换已有。
- `openspec/specs/studio-creative-skill-pack/spec.md`：内置Skill、方法库、Installed Agent Skills是不同库存；已有来源与许可证记录要求。
- 原网页视频change归档保持；新需求独立提案。既有工作树相邻修改不属于本轮。

## 证据与未验证事项

下附本轮实际缓存文件清单；缓存位于 `/tmp/aics-skill-research-20261016/`，可能被系统清理，持久证据采用上表固定commit URL。只读源文档不等于运行验收。未运行Hypit分析、本机第三方Skill、AE移植镜头、MiniMax新增路径或音乐混音；未安装依赖、导入音乐或改变默认Persona。

- **imraywang/wewrite**：`LICENSE`、`README.md`、`skills/wewrite-learn/SKILL.md`、`skills/wewrite-style/SKILL.md`
- **lijigang/ljg-skills**：`LICENSE`、`README.md`、`skills/ljg-card/SKILL.md`、`skills/ljg-explain/SKILL.md`、`skills/ljg-read/SKILL.md`
- **KKKKhazix/khazix-skills**：`LICENSE`、`README.md`、`hv-analysis/SKILL.md`、`khazix-writer/SKILL.md`
- **op7418/Humanizer-zh**：`LICENSE`、`README.md`、`SKILL.md`
- **Vincentwei1021/video-shotcraft**：`LICENSE`、`README.md`、`SKILL.md`、`references/music-beat-sync.md`、`references/sound-design.md`
- **Vincentwei1021/video-talkcraft**：`LICENSE`、`README.md`、`SKILL.md`、`references/shotbook-example.md`
- **cclank/lanshu-create-ai-presenter-video**：`LICENSE`、`README.md`、`README.zh-CN.md`、`SKILL.md`、`references/styled-explainer.md`
- **Agentchengfeng/chengfeng-videocut-skills**：`LICENSE`、`README.md`、`plugins/chengfeng-videocut/skills/chengfeng-cut/SKILL.md`、`plugins/chengfeng-videocut/skills/chengfeng-subtitle/SKILL.md`
- **louisedesadeleer/cut-video**：`LICENSE`、`README.md`、`SKILL.md`
- **Alisa0808/vox-director**：`LICENSE`、`README.md`、`SKILL.md`
- **aijiduonadegou/paper-cut**：`LICENSE`、`README.md`、`SKILL.md`
- **Arman-Luthra/aftr**：`LICENSE`、`README.md`、`presets/text-presets.json`
- **op7418/guizang-social-card-skill**：`LICENSE`、`README.md`
- **op7418/guizang-product-video-skill**：`LICENSE`、`README.md`
- **op7418/guizang-yingzao-skill**：`README.md`
- **dontbesilent2025/dbskill**：`LICENSE`、`README.md`
- **hypit-ai/hypit**：`LICENSE`、`README.md`、`README.zh-CN.md`、`skills/hypit/SKILL.md`、`skills/hypit/references/creation/brief.md`、`skills/hypit/references/creation/reference-video.md`
- **heygen-com/hyperframes**：`.agents/skills/motion-doctrine/SKILL.md`、`LICENSE`、`README.md`、`skills/hyperframes-audio/SKILL.md`
- **ayushozha/AdobePremiereProMCP**：`LICENSE`、`README.md`、`skills/premiere-dialogue-cut/SKILL.md`、`skills/premiere-look-effects/SKILL.md`
- **designbyfatur/PremiereMCP**：`LICENSE`、`README.md`
