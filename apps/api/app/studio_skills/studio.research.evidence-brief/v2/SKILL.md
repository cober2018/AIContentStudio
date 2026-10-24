---
key: studio.research.evidence-brief
version: 2
source_kind: studio_builtin
---

逐项阅读当前 Fact Boundary 中提供的精确来源。区分可核验事实、来源时间、推论和仍未知的内容；不要补造网页、引文、数据或亲历。content 必须是 research.brief.v1：question 写这一阶段要回答的问题；known 只列已提供的事实或推论，每项含 statement 与 kind（fact 或 inference），fact 才可带 fact_pack_item_id 和 as_of，inference 不得带引用；没有来源时 known 为空。unknowns 至少写一条，包括「没有提供可引用的来源」。time_boundary 写可核验的时间范围，没有则明确写没有。只可引用 reference catalog 提供的 ID/checksum。当前事件只能使用符合 freshness contract 的来源；reflection/speculation 模式必须明确写明并避免声称新闻事实已确认。用户接受简报仅释放下游输入，不创建或冻结 FactPack，也不改变事实边界。

先明确受众要回答的问题、资料的时间边界和真实缺口。known区分事实、来源观点与推断；只有冻结事实边界里的内容可绑定FactPackItem。给专业参考保留作者归属，风格只用于表达，不能拿风格示例的数字作证据。

本版本是仅供明确试用的新方法，不改变已保存角色或商品默认。输入按当前阶段使用已选且授权的专业参考、风格样本和事实边界；专业背景/旧观点不自动升格为已核实事实，风格参考作者身份与经历不属于当前角色。参考观察 polarity=avoid 表示应避免，未知或未试听内容保持未知。共享方法回答“怎样组织”，角色预设回答“怎样表达”，不能修改模型、路由、voice_id、rate或其它生成参数。输出只用当前请求的严格合同；每项建议说明具体内容依据，未知资料留缺口。技术检查、内容质量和用户认可分别记录，模型自评不是已接受。
