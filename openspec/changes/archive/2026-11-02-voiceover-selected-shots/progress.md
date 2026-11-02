# progress

- 2026-11-02 方案已写，等用户确认。
- 2026-11-02 用户确认后开始实施；按用户纠正改为 dub_persona（声音随角色）。
- 2026-11-02 已实施并重启服务，未提交：video_documents board 允许 dub_persona；voiceover 新增 _dubbed_shots/_synthesize_shots/_generate_dubbed（只合成标记镜头、声音取角色固定声音、超长先加速到最多 1.25 倍、按镜头起点拼整片配音轨与字幕、不重排时长）；MCP 导演稿与配音工具说明、video_chain 规则补 dub_persona 用法。
  - 正式库副本验收（作品 92，第 11 镜 shot-10 标「阿玲聊生活」，配音服务用 2.2 秒占位音频代替，未花钱）：只调用 1 次、用阅历姐姐声音；配音从 31.867 秒开始，长 2.2 秒 ≤ 本镜 3 秒；配音轨 = 整片 34.867 秒；所有镜头时长不变；字幕时间对应。超长情况：先 1.1 倍、再 1.38 倍，仍放不下就 409 提示需要多长。
  - 全量只剩 5 个已知失败。
- 2026-11-02 用户报：配音报错经 MCP 返回时说明文字被去掉。原因：creative_mcp.domain_error 只给 video_chain_/article_chain_/reference_video_/shot_grid_/account_import_ 带 message。已修：加 voiceover_、product_persona_（并把 product_persona 纳入可识别错误）；失败日志加 message；超长提示改为「配音加快到 X 倍后要 A 秒，这一镜只有 B 秒，还差 C 秒」。
  - 正式库副本经真实 MCP generate_video_voiceover 验收（占位超长音频）：返回 message「第 10 镜（shot-9）的配音加快到 1.38 倍后要 6.0 秒，这一镜只有 3.8 秒，还差 2.2 秒；请把这一镜改长或缩短台词」。全量只剩 5 个已知失败；API 已重启。
