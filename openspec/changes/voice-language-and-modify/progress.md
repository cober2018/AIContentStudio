# 进度

## 2026-10-29 本地实施
- `minimax_cli_provider`：配音改为直接 POST `<MiniMax 地址>/t2a_v2`（hex 解码；字幕文件转 SRT），删命令行 `speech synthesize` 路径与其能力探测；MiniMax 错误码转成大白话（密钥无效、余额不足、参数不对、太频繁、内容检查）。音色目录和转写仍走命令行。
- `model_capability_routing.tts_parameters`：加 `language_boost`（MiniMax 语言枚举）、`voice_modify`（pitch / intensity / timbre 整数 −100..100）。
- `voiceover`：默认值加两项；全 0 的声音调整不发送；配音失败时显示 MiniMax 给的原因。
- 设置接口 `VoiceSettingsIn` 加两项，保存改为只取传了的字段（传 null 可清掉语言增强）。
- 设置页 `VoiceSettings.tsx`：语言增强下拉，音调 / 强度 / 音色三个数字框。
- 男声已配：Chinese；pitch 2、intensity −2、timbre 0（其余：语速 1.1、音量 1.2、音调 1、mp3 32000 / 256 kbps 双声道、开心）。
- 验证：后端 `5 failed, 2463 passed`（5 个已知失败）；tsc、node --test 37/37、build 通过；不花钱的请求演练确认发出的 body 与用户给的配置一致；越界值（pitch 200）被 422 拒绝。
- 待做：真配一次音（花一次钱）、归档。
