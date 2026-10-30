# 进度

## 2026-10-29 本地实施（未提交）

代码位置：工作区 main 未提交，与 edit-files-in-project-folder 的未提交改动共存（在其上叠加，未回退）。

已完成：
- 后端：新服务 `apps/api/app/services/reference_video.py`（本机拆解：ffprobe、ffmpeg 切点 `select=gt(scene,0.2)`、每段首中尾三帧拼图、ebur128 响度、转写本机 MLX Whisper → 本机 whisper CLI 兜底；后台线程跑，记录在 SystemSetting `reference_video`）；保存拆解、拍摄清单汇总与导出 Markdown。
- 导演稿 `board` 加可选 `source_kind`、`attitude`（`video_documents.canonical_board`，只在写了时保存，旧文档哈希不变）。
- `product_motion.motion_prompt` 态度排最前；新增 `still_prompt` 四段首帧提示词，`get_shot_video_prompt` 返回 `still_prompt`。
- 九宫格：`shot_image.grid_prompt / cut_grid / upscale / grid / redraw_cell`，候选登记在 `product_i2v_jobs[作品].grid`，不自动采用；`generate` 加 `keep` 参数（九宫格不用商品保真句）。
- MCP 新工具：`analyze_reference_video`、`get_reference_video`（只读）、`save_reference_breakdown`、`generate_storyboard_grid`；`get_video_brief` 加 `reference`；`video_chain.RULES` 加两条。
- 接口：`GET/POST /video-chain/reference`、`POST /video-chain/reference/upload`、`GET /video-chain/reference/grids/{name}`、`POST /video-chain/reference/shot-list/export`；`POST /product-video/storyboard-grid`、`POST /product-video/shots/{id}/grid-redraw`；`GET /product-video` 多 `grid`。
- skill：`studio.video.reference-breakdown@1`、`studio.video.prompt-direction@1`（共享，视频作品可读）；`.codex/skills/video-production-handoff/SKILL.md` 加复刻说明。
- 前端：导演稿一步 `ReferenceVideoPanel`（上传 / 从素材库拖入、拆解结果、拼图、时间线、拍摄清单、导出）；素材一步 `StoryboardGridPanel`（九宫格分镜按钮、每镜候选、用作首帧、只重画这一镜）。

验证：
- 样本 A（薯片 30.2 秒）：8 个切点 / 9 段，平均 3.4 秒一镜，−12.0 LUFS，MLX 转写 12 句；2 张拼图。另经页面接口给作品 83 实传一次，结果相同，写在 `/Volumes/T1000/自媒体素材/20261027_儿童麸质饼干/工作/儿童麸质饼干-83/参考拆解/`。
- 样本 B（保湿霜 24.4 秒）：19 个切点 / 20 段，平均 1.2 秒一镜，−7.6 LUFS，MLX 转写 22 句；whisper 兜底单测 20 句。
- 后端 `pytest -q`：5 failed（已知基线 5 个）、2463 passed、28 skipped。前端 `tsc` 通过；`node --test` 37/37；`npm run build` 通过。
- 重启 API 后 MCP tools/list 共 51 个工具，含 4 个新工具；创意目录列出两个新 skill；`get_craft_skill` 可读 prompt-direction。

未做：页面点击实测、第三方模型实写拆解、九宫格真实生图（付费）、归档。
