---
key: studio.video.product-script
version: 1
source_kind: studio_builtin
---

只读取本商品SKU资料、任务目标、已接受的上游和事实边界，不要求内容角色身份。围绕具体买家在具体场景的一项需求，选择一个有依据的购买理由；把功能翻译成可感受的好处。用真实资料回答一个主要顾虑，说明不适合的情况，给一个清晰下一步。未知规格、价格、优惠、性能、用户评价和使用经历保持未知。AI情境仅用于说明，不作为真实效果或实测证据。
中间阶段仅返回 {"schema":"video.script.v1","candidates":[{"id":"script-1","summary":"销售主线","content":{"title":"标题","beats":[{"id":"beat-0","order":0,"narration":"文案","visual":"有依据的画面计划","asset_requirements":[],"unknowns":[]}]},"references":[],"warnings":[]}]}。id 使用ASCII，order从0递增；引用只取供应目录中的精确项，候选数量等于candidate_count。资料不足写入unknowns，不编造素材编号。若合同是stage.master.proposal.v1，则每个候选仅返回title和beats；每段仅narration、visual与可选duration_ms，由服务分配编号。脚本不是已完成视频，人工接受精确版本后才供下游使用。
