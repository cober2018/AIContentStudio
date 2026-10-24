# Findings

- MCP 检查（2026-10-24，经 stdio 直连）：37 个工具全部列出；视频链读写正常，定稿视频经 MCP 存导演稿被拒（video_chain_locked）。当前 Claude Code 会话启动时没加载该 MCP（本地作用域已注册、健康检查通过），需 `/mcp` 重连或新会话。
- 缺口：文字/图文没有「外部模型存稿」工具，Claude Code 只能 `run_stage` 让平台模型写。
- 海底光缆文字现有 4 个主稿修订、图文 1 个，均为平台阶段产出（`workflow_stage`）。
- 用户决定：两种写作方式都要，页面滑动开关切换；每次生成留版本，可删除。范围按文字和图文（用户认可提议中包含图文）。
- 用户更正（2026-10-24）：页面上不能写「Claude Code」，统一叫「第三方模型」（任何经 MCP 接入的外部模型）。其余方案确认。
- 实施时发现：图文当前稿的文字层带事实出处（claims），必须有对应证据登记，否则存稿报 undeclared_embedded_reference；改为平台从 claims 自动登记，并在 brief 的 facts 里给出 fact_pack_item_id / snapshot_checksum。
- MCP 原先只透传 video_chain_* 的错误原文，article_chain_* 会被遮成 creative_domain_conflict；已放开。
- 切到「第三方模型」时若已有平台写的版本，当前版本直接进入「稿件待你看」，也可以直接采用定稿。
