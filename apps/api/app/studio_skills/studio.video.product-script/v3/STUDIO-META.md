---
classification: self_developed
adaptation_basis: method_reference
license: product_owned
vendored_code: none
upstream_revision: 1aab133dd75f
upstream_subfile: src/lib/script-engine/prompts.ts, hook-patterns.ts, templates/
validation: candidate_contract_pending
---

需求：product-category-skills。自有版本，只抽象 clipforge（AGPL-3.0）的方法并用平台自己的话重写，不复制其代码、提示词原文和示例文案。
来源：https://github.com/xixihhhh/clipforge/tree/1aab133dd75f
与@2的差异：先读品类指令；按指定风格技能或从品类可选风格里选并说明；固定或自选开头机制，并写 1–3 个备选开头（hook_versions）；参考结构只学结构不抄原话；剧情类风格输出人物表和每拍说话人。@2 的规则全部保留。
验证状态：待第三方模型实际使用后评审。
