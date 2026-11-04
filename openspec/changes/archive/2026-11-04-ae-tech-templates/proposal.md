# AE 科技风模板：要点列表、总结大字（每秒 60 帧）

## Why
用户试了 MotionGit 开源模板「酷炫科技风」（试片：`output/_平台/模板审片/motiongit-kinetic-tech/`），认可它的画面和 60 帧的顺滑感，但它是网页逐帧截图渲染、只有横屏、带 MotionGit 标志、字数限制很严。用户要求在我们自己的 AE 模板库里做同类效果，先出对比视频看。

## What Changes
- 新增两个整屏模板（出 .mp4），竖屏 9:16 和横屏 16:9 同名同字段，每秒 60 帧：
  - `tech-points`「科技风要点列表」：标题 + 1–5 条带编号的要点，依次出现。
  - `tech-summary`「科技风总结大字」：一行金属质感大字 + 一条渐变分隔线 + 1–2 行说明。
- 画面：深色渐变底、中间泛光、暗角、细颗粒；四角取景框、左上小标题、右上时间码、底部进度刻度；文字带模糊逐字飞入；大字银色金属渐变。不带任何 MotionGit 标志。
- 字体用本机已装的思源黑体（Source Han Sans SC Heavy / Bold / Medium，SIL OFL 免费可商用），数字和时间码用 AE 自带等宽字体。
- 搭建脚本支持按模板设帧率（现有模板保持 30 帧不变）。
- 对比视频：同样的作品 94 文字，横屏 AE 版与 MotionGit 试片上下对比，另出竖屏 AE 版。用户看过认可后再写 checks、标 ready、加进 SKILL.md。

## 不在本次范围
- 成片改每秒 60 帧（现在 `edit_handoff.py` 固定 30 帧）。用户已说要改，单独开一个需求，本次模板认可后再提方案。
- 现有任何模板和作品 93、94 的数据都不动。

## Impact
- 代码：`craft-ae/scripts/make_templates.py`（新模板函数、按模板设帧率）、`landscape_layouts.py`（横屏排版）、`make_previews.py`（预览）；新增 `craft-ae/templates/tech-points/v1/`、`tech-summary/v1/` 的 manifest。
- 工程放本机模板库 `~/AIContentStudio/ae-templates/`，不进 git。
- 说明书每次调用实时读取，不用重启。
