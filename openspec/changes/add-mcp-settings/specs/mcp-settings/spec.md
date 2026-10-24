## ADDED Requirements

### Requirement: MCP is a visible settings section
The product settings SHALL include an 「MCP 接入」 section. It SHALL show the platform MCP's enabled state, acting account, endpoint, stdio bridge and runtime config paths, plus copyable Codex and Claude Code configurations built from those paths. The MCP token MUST NOT be returned by any settings endpoint or displayed.

#### Scenario: Admin opens MCP settings
- **WHEN** an admin opens `/settings?section=mcp`
- **THEN** the page shows whether the platform MCP is enabled, which account it acts as, and connection snippets that contain no token

#### Scenario: Token missing
- **WHEN** no MCP token is configured
- **THEN** the page shows "未启用" with the config key to set, and the self-check reports `creative_mcp_token_unavailable`

### Requirement: Connection self-check
`POST /api/v1/settings/mcp/check` SHALL verify, without network calls and without returning secrets, that the token and owner are configured, the owner is an active editor/admin, and the tool registry loads. It SHALL return one result per check with pass/fail and a short reason.

#### Scenario: Healthy
- **WHEN** the token and an active admin owner are configured
- **THEN** every check passes and the tool count is reported

### Requirement: Capability list is read from the registry
The section SHALL list every MCP tool from the server registry, with its name, description, group and whether it is read-only. It SHALL also state the actions MCP cannot perform (accept, reject, bind, approve, publish) and the recommended review loop.

#### Scenario: New tool added
- **WHEN** a developer adds a tool to the MCP registry
- **THEN** it appears in the list without a frontend change, under 「其他」 if it has no group

### Requirement: External MCP services are managed in the same section
Admins SHALL view and edit the external MCP service registry in the 「MCP 接入」 section through the existing plugins settings API and validation.

#### Scenario: Register a service
- **WHEN** an admin adds a service with name and URL and saves
- **THEN** it is stored through the existing plugins endpoint and appears in both the new section and the old settings page
