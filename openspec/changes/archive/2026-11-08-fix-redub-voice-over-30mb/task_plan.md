# task_plan

目标：单句重配后的整条配音存成立体声 FLAC，10 分钟内不超 30 MB；超限在调 MiniMax 前拒绝；413 带原因到 MCP。

/// 1. propose：选定 A 立体声 FLAC（实测见 proposal.md），等用户确认
/// 2. voiceover.py `_redub`：WAV 改 ffmpeg 编 FLAC，create_revision 用 .flac / audio/flac
/// 3. `_redub`：调 MiniMax 前按「原配音 FLAC 大小 + 重配区间未压缩大小」估算，超 30 MB 报 voiceover_redub_too_large
/// 4. `_redub`：create_revision 的 413 转成 voiceover_redub_too_large 带中文原因
/// 5. creative_mcp 工具说明、spec delta（改「Redub chosen lines in place」写明 FLAC 和超限错误）
/// 6. 核对入库 / 音频文件夹 / 达芬奇导入 / 浏览器播放能读 FLAC；10 分钟测试配音走一遍拼接存储（不调 MiniMax）
/// 7. 全量测试、openspec validate、archive、README
