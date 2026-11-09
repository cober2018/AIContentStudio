# findings

## 2026-11-08 作品99 重配最后一句失败（需求来源）

- 作品：项目 53 / 作品 99「量化数据质量：前中后台三道防线」，导演稿 master 303（第 9 版，已通过），配音 rev 813（MiniMax 克隆音色，4 分 52.9 秒）。
- 起因：用户小样意见「会先查数据（停顿）到齐（停顿）没有吗？停顿不需要」。这句里静音最长只有 0.03 秒，停顿是配音把字拖长了，剪不掉，只能重配 `line-26`。
- 调用：`generate_video_voiceover(project_id=53, unit_id=99, lines=["line-26"])`
- 结果：MCP 返回 `{"code":"creative_domain_bounds","status":413}`，没有原因。
- 日志（logs/api.log）：
  - `2026-11-08 18:26:10,221 HTTP Request: POST https://api.minimaxi.com/v1/t2a_v2 "HTTP/1.1 200 OK"` → MiniMax 已经配完这一句（计费）。
  - `2026-11-08 18:26:10,453 creative mcp tool failed: tool=generate_video_voiceover ... code=creative_domain_bounds status=413 trace=658b99a1d0f04ea3814ec8f50070c6c9 message=None`
- 原因：`voiceover.py` `_redub` 把整条配音写成 `voice.wav`（16 位 PCM，保持原采样率和声道），`create_revision` → `materials.validate_upload` 超过 30 MB 报 413「素材超过 30MB 上限」。本例 297 s × 32000 Hz × 2 声道 × 2 字节 ≈ 36.3 MB。
- 原配音文件：MP3，32 kHz，立体声，320 kbps，11.7 MB；左右声道逐样本相同（max|L−R| = 0）。
- 临界片长：32 kHz 立体声 WAV 约 7.3 MB/分钟，超过约 4 分 7 秒必失败。

## 同一作品之前一次失败（已绕过，记在这里方便对照）
- 第一次调用报 `voiceover_line_split_unclear`：「第 26 句「两盏灯都绿了才准启动，有」字幕终点 285.30 秒附近找不到停顿，离最近的停顿差 0.37 秒」。原因是导演稿里第 25 句最后一条字幕延到了下一句开始（285.30），真正说完在 284.93，超出 0.3 秒容差。已存导演稿第 9 版把这条字幕结束改到 284.93 绕过；这不在本需求范围内。

## 修好以后要做的（作品99 制作方接着做，不是开发任务）
- 重配 `line-26`（再计费一句），听写和看音高确认「到齐没有吗」不再拖音，出新小样给用户通过，再做成片（成片加右下角 Logo 水印、角色收尾、三张封面）。

## 2026-11-08 格式实测（开发方）
- rev 813 解码 PCM 35.75 MB；立体声 FLAC 7.45 MB、单声道 FLAC 7.43 MB，解码回来逐字节相同；10 分钟立体声 FLAC 15.24 MB。
- 原因：左右声道相同，FLAC 侧声道近乎零成本，立体声和单声道一样大 → 选 A，保留立体声，不碰 3 dB 混音规则。
- MCP 已对 `voiceover_` 开头的错误码透传 message（creative_mcp.py 约 905 行），413 只要换成这个前缀的码就有原因。
- 素材类型识别（`sniff_mime`）原来不认 FLAC 魔数，导演稿存档会因 `video_asset_bytes_or_mime_invalid` 拒绝 FLAC 配音；已补。
- ffmpeg 往管道输出 FLAC 时写不回总时长（ffprobe 读成 N/A，duration_ms 为空），必须写文件。
- 估算对最后一句偏保守：最后一句的可用区间到整条结尾，按未压缩算；真实配音最后一句后面只有短尾音，不影响。
