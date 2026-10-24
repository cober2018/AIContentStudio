# Findings

- Edit tasks today are creative executions with executor `agent / codex-video-production`, prepared from the 导演包 by the 「准备剪辑任务 / 交给Codex」 button; agents claim them through the platform MCP (`claim_execution`, `start_execution`, …). The MCP cannot accept outputs.
- The handoff accepts the 导演包 but does not prepare an execution (`execution_id` is null).
- `claude` CLI is at `~/.local/bin/claude`; existing launchd jobs `com.aicontent.api` and `com.aicontent.worker` show the install pattern.
- Platform judgment calls use the model set in 设置 → 模型与 AI (currently gemini-3.8-flash-high); the edit itself runs on the assistant that claims the task.
- Edit tasks are created with `web_video_handoff.prepare_edit`; it requires every shot to have material and `postproduction` set, which 准备剪辑 now guarantees.
- Only tasks queued by 准备剪辑 auto-start; tasks prepared by hand stay manual.
- The dispatcher authenticates with the creative MCP token from `scripts/startup/runtime.env`, the same as the stdio MCP bridge.
- Starting an unattended agent session from inside this Claude Code session is blocked by its safety check ("Create Unsafe Agents"); the dispatcher must be installed and first run by the user.
- 2026-10-24 live check, 「剪辑没有反应」: (1) 海底光缆's 准备剪辑 ran at 15:39, before the edit-task step existed, so no edit task was queued; (2) 自动剪辑 was switched off in settings at 16:27; (3) the dispatcher is not installed (no launchd job, no log folder). Added 「开始剪辑」 on 制作内容 when a work has no edit task yet.
- 专业执行准备 is not on the auto-edit path: the edit task builds its own director package from the saved master (`prepare_edit`). The stage only records an accepted 导演包.
- Decision (user, 2026-10-24): auto-edit off; edits are triggered from the harness (user tells Claude Code / Codex to cut a work, which claims the task via the platform MCP). The platform keeps preparing and queuing the task.
- `submit_output.relative_path` must be directly under `outputs/` (no subfolders); keep project dependencies in `outputs/ae/` and submit copies at the top level.
- Resolve's `run_script` sandbox has no `os`/`glob`; resolve file paths in the shell first.
- A session without the platform MCP tools can still use it through `scripts/creative_mcp_stdio.py`, which reads the key itself.
