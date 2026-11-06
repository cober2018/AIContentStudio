# 发现
- 时长检查在 creative_media_stream.validate，只取 director.timeline.duration_ms。
- 清单 timeline 起止上限、delivery_checks.inspect 也用 timeline.duration_ms，但都不是成片总长，不改。
