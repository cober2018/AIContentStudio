# auto-start-edit-agent

**Stage:** applied locally (not committed). API restarted. Dispatcher written but not installed; live session not tested.

**What:** 准备剪辑 now also prepares and queues the rough-cut task. A launchd job (`com.aicontent.edit-dispatcher`) starts a headless Claude Code (or Codex) for each queued task, one at a time; it claims the task through the platform MCP, edits in DaVinci and AE, and submits the rough cut. 制作内容 shows 排队中 / 剪辑中 / 粗剪已回传，待你审片 / 出错.

**Code:** API `app/services/edit_agent.py`, `app/routers/edit_agent.py` (new), `app/services/edit_handoff.py`, `app/main.py`; `scripts/edit_dispatcher.py`, `scripts/install_edit_dispatcher.sh` (new). Web `EditAgentStatus.tsx`, `EditAgentSettings.tsx` (new), `VideoStudioShell.tsx`, `ProductSettingsPage.tsx`, `editHandoff.ts`.

**User steps:** run `apps/api/scripts/install_edit_dispatcher.sh` once; click 准备剪辑 on 海底光缆; watch 制作内容.

**Next:** live rough cut on 海底光缆, then review.
