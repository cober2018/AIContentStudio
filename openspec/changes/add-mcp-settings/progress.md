# Progress

- 2026-10-22: Claude Code connected locally (`claude mcp add aicontentstudio-creative -s local …`, status Connected). Proposal written; waiting for confirmation.
- 2026-10-22: applied. API `GET /api/v1/settings/mcp`, `POST /api/v1/settings/mcp/check` (admin) in `routers/settings.py` + `services/mcp_settings.py`; Web `McpSettings.tsx`, section `mcp` in `ProductSettingsPage`.
- Verified: token string absent from both responses (compared against the runtime value in-process); self-check 5/5 pass, 23 tools in 4 groups; browser check of `/settings?section=mcp` (status, snippets, grouped list with Chinese summaries, cannot-do list, external services showing existing `dsh-web`). Tests `-k "mcp or settings"` see below; web build passes.
