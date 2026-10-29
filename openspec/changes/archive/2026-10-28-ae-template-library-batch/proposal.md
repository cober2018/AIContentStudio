## Why

craft-ae 现在只有 6 个模板，很多常用画面（关键词强调、金句、标注、人名条、图表、转场、关注引导）每次都要临时搭，风格不统一也容易出错。用户从 video-shotcraft / video-talkcraft 官网按 13 类挑了 46 张卡，要求照着做相似的节奏和手法，固化成平台自己的 AE 模板。

## What Changes

- 新增 46 个 AE 模板（v1），按 3 批做，每批渲染给用户看过、认可后入库，再做下一批。清单见 design.md。
- 外观统一按平台规则重新设计（字体、主题色、1080×1920 竖屏、安全区），节奏和手法参照所选卡片；不复制原卡的代码、文字和素材。
- 模板渲染支持透明背景：叠在画面上用的模板（关键词、标注、人名条、转场、关注卡等）输出带透明通道的 .mov（ProRes 4444），交给达芬奇放上层轨道；manifest 新增 `alpha: true`。整屏模板仍出 .mp4。
- 每批完成后更新 craft-ae `SKILL.md` 模板表；武器库对应条目的「模板候选」改为指向已入库模板。

## Capabilities

### New Capabilities
- `ae-templates`: 第二批 AE 模板库与透明背景渲染。

### Modified Capabilities
（无）

## Impact

- 模板说明书：`apps/api/craft_skills/craft-ae/templates/<id>/v1/manifest.json`（46 个）。
- 模板工程：本机模板库 `~/AIContentStudio/ae-templates/<id>/v1/`，由 `scripts/make_templates.py` 搭建。
- 渲染：`apps/api/app/services/craft_skills.py` `render()` 按 `alpha` 选输出格式与入库 MIME。
- 无数据库迁移，无新依赖（用本机 AE 和 aerender）。
