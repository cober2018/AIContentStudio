## ADDED Requirements

### Requirement: Production pages name the external model 第三方模型

User-facing text in the production flow SHALL call the external MCP-connected model 「第三方模型」, not a specific product name. Settings that configure a specific client MAY name it.

#### Scenario: Video waiting to start
- **WHEN** a video has not started
- **THEN** the page says to start it in the third-party model, without naming Claude Code
