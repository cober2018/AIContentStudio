# single-version Specification

## Purpose
TBD - created by archiving change remove-legacy-version. Update Purpose after archive.
## Requirements
### Requirement: Only the new version remains

The platform SHALL NOT keep pages, routes, backend code or tables that only the old version used. Backends the new version still relies on SHALL stay, with their pages living in the new settings or page structure.

#### Scenario: Old page path
- **WHEN** the user opens an old path such as /topics or /handoff
- **THEN** the page no longer exists

#### Scenario: Data sources and templates
- **WHEN** the user opens 设置 → 数据源 or 设置 → 规则与模板
- **THEN** the connector and template tools are there and work as before

### Requirement: No advanced runtime section

Settings SHALL NOT have a 高级运行环境 section. The capability method library SHALL be its own settings section.

#### Scenario: Settings overview
- **WHEN** the user opens 设置
- **THEN** there is no 高级运行环境 card and there is a 能力方法库 card

