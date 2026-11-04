# progress：fact-boundary-result-json

- 2026-11-04 方案写好，`openspec validate` 通过，等确认。
- 2026-11-04 用户确认，已实施：`fact_templates.py` `current()` 的 `frozen_at` 改为 ISO 字符串。
- 数据库副本验证（项目 49 / 作品 94）：经 MCP 分发调 `get_fact_template` 正常返回，`frozen_at`=2026-11-03T13:28:36.459446、9 条事实；调 `submit_facts`（一条打不开的来源）正常返回 kept 0、退回 1、当前事实边界第 2 版，不再报 422。
- 已有测试：test_aco_creative_mcp.py 74 passed；含 fact 的测试 18 passed。
- 2026-11-04 已重启 API 和 worker，健康检查 ok。
