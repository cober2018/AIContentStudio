# 进度

## 2026-11-09 实施
- 新增 `third_party_review_task` 表和迁移 `thirdparty0001`（接在 websearch0001 后）；本机数据库已升级，runtime.env 的 REQUIRED_SCHEMA_HEAD 改为 thirdparty0001。
- 新增 `app/services/third_party_review.py`：写作方式为第三方时挂起复核、领取、提交、校验。
- 文字、图文的事实与身份复核接入（`_semantic_review` 的 review 参数）；平台模式不变。
- 未提交的复核记为 incomplete，冻结被挡住。
- MCP 新增 `get_review_tasks`、`submit_review`（只对第三方写作开放）；写作说明和权限分组已更新。
- 测试：后端全量 2329 passed，5 failed（与改动前相同的 5 个：迁移 3 个、plugins、aco_schema_lifecycle 1 个）。MCP 白名单测试和图文定稿测试已按新流程更新。

## 未做 / 待定
- 3.3 用候选 15 实测：会在已定稿作品上新增检查记录，待你确认。
- 前端：检查面板还没有「等待第三方复核」的专门文案，目前显示为未完成。
- 第三方模型需要重新连接 MCP 才能看到两个新工具。
- 送审失败的提示仍是「渠道版本检查没过」，没有说明在等第三方复核。
