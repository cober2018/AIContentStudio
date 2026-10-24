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
输入、输出、阶段和可调字段见同目录 STUDIO-CONTRACT.json。与@1的差异：按已接受镜头、素材索引与声音方向交接。旁白、配乐和音效独立轨，必要配乐须为旁白留空间；没有配乐也可以成立。Resolve主剪，AE只负责必要包装；平台只准备合同，经CLI/MCP的执行器返回真实工程与成片。缺人工网页素材时保留待回传，不运行上游安装/网关/发布脚本。返修定位镜头或时间，说明实际重跑范围，保留独立分支和旧版本。
验证状态：待开发自检与独立成品评审；未获用户角色风格采纳，不改变旧默认或商品绑定。
