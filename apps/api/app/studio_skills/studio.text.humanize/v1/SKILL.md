---
key: studio.text.humanize
version: 1
source_kind: studio_builtin
---

把当前已接受的正文当成精修基线，不重新发明一篇文章。改进笨重句子、重复表达和空泛过渡，保持已经写明的事实、数字、时间和未知项不变。语气只能改变表达，不能放宽事实、权利或审批规则。技术角色保留工程取舍；生活角色保留具体观察，不增加虚构经历。如果出现连续标题、以标题结尾，或标题一次跳过一级，补上对应段落并把层级改成逐级加深。不要在正文里用一级标题重复 title。

返回形状以冻结的 output contract 为准。当合同要求 title 和 body 时，每个候选只有这两个字段，body 是精修后的完整 Markdown，候选数量等于 candidate_count。不要返回 payload、引用、hash 或新的素材编号。服务会把 Markdown 转成新的 text.master.v2 提案。原 Master 不被改写；只有人工接受后才追加新修订。
