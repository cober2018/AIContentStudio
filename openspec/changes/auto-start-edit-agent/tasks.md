## 1. API

- [x] 1.1 准备剪辑 prepares the rough-cut edit execution (`prepare_edit`, one per saved master) and queues it; skipped with a reason while rows lack material.
- [x] 1.2 `edit_agent.py`: queue in `system_settings.edit_agent_runs`; `GET /edit-agent/next` and `POST /edit-agent/tasks/{id}/report` with the creative MCP token; a stuck "launched" turns failed after 100 min; never auto-restarted.
- [x] 1.3 Settings `edit_agent` (on by default, Claude Code / Codex); `GET/PUT /settings/edit-agent` with the dispatcher's last poll.

## 2. Dispatcher

- [x] 2.1 `scripts/edit_dispatcher.py`: next task → `claude -p` (or `codex exec`) with only the platform MCP and DaVinci MCP, allowed tools listed, 90 min limit, log per task in `~/AIContentStudio/edit-logs/`.
- [x] 2.2 `scripts/install_edit_dispatcher.sh` (launchd, every minute, no overlap). Not installed: installing starts unattended sessions, so the user runs it.

## 3. Web

- [x] 3.1 `EditAgentStatus` on 制作内容: 排队中 / 剪辑中 / 粗剪已回传，待你审片 / 出错 + 重试, link to the task.
- [x] 3.2 Settings 自动剪辑.

## 4. Verify

- [x] 4.1 DB copy: 准备剪辑 queues task #6; next → launched (busy, no second start) → failed (no auto restart) → 重试 → queued; repeating 准备剪辑 reuses the same master and task. Dispatcher dry run against the live API exits cleanly. 204 related API tests pass; web build passes.
- [ ] 4.2 Live headless session (MCP reachability and a real rough cut): blocked in this session by the agent-safety check; the user runs it.

## 5. Docs

- [x] 5.1 README, task_plan, progress, findings.
