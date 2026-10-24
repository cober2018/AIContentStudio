# 实际发现与关键决策

## 2026-10-15 现状核对

- `routers/discovery.py`已有GET sources和仅修改暂停/模型权限的PATCH，没有POST登记或角色关联写入；`DiscoveryPanel.tsx`仅列来源与两个开关。
- `DiscoverySource`按owner+canonical_url唯一；`PersonaSourceSubscription`按persona+source唯一，已有enabled/manually_paused/profile_hash，适合复用。
- `register_candidate`会更新自动来源名称/类型/发现元数据和订阅画像；`research_sources`会禁用旧profile订阅。人工设置保护必须贯穿这些路径，仅加一个前端表单不够。
- `probe`已有RSS/Atom、发现网页Feed和受支持HTML/JSON读取；实际“新闻网站/博主主页”能否持续采集取决于公开入口。不能承诺任意平台可采集。
- 现有日批按当前profile订阅取证，且有正文、日期、独立评价、同类合并、来源分散和每日上限。手动来源直接进入同一筛选链。
- 当前未暴露codebase-memory-mcp代码图工具，按限定文件读取回退；未扫描整个代码库。

## 本提案决策

独立新增capability承载这次手动配置范围，避免把未批准开发混入前一43/45的日批验收。来源仍同库同任务，选择可为0/多个角色；设置角色集合即人工指定范围，自动发现不能静默更改。URL作为历史来源身份，另一URL通过添加与验证去重处理；不直接将有历史的来源改指另一站点。

## 实施发现

来源按canonical和adapter URL/验证别名共同识别；最终复用必须锁定后刷新，不能仅在HTTP前检查人工模式。源管理JSON协调和验证启动同样需要写锁，避免整块旧JSON覆盖新角色集合。owner锁统一源写入顺序，角色锁后复查容量。HTML仅有单篇结构化条目不能认定持续入口；RSS/JSON列表沿用原适配器。合并通知必须不受角色筛选影响，提供按source id解析目标的读取，避免目标角色不同而丢失反馈。

真实后台验收补充：SQLite DateTime从库读回可能无时区，租约条件若由ORM synchronize_session=evaluate在内存求值会TypeError；领取时让DB判断并显式刷新对象即可。隔离服务必须在worktree cwd启动，单设PYTHONPATH不能覆盖python -m的当前目录优先级；最初误用旧root导入已纠正，后续回执包含实际模块路径。
