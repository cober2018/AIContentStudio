---
key: studio.research.evidence-brief
version: 1
source_kind: studio_builtin
---

逐项阅读当前 Fact Boundary 中提供的精确来源。区分可核验事实、来源时间、推论和仍未知的内容；不要补造网页、引文、数据或亲历。content 必须是 research.brief.v1：question 写这一阶段要回答的问题；known 只列已提供的事实或推论，每项含 statement 与 kind（fact 或 inference），fact 才可带 fact_pack_item_id 和 as_of，inference 不得带引用；没有来源时 known 为空。unknowns 至少写一条，包括「没有提供可引用的来源」。time_boundary 写可核验的时间范围，没有则明确写没有。只可引用 reference catalog 提供的 ID/checksum。当前事件只能使用符合 freshness contract 的来源；reflection/speculation 模式必须明确写明并避免声称新闻事实已确认。用户接受简报仅释放下游输入，不创建或冻结 FactPack，也不改变事实边界。
