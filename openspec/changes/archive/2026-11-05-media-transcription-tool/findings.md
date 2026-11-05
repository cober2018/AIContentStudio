# findings

- 平台已有本机转写：`local_mlx_asr_provider`（MLX Whisper，沙箱断网，单次最多 10 分钟、120 秒超时）；`reference_video.transcribe` 在它失败时退回本机 whisper 命令行（large-v3-turbo，900 秒超时）。画面切换用 `reference_video.scene_cuts`。
- opc-asr 用 openai-whisper（PyTorch），平台引擎更快；只借用它的输出约定（一篇一个文件夹、md + images/ 相对引用），不搬代码。
- 用户 2026-11-05 决定：
  - 做成独立小工具，通过 MCP 执行，不进做视频、图文流程。
  - 导航加「小工具」页。
  - 默认输出到素材盘。
- 素材盘根目录下的 `AIContentStudio/` 是平台自用目录（已在保留名单里，现有 其他 / 音频 / 视频 / 图片），转写放 `AIContentStudio/转写/`，不用新增保留名。
- 已有「在访达中显示」做法：`routers/materials.py` 用 `open -R`。
- MLX 转写要读 runtime.env 里的开关（不开时报 local_asr_not_enabled，自动退回 whisper 命令行）。API 进程会读这个开关。
- MLX 输出校验很严（句子时间必须递增、不重叠）。合成的循环音频曾被判 local_asr_output_invalid，那一段由 whisper 命令行接手，结果完整，任务记录里的转写方式会列出两种。
- 现有 MLX 单次限 10 分钟、120 秒；改为每 5 分钟一段。
