---
classification: self_developed
adaptation_basis: method_reference
license: product_owned
vendored_code: none
upstream_revision: 8d08b216105bd7c7057c84c97cd637cec44db609
upstream_subfile: skills/builtin/short-drama/SKILL.md
validation: candidate_contract_pending
---

需求：improve-persona-content-methods。自有新版本，只抽象所引方法，不安装或复制上游实现。
来源：https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/short-drama/SKILL.md
输入、输出、阶段和可调字段见同目录 STUDIO-CONTRACT.json。与@1的差异：每镜有明确purpose、内容依据、真实可用时长与连续性。v2中用reference_index将主体/场景/道具映射到精确已给MaterialRevision，shots.reference_keys只能引用此索引；缺素材不用虚构编号。continuity说明前后动作/视线/空间衔接，sound分别写旁白、环境声、可选配乐及未检查项。Grok/Gemini仅准备人工网页任务，Resolve主剪，AE按需包装；逐镜回收与返修，不把镜头计划当成片。旧v1只用既有字段说明这些要求。
验证状态：待开发自检与独立成品评审；未获用户角色风格采纳，不改变旧默认或商品绑定。
