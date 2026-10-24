# article-writer Specification

## Purpose
TBD - created by archiving change article-writer-switch-and-versions. Update Purpose after archive.
## Requirements
### Requirement: Writer switch for text and graphic pieces

Text and graphic pieces SHALL have a slide switch on the 内容方案 page choosing who writes: 平台模型 (the platform's configured model through its stages, the default) or 第三方模型 (any external model over MCP). The switch SHALL be changeable until the piece is final and SHALL NOT delete versions.

#### Scenario: Switch to the third-party model
- **WHEN** the user slides the switch to 第三方模型
- **THEN** the platform stages are hidden and the page shows the waiting state, the version list and the review area

#### Scenario: External model saves while the switch is on 平台模型
- **WHEN** the external model calls save_article_draft and the switch is 平台模型
- **THEN** the save is refused with a message to switch on the page

### Requirement: Third-party model article chain

In third-party mode, the external model SHALL read the brief over MCP, save a draft version and stop; the user SHALL approve or send notes on the page. Approval SHALL make the piece final and read-only; adjustments go into a copy.

#### Scenario: Notes then approval
- **WHEN** the user writes notes on version 1 and the external model saves version 2, which the user approves
- **THEN** the piece is 已定稿 and further saves are refused with 「已定稿，要调整请复制一份」

### Requirement: Every generated version is kept and deletable

Each generated draft (platform stage or third-party model) SHALL appear as a version with its source and time. The user SHALL be able to view it, make it current (as a new version) or delete it; the current, final or referenced version SHALL NOT be deletable.

#### Scenario: Delete an old version
- **WHEN** the user deletes version 2 of 5 that nothing references
- **THEN** it disappears from the list and cannot be restored

