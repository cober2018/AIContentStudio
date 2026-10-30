# 设计

## 1. 参考拆解
- 新服务 `reference_video.py`：`analyze(db, user, project_id, unit_id, material_revision_id)`。
  - 转写：复用 `local_mlx_asr_provider`（逐词时间）；不可用时用本机 whisper。
  - 切点：ffmpeg `select=gt(scene,0.2)`；每段取首中尾 3 帧，拼成一张带时间标注的拼图。
  - 响度：ebur128。
  - 结果存 `<项目>/工作/<作品>-<号>/参考拆解/`（拼图、transcript.json、cuts.json）和作品记录 `reference_analysis`（路径与摘要）。
- MCP：`analyze_reference_video`（启动 / 取结果）、`save_reference_breakdown`（第三方模型交整体分析 + 时间线 + 拍摄清单，存进作品记录）。导演稿仍用现有 `save_director_draft`。
- 导演稿 `video.master.v2` 每镜 `board` 加可选 `source_kind`（shoot / product_image / generated / ae_template / library）与 `attitude`；拍摄清单由 `source_kind=shoot` 的镜头汇总，存在 `reference_breakdown.shot_list`，页面「导演稿」一步显示并可导出 Markdown 到 `<项目>/导演稿/`。
- 新 skill：`studio.video.reference-breakdown`（平台目录 + `.codex/skills` 交接说明），内容按 hypit `reference-video.md` 改写为中文、按我们的导演稿字段输出。

## 2. 视频提示词
- 新 skill `studio.video.prompt-direction`：上面四条规则 + 口播 / 试吃 / 演示三类示例。
- `product_motion.motion_prompt`：`board.attitude` 有值时放在第一句；首帧生图提示词按四段拼（拍摄方式取 look 的固定写法）。
- `video_chain.RULES` 加一句：写镜头提示词按 `studio.video.prompt-direction`。

## 3. 九宫格
- `shot_image.grid(db, user, project_id, unit_id, shot_ids)`：最多 9 镜，网格比例 = 单镜比例（9:16 镜头 → 9:16 网格），提示词写清「3×3 网格、无边框、每格一个镜头、同一人物服装场景光线」，每格附该镜画面描述。
- 裁切：按等分切；检测边框 / 留白后内缩；每格放大到目标清晰度（沿用现有放大方式，没有就 ffmpeg lanczos）。
- 每格登记为该镜首帧候选（素材放 `<项目>/图片/图片素材/`），不自动采用；页面逐镜采用。
- 商品镜头（board 有商品主体）排除；有人物参考 / 角色形象时作为网格参考图。
- MCP：`generate_storyboard_grid`。页面「素材」一步加「九宫格分镜」按钮。

## 风险
- 网格单格清晰度低：只作首帧，必须放大；放大后仍糊的格子单独重画。
- 生图模型不一定严格画 3×3：裁切前检查格线，失败时提示重试，不静默用错位的格子。
