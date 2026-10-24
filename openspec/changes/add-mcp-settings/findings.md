# Findings

- Platform MCP: loopback HTTP `/api/v1/creative-mcp` + stdio bridge `apps/api/scripts/creative_mcp_stdio.py --runtime-env …`; token and owner in runtime.env (`AICS_CREATIVE_MCP_TOKEN`, `AICS_CREATIVE_MCP_OWNER_USER_ID`).
- Codex already configured in `~/.codex/config.toml` (tool timeout 360 s); Claude Code added 2026-10-22 in local scope.
- External MCP registry lives in `/api/v1/settings/plugins` (`mcp` list), surfaced only on `/legacy/settings`.
- While reading the Codex config, an unrelated MiniMax API key in that file was printed to the chat; user told to rotate it.
- `PUT /settings/plugins` replaces skills and MCP together, so the page sends current skill settings back unchanged when saving MCP services.
- Registry descriptions are for models (English); `mcp_settings.SUMMARIES` gives Chinese summaries for people, falling back to the description for new tools.
- `text-ink-50` and `sm:grid-cols-[auto_minmax(0,1fr)]` did not produce styles here; replaced with slate colours and a flex layout.
