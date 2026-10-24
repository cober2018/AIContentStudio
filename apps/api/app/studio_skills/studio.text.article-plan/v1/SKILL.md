---
key: studio.text.article-plan
version: 1
source_kind: studio_builtin
---

一次给出完整的写作方案，让用户只选一次。逐项阅读当前事实边界里提供的精确来源，不重新抓取或猜测来源。每个候选的 content 必须是 article.plan.v1：title 是暂定标题；angle 是这篇文章的论点；reader_stake 写读者为什么关心、为什么是现在；known 只列已提供的事实或推论，每项含 statement 与 kind（fact 或 inference），fact 才可带 fact_pack_item_id 和 as_of，inference 不得带引用；unknowns 写仍未知或不能说的部分，没有来源时写明「没有提供可引用的来源」；sections 是大纲，按 order 从 0 连续编号，每节含 id、heading、purpose、至少一条 points 和 open_questions，每节只承担一个目的。

不同候选要体现不同论点和结构，不只是换形容词。技术角色优先讨论工程问题、替代设计与 trade-off；生活角色从具体细节和普通人的感受进入，不强行升华。事实、推论与想象分开，不把热点或亲身经历编成事实，不创作未经提供的数字、日期或新闻。遵循 candidate_count；下游只使用用户选中的那个方案。用户选中方案只释放下游输入，不创建或冻结 FactPack，也不改变事实边界。
