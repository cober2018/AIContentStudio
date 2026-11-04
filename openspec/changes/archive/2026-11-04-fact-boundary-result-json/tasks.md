## 1. 修复
- [x] 1.1 `fact_templates.current()` 的 `frozen_at` 转 ISO 字符串

## 2. 验证（数据库副本）
- [x] 2.1 作品 94 所在项目 49：`current()`、`for_model()` 结果能 `json.dumps`
- [x] 2.2 经 MCP 分发调 `get_fact_template` 不再报 422
- [x] 2.3 跑 fact_templates 相关已有测试
