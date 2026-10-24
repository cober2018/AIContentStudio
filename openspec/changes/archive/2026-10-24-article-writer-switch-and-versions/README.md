# article-writer-switch-and-versions

**Stage:** applied and archived 2026-10-24 (not committed). API restarted.

**What:** 文字/图文作品可选「平台模型」或「第三方模型」写，内容方案页滑动开关切换；第三方模型经 MCP 读资料、存稿、等用户采用或意见，采用即定稿；每次生成都留版本，可删除（当前/定稿/被引用的不能删）。

**Code:** API 新 `services/article_chain.py`, `services/creative_mcp.py`, `services/mcp_settings.py`, `services/content_masters.py`, 路由；Web 开关组件、`CreationRecipePanel` / `ProductionWorkspace`、版本列表组件；skill 说明。Branch `video-chain-and-material-library`.

**Next:** none.
