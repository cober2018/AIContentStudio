# progress：film-60fps

- 2026-11-04 方案写好，等确认。
- 2026-11-04 用户确认，已实施：
  - `edit_handoff._postproduction`：导演稿已有 postproduction 就沿用其 fps，没有就 60；小样 / 成片和 AE 中间合成同一帧率。
  - `VideoShotMaterialPanel.tsx` 默认 fps 60；`ae_build.py` 默认 fps 60。
  - 达芬奇 skill：`delivery.md` 时间线帧率按导演稿 `postproduction.fps`（默认 60，旧作品沿用 30），30 帧实拍进 60 帧时间线不用补帧；`beat-and-speed.md` 慢放例子改为 60 帧时间线。
- 数据库副本验证：作品 94 最新导演稿开剪重算仍是 30（含 AE 合成 30），和已存的一致，不会存新主稿；去掉 postproduction 模拟新作品得 60（AE 合成 60），平台格式校验通过。网页类型检查通过。
- 全量后端测试：2441 passed、28 skipped，5 个失败和改动前完全相同（迁移 3 个、schema 生命周期 1 个、插件 1 个，都是已知旧问题，与帧率无关）。
- 2026-11-04 已重启 API 和 worker，健康检查 ok；新作品开剪起按 60 帧。
