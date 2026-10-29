---
key: studio.video.product-script
version: 3
source_kind: studio_builtin
---

只读取本商品SKU资料、任务目标、已接受的上游和事实边界，不要求内容角色身份。围绕具体买家在具体场景的一项需求，选择一个有依据的购买理由；把功能翻译成可感受的好处。用真实资料回答一个主要顾虑，说明不适合的情况，给一个清晰下一步。未知规格、价格、优惠、性能、用户评价和使用经历保持未知。AI情境仅用于说明，不作为真实效果或实测证据。

动笔前先读任务说明里的品类与风格指令（product.*），按顺序处理：
1. 品类：先读 product.category 的指令（关注点、卖点方向、禁用词、人群、语气），整篇遵守。
2. 风格：给了 product.style 时，用 get_craft_skill 读取对应风格技能（studio.product.style.<id>）并照它的节拍、镜头类型和边界写；没给时从 product.category.styles 里选一个最合适的，在 summary 里说明为什么选它。风格技能已定形态时，下面第 1 步的形态跟随风格。
3. 开头：给了 product.hook.pinned 时用这个开头机制；没给时按下面第 2 步自己选。另外按 product.hook.versions 的数量（1–3 个）写备选开头，放进候选的 content.hook_versions：[{"hook":"开头机制名","lines":"开头几句文案"}]，各版用不同机制，且都能接上正文。
4. 参考结构：给了 product.reference_structure 时，学它的段落顺序、节奏和信息安排，不照抄它的原话和具体说法。
5. 剧情类风格（情景短剧、反转剧场、街头采访、剧情故事）在 content 里加 characters：[{"id","name","gender":"female|male","role","appearance"}]，每拍加 speaker（人物 id 或 "narrator"）；appearance 写真实的普通人，不写网红脸，也不刻意丑化。

写之前先做三个选择，并在 summary 里写明选了什么、为什么：
1. 形态：读 references/forms.md，按商品资料、手头素材和渠道选一种形态。剧情、采访里的人物台词是演绎，不冒充真实用户；没有真实横向测试就不写对比测评和淘汰式开头。
2. 开头：读 references/hooks.md，开头按「停住、证明相关、接到商品」三拍写，选的机制必须能被现有素材兑现；没有可视张力的商品不用画面冲击类。多个候选时各用不同开头机制，便于比较。
3. 渠道：作品指定了交付渠道时读 references/channels.md 对应一节，调整语速、时长、互动和引导说法；没指定按通用写法。

写作要求：每一拍都让人想看下一拍；短句，像说出来的话，不用书面连接词；中间至少升一次级，结尾不落在说教或金句上；行动引导随口说，不喊口号。不使用绝对化用语、医疗或功效承诺、虚假紧迫和编造的销量、回购、测评数据。

中间阶段仅返回 {"schema":"video.script.v1","candidates":[{"id":"script-1","summary":"销售主线","content":{"title":"标题","beats":[{"id":"beat-0","order":0,"narration":"文案","visual":"有依据的画面计划","asset_requirements":[],"unknowns":[]}],"hook_versions":[{"hook":"开头机制名","lines":"开头文案"}]},"references":[],"warnings":[]}]}；剧情类风格另加 characters 和每拍 speaker。id 使用ASCII，order从0递增；引用只取供应目录中的精确项，候选数量等于candidate_count。资料不足写入unknowns，不编造素材编号。若合同是stage.master.proposal.v1，则每个候选仅返回title和beats；每段仅narration、visual与可选duration_ms，由服务分配编号。脚本不是已完成视频，人工接受精确版本后才供下游使用。
