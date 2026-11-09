# tasks

- [x] 1. 在 proposal「可选做法」里选定存储格式（A / B / C），写进 propose，等用户确认后再动代码。
- [x] 2. `voiceover.py` `_redub`：按选定格式写出拼好的整条配音；`create_revision` 的 suffix、declared_mime、duration 跟着改；确认素材入库、项目 音频 文件夹归档、达芬奇导入和平台播放都能读这个格式。
- [x] 3. 调 MiniMax 之前按片长、采样率、声道和选定格式估算结果大小，超限就用明确错误码 + 中文原因拒绝，不发请求。
- [x] 4. 重配链路上的 413 带原因传到 MCP（不再只回 `creative_domain_bounds`）。
- [x] 5. 更新 `generate_video_voiceover` 工具说明和 `video-chain-led-by-mcp-model` 规格里关于重配结果的描述。
- [x] 6. 验收：按 proposal「验收」四条逐条核对，结果写进 progress.md；作品99 那一句由制作方在修好后重配，不在开发验收里代做计费调用（用测试配音验证 10 分钟场景）。
- [x] 7. 归档（`/opsx:archive`），README 改成已完成。
