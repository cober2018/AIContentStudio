# task_plan：fact-boundary-result-json

/// 1. ✅ `current()` 的 `frozen_at` 改为 `isoformat()`（无则 None）
/// 2. ✅ 数据库副本上调 `current()`、`for_model()`、MCP 分发 `get_fact_template`，确认能转 JSON
/// 3. ✅ 跑 fact_templates 相关已有测试
/// 4. 更新 progress.md、README.md；等「重启吧」「提交吧」
