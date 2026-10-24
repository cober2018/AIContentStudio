# add-mcp-settings

**Stage:** applied locally and checked in the browser. Not committed, archived or published.

**What:** Settings → 「MCP 接入」 (`/settings?section=mcp`) shows four things:
- the platform MCP's status, plus a self-check;
- how to connect Codex and Claude Code;
- the live tool list with what it cannot do;
- the external MCP services registry.

## Code (uncommitted, working tree on `main`)

| Part | Files |
|---|---|
| API | `apps/api/app/services/mcp_settings.py` (new)<br>`apps/api/app/routers/settings.py`: `GET /settings/mcp`, `POST /settings/mcp/check` |
| Web | `apps/web/src/product/McpSettings.tsx` (new)<br>`ProductSettingsPage.tsx`: section `mcp` |

## Decisions

- **No token is ever returned.** The page shows only whether one is configured.
- **The tool list is read from `creative_mcp.TOOLS`, so new tools appear automatically.** Chinese summaries come from `SUMMARIES`.
- **External services reuse the plugins API.** The old settings page still works.

## Next

Archive, on request. Verification results are in `progress.md`.
