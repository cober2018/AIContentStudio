# 设计

- `minimax_cli_provider` 的 TTS `generate` 改为 HTTP POST `<base>/t2a_v2`（base 用 `chat_base_url()`，钥匙用现有读取方式），`stream=false`、`output_format=hex`；hex 解码成音频。`subtitle_enable=true` 时下载返回的字幕文件，转成 SRT 放进 `subtitles_srt`，与现在一致。删去命令行 `speech synthesize` 这条路及其能力探测；`speech voices`（音色目录）和转写仍走命令行。
- `model_capability_routing.tts_parameters`：可选字段加 `language_boost`（MiniMax 枚举）与 `voice_modify`（`pitch` / `intensity` / `timbre` 整数 −100..100）；记录在 `tts_applied_parameters`。
- `voiceover.DEFAULT` 加 `language_boost: None`、`voice_modify: {pitch:0,intensity:0,timbre:0}`；`_parameters` 只在非默认时发送。
- 前端 `VoiceSettings.tsx` 加「语言增强」下拉和三个滑杆 / 数字框。
- 失败时报错原样转成大白话（钥匙无效、音色不存在、参数越界）。
