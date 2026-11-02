# progress

- 2026-11-02 方案已写，等用户确认。
- 2026-11-02 已本地实施，未提交：edit_handoff._save 的 expected_context_hash 改为按当前设置现算（content_masters._context + _hash），不再用上一版存的 context_hash。
  - 正式库副本验证：作品 90 最新导演稿 196 存的上下文与当前不同（确认是原因）；经 video_chain._save（MCP 保存导演稿/选材的路径）保存成功，生成新版本。副本已删。
  - API/worker 已重启。
