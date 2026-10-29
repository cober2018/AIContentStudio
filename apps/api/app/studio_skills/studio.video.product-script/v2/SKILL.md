---
key: studio.video.product-script
version: 2
source_kind: studio_builtin
---

只读取本商品SKU资料、任务目标、已接受的上游和事实边界，不要求内容角色身份。围绕具体买家在具体场景的一项需求，选择一个有依据的购买理由；把功能翻译成可感受的好处。用真实资料回答一个主要顾虑，说明不适合的情况，给一个清晰下一步。未知规格、价格、优惠、性能、用户评价和使用经历保持未知。AI情境仅用于说明，不作为真实效果或实测证据。

写之前先做三个选择，并在 summary 里写明选了什么、为什么：
1. 形态：读 references/forms.md，按商品资料、手头素材和渠道选一种形态。剧情、采访里的人物台词是演绎，不冒充真实用户；没有真实横向测试就不写对比测评和淘汰式开头。
2. 开头：读 references/hooks.md，开头按「停住、证明相关、接到商品」三拍写，选的机制必须能被现有素材兑现；没有可视张力的商品不用画面冲击类。多个候选时各用不同开头机制，便于比较。
3. 渠道：作品指定了交付渠道时读 references/channels.md 对应一节，调整语速、时长、互动和引导说法；没指定按通用写法。

写作要求：每一拍都让人想看下一拍；短句，像说出来的话，不用书面连接词；中间至少升一次级，结尾不落在说教或金句上；行动引导随口说，不喊口号。不使用绝对化用语、医疗或功效承诺、虚假紧迫和编造的销量、回购、测评数据。

中间阶段仅返回 {"schema":"video.script.v1","candidates":[{"id":"script-1","summary":"销售主线","content":{"title":"标题","beats":[{"id":"beat-0","order":0,"narration":"文案","visual":"有依据的画面计划","asset_requirements":[],"unknowns":[]}]},"references":[],"warnings":[]}]}。id 使用ASCII，order从0递增；引用只取供应目录中的精确项，候选数量等于candidate_count。资料不足写入unknowns，不编造素材编号。若合同是stage.master.proposal.v1，则每个候选仅返回title和beats；每段仅narration、visual与可选duration_ms，由服务分配编号。脚本不是已完成视频，人工接受精确版本后才供下游使用。
