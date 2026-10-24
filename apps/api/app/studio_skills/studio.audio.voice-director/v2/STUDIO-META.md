---
classification: self_developed
adaptation_basis: method_reference
license: product_owned
vendored_code: none
upstream_revision: 8d08b216105bd7c7057c84c97cd637cec44db609
upstream_subfile: skills/builtin/audio-mix/SKILL.md
validation: candidate_contract_pending
---

需求：improve-persona-content-methods。自有新版本，只抽象所引方法，不安装或复制上游实现。
来源：https://github.com/ZJU-REAL/Easel/blob/8d08b216105bd7c7057c84c97cd637cec44db609/skills/builtin/audio-mix/SKILL.md
输入、输出、阶段和可调字段见同目录 STUDIO-CONTRACT.json。与@1的差异：核对请求中的原voice/rate约束后给停顿、句长、重音与专名方向；rate必须沿用冻结原值。文本层面的节奏建议不能当作已实现的TTS参数。旁白为主，配乐可不用；如需配乐，在pause_policy说明独立轨、避让旁白和依据，不能添加原工具不支持的参数。机器转写或测量不等于已试听。
验证状态：待开发自检与独立成品评审；未获用户角色风格采纳，不改变旧默认或商品绑定。
