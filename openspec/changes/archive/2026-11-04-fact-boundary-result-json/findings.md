# findings：fact-boundary-result-json

- 数据库副本上确认：项目 49 的 `current()` 结果里只有 `frozen_at`（datetime）转不了 JSON，其余字段都正常。
- `routers/fact_packs.py:65` 已用 `isoformat()`，照同一写法改。
- 网页接口 `routers/project_evidence.py:185` 也走 `current()`，FastAPI 本来就会把 datetime 转成字符串，所以网页一直正常；前端没用这个字段。
