# video-chain-led-by-mcp-model Specification

## Purpose
TBD - created by archiving change video-chain-led-by-mcp-model. Update Purpose after archive.
## Requirements
### Requirement: Video is led by the external model

In the video chain, the 导演稿, material choices, voiceover call, DaVinci / AE decision, 小样, 排版 and 成片 SHALL be decided by the external model through the platform MCP. The platform SHALL NOT call its own models for these steps. Articles and images SHALL keep the platform's abilities.

#### Scenario: Start from the conversation
- **WHEN** the user tells Claude Code 「做海底光缆的视频」
- **THEN** Claude Code reads the brief through MCP, writes the 导演稿 and saves it, and the page shows 导演稿待你看

#### Scenario: No platform model button
- **WHEN** the user opens a video's 内容方案
- **THEN** there is no 生成导演稿 or AI 补齐素材 button; the page shows the current state and review actions

### Requirement: Material request with the 导演稿

The 导演稿 SHALL include a material request per shot. The user SHALL be able to supply material for it; rows the user does not cover SHALL be found or made by the external model through platform tools, and the external model SHALL pick the material for every shot.

#### Scenario: User supplies some footage
- **WHEN** the user adds footage for rows 2 and 5 and approves the 导演稿
- **THEN** rows 2 and 5 use it, the other rows are found or made, and the receipt says which is which

### Requirement: Made in DaVinci Resolve and After Effects

小样, 排版 and 成片 SHALL be produced in DaVinci Resolve and After Effects as far as possible; other tools SHALL be used only for checks and format conversion.

#### Scenario: 小样
- **WHEN** a 小样 is submitted
- **THEN** it comes with its Resolve project and AE files that reopen without missing media

### Requirement: Stops for the user

The chain SHALL stop for the user after the 导演稿, after the 小样 and after the 成片, and SHALL continue only after the user approves on the page.

#### Scenario: 导演稿 changes
- **WHEN** the user leaves notes on the 导演稿
- **THEN** Claude Code saves a new 导演稿 version and waits again

#### Scenario: 小样 then 成片
- **WHEN** the user approves the 小样
- **THEN** Claude Code does 排版 and exports the 成片, which goes to 导出/成片 after the user approves it

### Requirement: The edit follows the 导演稿

Picture content SHALL change only through a new 导演稿 version. Details the 导演稿 does not specify SHALL be listed in the edit receipt.

#### Scenario: A shot must change
- **WHEN** a planned picture cannot work while editing
- **THEN** a new 导演稿 version is saved before the edit continues

### Requirement: Materials are allowed by default

Every material in the library SHALL be allowed for AI editing and publishing. Web-found materials SHALL keep their source credit.

#### Scenario: Old material missing AI permission
- **WHEN** the one-off update runs
- **THEN** every active material allows AI use and public use, and attribution text is unchanged

