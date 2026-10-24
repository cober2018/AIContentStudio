---
key: studio.text.title-hook
version: 1
source_kind: studio_builtin
---

先读当前已经接受的正文，再生成与它实际结论一致的标题与开头候选。每个 content 必须是 creative.title-hook.v1，且只含 title、hook、reason：title 是标题，hook 是开头，reason 说明它为何与正文结论一致。标题不能承诺正文没有兑现的内容，不新增夸张数字、热点事实或虚构亲历。技术角色突出真实工程问题和权衡，生活角色用具体观察引出好奇心，避免必看、震惊、制造焦虑或强行人生道理。candidate_count 控制候选数量。用户明确选择后将精确候选传给 final Master 阶段，接受标题本身不静默改写任何 Master。
