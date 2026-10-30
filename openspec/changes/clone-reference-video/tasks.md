## 1. 参考拆解
- [x] 1.1 `reference_video.analyze`（逐词转写、切点、拼图、响度）与存放 —— 实现为 `start` / `local_breakdown`；转写只到句级时间（见 findings）
- [x] 1.2 MCP `analyze_reference_video` / `get_reference_video` / `save_reference_breakdown`；导演稿 `source_kind`、`attitude`
- [x] 1.3 skill `studio.video.reference-breakdown`；页面上传参考、看拆解、拍摄清单与导出
## 2. 视频提示词
- [x] 2.1 skill `studio.video.prompt-direction`；`motion_prompt` 态度前置、首帧四段（`still_prompt`）
## 3. 九宫格
- [x] 3.1 `shot_image.grid` 生成、裁切、放大、登记候选；MCP `generate_storyboard_grid` 与页面按钮；单镜重画 `redraw_cell`
## 4. 收尾
- [x] 4.1a 用两条样本实拆（本机部分）、全量测试、文档
- [ ] 4.1b 页面实测（用户在浏览器里点一遍）、第三方模型按 skill 实际写一次拆解和导演稿、九宫格真实生图一次（付费，待用户决定）、归档
