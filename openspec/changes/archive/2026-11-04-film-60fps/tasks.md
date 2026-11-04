## 1. 实现
- [x] 1.1 `edit_handoff._postproduction`：导演稿已有 postproduction 就沿用其 fps，否则 60
- [x] 1.2 `VideoShotMaterialPanel.tsx` 默认 fps 60
- [x] 1.3 `ae_build.py` 默认 fps 60
- [x] 1.4 达芬奇 skill：`delivery.md` 帧率规则、`beat-and-speed.md` 慢放例子

## 2. 验证（数据库副本）
- [x] 2.1 没开剪过的作品走一遍开剪：导演稿记 60 帧
- [x] 2.2 作品 94 副本走开剪：仍是 30 帧
- [x] 2.3 相关已有测试
