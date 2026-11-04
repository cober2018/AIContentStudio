# 成片默认每秒 60 帧

## Why
用户看了 MotionGit 和 AE 科技风模板的 60 帧效果，要求成片默认按每秒 60 帧出品。现在开剪时平台把小样、成片和 AE 中间合成都定成 30 帧（`edit_handoff.py`），60 帧模板放进来会被丢掉一半帧。

## What Changes
- 开剪（`prepare_video_edit`）时，没定过帧率的作品，小样、成片和 AE 中间合成都定为 60 帧。
- 已经开剪过、导演稿里已经记了帧率的作品（现有 80、83、84、85、90、92、93、94 都是 30）沿用原帧率，不重做已出的视频；作品 93 已定稿锁定，本来也不会再开剪。
- 网页「镜头素材」面板在导演稿还没有后期信息时，默认显示 60 帧。
- 代码动画搭建脚本 `ae_build.py` 默认帧率改 60，和 AE 中间合成的要求一致（平台交片时会核对帧率）。
- 达芬奇 skill：时间线帧率不再「按主要素材定」，改为按导演稿 `postproduction.fps`（默认 60）；30 帧实拍放进 60 帧时间线正常（每帧显示两次），不用补帧；慢放的例子改成 60 帧时间线（120 帧素材可直接慢放一半，60 帧素材慢放要补帧）。
- 现有 30 帧 AE 模板不改，放在 60 帧时间线里照常用。

## 不在本次范围
- 不重新渲染任何已有视频，不改任何作品的数据。

## Impact
- 代码：`app/services/edit_handoff.py`、`apps/web/src/product/VideoShotMaterialPanel.tsx`、`craft_skills/craft-ae/scripts/ae_build.py`、`craft_skills/craft-resolve/techniques/delivery.md`、`beat-and-speed.md`。
- 生效要重启 API（skill 文本每次实时读取）。
