# 进度

## 第二版（全自动，2026-11-03「确认」）— 当前代码
第一版（模型起草、用户在页面冻结）已重启上线但未提交，按用户要求直接改成本版，不单独提交第一版。

### 改动
- `apps/api/app/fact_templates/topics.json`（新）：7 个题材模板。
- `apps/api/app/services/fact_templates.py`（新）：读模板、按选题和角色定位建议（只匹配资料内容，不匹配字段名）、项目选用；`for_model` 给模型的资料；`submit` 交事实——项目没选模板时记下模型选的，逐条打开来源核对，打不开 / 原文对不上退回不收，其余（不在常见权威网站 / 可能过期带标注）自动冻结成事实边界新一版并绑定，全退回不动；`current` 当前事实边界条目与标注；`stale_works` 稿子早于事实边界的作品。
- `apps/api/app/routers/project_evidence.py`：`GET/PUT /content-projects/{id}/fact-templates`（返回模板、已选、建议、当前事实边界、要重存的作品）。
- `apps/api/app/services/creative_mcp.py`、`mcp_settings.py`：MCP `get_fact_template`（只读）、`submit_facts`，组「事实边界（按题材模板自动核对）」；`tests/test_aco_creative_mcp.py` 白名单预期加这两个。
- `apps/api/app/services/video_chain.py`、`article_chain.py`：规则「写稿前先 submit_facts，事实改了重存稿子，事实只用事实边界，守模板红线」；资料包带 `fact_templates`；事实列表带上引语和专家观点（原来只取有 Fact 的条目）。
- `apps/web/src/product/project/FactTemplatePanel.tsx`（新）：模板选择（可不选）、只读当前事实边界、审稿事实行（可展开、含要重存提示）。
- `ProjectEvidenceTab.tsx`：去掉绑定已冻结 FactPack、新建证据包、克隆、草稿编辑 / 冻结、项目证据区；改为模板选择 + 只读当前事实边界 + 事实边界历史；项目来源、知识参考不动。
- `SystemAssetsKnowledgePage.tsx`：去掉新建证据包、证据包编辑器、把事实包绑到项目；事实包只留查看。`FactPackTools.tsx` 无引用，已删；`systemLibraryTypes.ts` 去掉不再用的 `FactBoundary` 类型。
- `ProductionWorkspace.tsx`：角色作品「选题与资料」显示模板选择；导演稿 / 文章审阅上方显示「本稿用到的事实」。

### 验证（数据库副本，抓网页用替身）
- 没选模板、也没带 templates：被拒（fact_template_missing）；带 templates [health] → 项目记下健康科普并收下。商品作品被拒。
- 交 5 条：坏链接→退回「来源打不开」，摘句不在页面→退回「原文对不上」；其余 3 条收下（知乎 + 2015 年那条带「来源不在常见权威网站」「来源可能过期」），自动冻结绑定；再交 1 条→新一版替换（1 条）；全退回→事实边界不变，提示换来源。
- 冻结的事实包状态 frozen 有校验和；「准备剪辑」的事实边界检查（creative_packages._check_evidence）通过；作品 94 不再有 evidence_missing，变为 stale_evidence（导演稿要重存），stale_works 列出作品 94。
- 视频资料包 facts、fact_templates 正常；规则里有 submit_facts。
- 页面（无头浏览器；fact-templates 请求由脚本从副本回答，其余只读走线上，线上写请求拦截，实际 0 次）：来源与事实边界页没有「选择已冻结 FactPack / 绑定为新版本 / 新建项目证据包 / 克隆 / 冻结」任何入口，显示「当前事实边界 第 1 版 · 3 条 · 1 条带标注」及来源、原文、标注；导演稿一步显示「本稿用到的事实：3 条已核对出处（1 条…）」，展开有来源和「稿子要重存」提示。
- 线上数据库：项目 49 只有用户在页面选的模板（health、parenting），没有事实边界；事实包仍到 #11。
- #1–#10 测试事实包只读核对：渠道版本证据、主稿证据、素材、知识集合、项目事实边界、子版本都没有引用。
- 前端类型检查通过；全量测试 2441 通过、28 跳过，只有已知的 5 个旧失败。

### 上线（2026-11-03 用户「上线」）
- 删前再核对 #1–#10：引用 0（渠道版本证据、主稿证据、素材、知识集合、项目事实边界、子版本）。
- 先备份 `backups/content_studio-before-drop-test-factpacks-20261103-212102.db`（git 忽略），再在一个事务里删 18 个条目和 10 个事实包；条目关联的事实和来源文档不动。
- 删后：事实包只剩 #11 海底光缆，项目 41 事实边界仍是第 1 版 · #11；外键检查、完整性检查通过；接口 /fact-packs、健康检查正常。

### 没做
- 后端手动接口（建事实包、加条目、冻结、克隆、项目绑定）照方案保留。
