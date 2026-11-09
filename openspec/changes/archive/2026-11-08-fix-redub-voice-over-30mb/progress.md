# progress

- 2026-11-08 propose：实测 rev 813 各格式大小（proposal.md「选定做法」），选 A 立体声 FLAC，待用户确认。未改代码。
- 2026-11-08 apply（用户已确认 A）：
  - voiceover.py：`_flac` 把拼好的 PCM 编成 FLAC（写临时文件，让 ffmpeg 回填总时长）；`_redub` 调 MiniMax 前估算（原配音 FLAC + 重配区间未压缩），超 30 MB 报 `voiceover_redub_too_large`(413) 带片长/预计大小/上限；入库前再查一次；create_revision 改 .flac / audio/flac。
  - materials.py：`_SIGNATURES` 加 `fLaC` → audio/flac。没有它，带 FLAC 配音的导演稿存不进去（`video_asset_bytes_or_mime_invalid`，验证时发现）。
  - creative_executions.py：`_INPUT_EXTENSIONS` 加 audio/flac → .flac，剪辑任务里的配音文件不再叫 .bin，达芬奇按扩展名识别。
  - creative_mcp.py：工具说明写明 FLAC 和 `voiceover_redub_too_large`。
  - spec delta 改为 MODIFIED「Redub chosen lines in place」。
- 验证（数据库副本 + 假 MiniMax，不计费）：
  | 场景 | 结果 |
  |---|---|
  | 作品99 重配 line-26 | 成功；audio/flac 7.27 MB、32 kHz 立体声、292.896 s 与原长相同；接缝外逐样本相同；归档到「音频」；导演稿存下 |
  | 10 分钟立体声重配 line-5 | 成功；14.94 MB、600.000 s；接缝外逐样本相同 |
  | 上限调到 5 MB | 413 `voiceover_redub_too_large`「配音 292.9 秒…预计约 8.4 MB，超过素材 5 MB 上限…」，MCP 带 message；MiniMax 调用 0 次 |
  - 达芬奇导入：Resolve 正开着作品99 的工程，没往里导测试文件；留到第一次真实剪辑时确认。
  - 浏览器播放：Chrome / Safari 原生支持 FLAC，平台按 revision.mime_type 下发。
- 全量测试：2445 通过、5 个失败（schema_lifecycle、migrations×3、models_plugins，与原有失败相同）；openspec validate 通过。
