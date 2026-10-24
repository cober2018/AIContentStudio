## 1. API

- [x] 1.1 `GET /api/v1/settings/mcp`: enabled flags, owner, endpoint, bridge/runtime paths, tools (name, description, group, read-only), cannot-do list, loop text
- [x] 1.2 `POST /api/v1/settings/mcp/check`: config readable, owner active editor/admin, registry loads; no token in any response

## 2. Web

- [x] 2.1 `McpSettings.tsx`: status + 检测连接, Codex/Claude Code snippets with copy, grouped capability list, cannot-do list
- [x] 2.2 External MCP services list editable by admins via existing plugins API
- [x] 2.3 Add `mcp` section to `ProductSettingsPage` directory and nav

## 3. Verify and hand over

- [x] 3.1 Endpoint responses contain no token (checked against runtime value); MCP and settings tests pass; web build passes
- [x] 3.2 Browser check of the section; README, progress, findings
