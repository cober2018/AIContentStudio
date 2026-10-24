## Why

After 准备剪辑, the 导演包 is ready, but nothing starts the edit. Today the user has to tell an AI assistant "剪海底光缆", and the assistant then claims the task through the platform MCP and works in DaVinci and AE. The user wants the edit to start by itself once the 导演包 is ready, run by the assistant's own model (Claude Code by default), with the user only reviewing the cut.

## What Changes

- **Edit task prepared automatically.** When 准备剪辑 accepts a new 导演包, the platform also prepares the edit task (粗剪) for it, with the existing video-edit executor. Today this needs the 「准备剪辑任务 / 交给Codex」 button under 更多.
- **Local dispatcher starts the assistant.** A small background job on this Mac (launchd, like the existing API and worker jobs) checks every minute for edit tasks that are prepared and allowed to auto-start. For each one, one at a time, it starts a headless Claude Code session (`claude -p`) in the project folder with the platform MCP and the DaVinci MCP connected and the `resolve-edit` / `ae-motion` skills. The session claims the task, cuts and grades in DaVinci, makes the AE shots marked in the 导演包, renders the rough cut, and submits it back through MCP.
- **Result comes back for review.** The rough cut and project files arrive as the task's outputs; the 制作内容 page shows 「粗剪已回传，待你审片」 with the video. Accepting it or writing notes uses the existing review; notes start a 修改 round the same way.
- **Settings → 自动剪辑:** on/off, which assistant (Claude Code by default; Codex as an option), and the log folder. On by default once the dispatcher is installed.
- **Safety rules kept.** One edit at a time. A start that may have reached the assistant is never retried automatically (existing dispatch rule). A failed or timed-out session marks the task 待处理 with the reason and the log path; the page shows 重试. The assistant can only claim and submit; it cannot accept its own output.
- The page shows where the edit is: 排队中 / 剪辑中 / 粗剪待审 / 出错（原因）.
- Not in this change: one-click voice, edit proxies in the standard project folder, final export.

## Impact

- API: prepare the edit execution after the 导演包 is accepted; an `auto_start` flag and a small "next task to start" query for the dispatcher; settings key `edit_agent`.
- New script `apps/api/scripts/edit_dispatcher.py` + launchd plist `com.aicontent.edit-dispatcher` (installed by a script, not by the API).
- Web: status line on 制作内容; settings section 自动剪辑.
- Cost: each edit is one Claude Code session on the user's own Claude account.
