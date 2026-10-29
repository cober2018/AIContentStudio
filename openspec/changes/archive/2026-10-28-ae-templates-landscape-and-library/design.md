# 设计

## 说明书（manifest）扩展

```json
{
  "category": "数字与图表",
  "aspect_ratios": ["9:16", "16:9"],
  "project": {"file": "template.aepx", "sha256": "…"},
  "variants": {"16:9": {"project": {"file": "template-16x9.aepx", "sha256": "…"}, "size": [1920, 1080]}},
  "previews": {"9:16": "preview-9x16.mp4", "16:9": "preview-16x9.mp4"}
}
```

- 原 `project` / `size` 仍代表 9:16，旧调用不受影响；横屏放在 `variants["16:9"]`。
- 横屏工程与竖屏放同一个版本目录（`~/AIContentStudio/ae-templates/<id>/v1/template-16x9.aepx`），图片占位文件共用；横屏工程带 16:9 安全区参考层（`guide-16x9.png`）。
- 预览视频放同一目录，内容用示例内容一，叠加类合成在示例画面上。

## 渲染

- `render_ae_template` 增加可选 `aspect`（`9:16` | `16:9`，默认 `9:16`）。没有该画幅工程：`ae_template_aspect_unavailable`（409）。
- 校验对应画幅工程的 SHA256；素材尺寸按该画幅写入。

## 横屏排版原则

- 不是把竖屏拉宽：竖屏上下叠的内容，横屏多改为左右分栏（例如讲者缩位让台：头像在左、图形在右）。
- 叠加类文字块放在左下或右侧 1/3，避开中间人脸区；整屏类按 16:9 重新分栏。
- 字号按横屏阅读距离调整，动画节奏与竖屏一致。
- `check_safe_area.py` 支持按画幅读取规格（16:9：x 91–1828、y 190–959，无按钮列）。

## 预览与页面

- craft-ae 新增 `scripts/make_previews.py`：用示例内容渲染两套动画、合成预览视频、写回 manifest 的 `previews`；审片用的「两套 + 参考卡」对比视频仍放 `output/`。
- 接口：`GET /api/v1/ae-templates`（登录用户，返回类别、名称、用法、字段、图片、画幅、状态、是否有预览）；`GET /api/v1/ae-templates/{id}/{version}/preview/{aspect}`（返回本机模板库里的预览视频，只读）。
- 设置页加「AE 模板库」：按类别分组卡片，竖屏 / 横屏切换，点开播放预览、看用法。只读，不在这里渲染。

## 选模板规则（写进 craft-ae SKILL.md 与 MCP 说明）

1. 默认：大模型按镜头内容和用途自己挑 ready 模板、自己填字段渲染，不问用户。
2. 用户在微调时明确点名某个效果（说名称或类别），必须用对应模板；该模板没有当前画幅或不是 ready 时，先告诉用户，不擅自换。
3. 画幅跟着片子走，竖屏片用 9:16，横屏片用 16:9。
