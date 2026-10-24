# Progress

- 2026-10-24 MCP 检查完成（见 findings.md），方案写好，等用户确认。
- 2026-10-24 用户确认（改名「第三方模型」）后实施完成：
  - 后端：新 `services/article_chain.py`（开关、状态、存稿、决定、定稿锁、版本列表 / 用这一版 / 删除即隐藏）；`save_revision` 对文字/图文定稿后拒绝；复制一份放开文字并沿用原作品写作方式；路由 `GET/PUT/POST/DELETE .../article-chain[...]`；MCP 新增 `get_article_brief` / `save_article_draft` / `get_article_decision`（mcp_settings「写文章 / 图文」组），`article_chain_*` 错误原文透传给模型；图文存稿时平台自动登记图片层素材和文字层 claims 的出处。
  - 页面：`ArticleChainPanel.tsx`（iPhone 式滑动开关「平台模型 ⇄ 第三方模型」、审稿区、版本列表：查看 / 用这一版 / 删除）；内容方案页挂载，第三方模型方式下不显示平台阶段；定稿后主稿只读，可复制一份；内容矩阵文字也能复制。
  - Skill：新增 `.codex/skills/article-writing/SKILL.md`；视频 skill 中「文章用平台能力」改为按页面开关。
  - 验证：数据库副本上文字全流程（平台方式存稿被拒 → 切换 → 存 v1 → 意见 → 存 v2 → 删旧版 → 当前版不能删 → 采用定稿 → 存稿 / 切换 / 恢复均被拒 → 复制出「· 副本」待审）；图文切换、存稿（含 6 条事实出处）、用这一版。MCP 直连 40 个工具，三个新工具可用、拒绝原因原文返回。浏览器：开关两种状态、版本查看正常，测试后已切回平台模型。后端全量 2808 通过，7 个失败均为原有；前端类型检查通过。
