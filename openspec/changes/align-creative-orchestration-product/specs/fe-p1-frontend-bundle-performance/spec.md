## ADDED Requirements

### Requirement: Creative Execution and Capability Memory remain lazy

Creative Execution package/detail/MCP guidance, Capability Memory management, advanced Workflow automation and legacy compatibility components SHALL load only when their relevant surfaces are opened. Home, Projects list, Opportunities, ordinary Assets list, Learning and unrelated Production modalities MUST NOT statically import professional-execution/legacy editor bundles.

#### Scenario: Open Projects list
- **WHEN** the user loads `/projects` without opening an execution or capability-memory panel
- **THEN** Creative Execution/MCP/legacy compatibility code is outside the initial route closure and existing FE-P1 budgets remain enforced

#### Scenario: Open normal Text editing
- **WHEN** a user edits Text without opening Advanced Automation or professional execution
- **THEN** professional-tool/MCP guidance and legacy Video/Workflow editors are not eagerly loaded
