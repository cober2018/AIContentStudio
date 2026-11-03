# 进度

- 2026-11-03 写提案，等用户「确认」。
- 2026-11-03 用户「确认」，实施完成（未重启、未提交）：
  - 导演稿声音段 speed_percent（50–200），长度允许差 34 毫秒；非声音轨元素不收这个字段。
  - `voiceover.set_speed` 按 旧倍速/新倍速 换算整片时间轴，经 `edit_handoff._save` 存新主稿（edit_summary speech_speed）；`video_chain._keeps_draft` 登记，不用重新采用；`GET voiceover` 多返回 speech；`PUT voiceover/speed`（80–150）。
  - 规则文字：video_chain「口播声音」、craft-resolve sound.md「声音轨口播衔接」、MCP save_director_draft 说明。
  - 页面：「配音与音乐」配音卡片上方加「口播语速」滑块（有声音轨才显示，配音卡片保留，因为实拍作品个别镜头可能要配音）；分镜声音段标「N 倍速」。
- 核对（数据库副本，作品 94 主稿 #244）：
  - 1.15：总长 117720→102365 毫秒（比 1.1500）；14 段都是 speed_percent 115，截取与放置×1.15 最大差 0.45 毫秒；镜头 500/2750/3220/4950→435/2391/2800/4304，镜头总和=总长；字幕、叠字同比例；配乐不变；作品状态不变（不算新导演稿）。
  - 调回 1.0：所有时间点与原稿最大差 1 毫秒；speed_percent 字段去掉。
  - 校验：截取 0–11500、放置 0–10000、115 能存；去掉 speed_percent 报 video_dialogue_length_mismatch。
  - 页面（无头浏览器，接口返回补上 speech，写请求全部拦截）：滑块显示「1.00 倍 · 全片约 118 秒」，拖动实时变「1.05 倍 · 全片约 112 秒」，松手只发一次 PUT。
  - 前端类型检查通过。
- 2026-11-03 重启接口和 worker：健康检查 ok；`GET voiceover` 对作品 94 返回 speech {speed_percent: 100, duration_ms: 117720}。
- 2026-11-03 后端全量测试：2441 通过、28 跳过、5 失败（都是之前就有的 5 个：schema_lifecycle 1、migrations 3、models_plugins 1，和本次改动无关）。
- 2026-11-03 按 review.md 修两处：creative_mcp.py:482 save_director_draft 说明里「trimmed length must equal placed length」改成「× speed_percent / 100」，和前面新加的一句一致；tasks.md 全部打勾（之前的 sed 在 macOS 上没生效）。可选建议未做。
