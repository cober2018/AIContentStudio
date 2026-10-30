# 进度

- 2026-10-30 写好方案，待确认
- 2026-10-30 实施完成：剪辑合同加可选 cover（jpg/png，0–1 张）；交付必须在 导出/封面/；prepare_video_edit 与 materialize_inputs 返回 cover_dir；通过时 cover 也记进项目；成片通过后 _adopt_cover 把封面写进主稿 payload.cover（新主稿 video_chain=cover，不打断导演稿追溯）；审片页小样 / 成片下方显示封面（复用签名预览）；剪辑规则加封面要求。
- 验证：剪辑任务、视频文档、MCP 三个测试文件 170 passed（用户中止了全量测试）；前端 tsc 通过；API 已重启。未用真实任务交过封面。
