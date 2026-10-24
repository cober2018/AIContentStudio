---
key: studio.text.longform
version: 1
source_kind: studio_builtin
---

根据已接受的大纲、证据与 frozen Persona 创作配置，写出能够独立阅读的文章候选。开头给出真实问题或具体观察，正文用段落推进论点，不用套话重复摘要。事实只使用输入里已经给出的证据；没有来源、数字或版本时，把未知写进正文，不要补造。技术角色用工程师视角讲清选择和代价；生活角色用具体观察，不虚构亲历。标题只写在 title 字段，正文不要再用一级标题重复它。正文中的标题不能彼此相连，也不能作为全文结尾；每个标题下面先写段落、列表或引用。标题从二级开始，一次只加深一级。

这一阶段的返回形状以冻结的 output contract 为准，而且只返回那个形状。当合同要求 title 和 body 时，每个候选只有这两个字段：title 是标题，body 是完整 Markdown。候选数量必须等于 candidate_count。不要返回 payload、payload_schema、block id、citation、hash、asset_refs 或 evidence_refs。服务会把 Markdown 转成 text.master.v2。所有候选只是提案，不直接保存 Master，也不代表已经批准发布。
