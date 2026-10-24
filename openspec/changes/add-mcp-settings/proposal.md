## Why

The platform's own MCP server (`aicontentstudio-creative`) is how the user's large model drives production. As of `add-agent-review-loop` it has 23 tools. But it exists only in code and in local client configs:

- Nothing in the product says it exists, whether it works, which account it acts as, or what it can and cannot do.
- External MCP services the platform calls are registered on the old settings page (`/legacy/settings` → 技能与插件).

The user asked (2026-10-22) to make MCP its own feature item, with all related capabilities in one place, so it is visible and maintainable. On the same day Claude Code was connected locally, alongside the existing Codex entry. That was a client config entry only, with no platform change.

## What Changes

A new settings section **「MCP 接入」** in `/settings`, with four parts:

1. **Connection status** (server-side, no secrets):
   - Whether the platform MCP is enabled: token and owner configured.
   - The acting account (email and role).
   - The endpoint (`/api/v1/creative-mcp`, loopback only).
   - The stdio bridge script and runtime config paths.
   - A **「检测连接」** button that runs a server-side self-check: the configuration is readable, the owner is active and is an editor/admin, and the tool list loads. The token is never returned or shown.
2. **How to connect:** copyable configs for Codex (`~/.codex/config.toml`) and Claude Code (`claude mcp add …`), built from the real paths. Never the token.
3. **Capability list:**
   - Read live from the server's tool registry.
   - Grouped as 生产阶段与决定 / 找素材 / 执行包与回传 / 读取上下文.
   - Each tool shows its description and whether it is read-only or makes changes.
   - A fixed list of what MCP cannot do: accept, reject, bind, approve, publish.
   - The recommended loop (run → send review link → read decision → continue).
4. **External MCP services:** the existing registry (`GET/PUT /api/v1/settings/plugins`, `mcp` list) shown and editable here for admins, with the same validation as today. The old settings page keeps working.

## Impact

- API: new `GET /api/v1/settings/mcp` and `POST /api/v1/settings/mcp/check` (admin). These read `creative_mcp.TOOLS`, the environment presence flags and the owner, using existing helpers. External services reuse the existing plugins endpoints.
- Web: a new `mcp` section in `ProductSettingsPage` with a new `McpSettings.tsx`.
- No schema change, no change to MCP authentication or tools.
