# 进度
- 2026-11-07 写规范，等「确认」。
- 2026-11-07 已确认并实现：video_chain._require_four_three 在成片通过前检查（清单有 cover_43 且没交 → 409 video_chain_cover_43_missing「抖音 4:3 横封面还没交，交了才能通过」）；RULES、prepare_edit files、prepare_video_edit 说明写成必交。
- 验证（库副本）：旧任务 58 通过不受影响；给它清单加 cover_43 后未交被拒；交了 4:3 后通过。全量测试 2445 通过、5 个原有失败；ruff 通过。
- 2026-11-07 已重启，健康检查正常。
- 2026-11-08 已归档提交（本地 main，未推送）。
