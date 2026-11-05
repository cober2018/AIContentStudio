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

### Requirement: Approving a sample or final shows in progress until it is written

When the user approves a 小样 or 成片, the platform SHALL first record and save an in-progress approval, then accept the task's outputs, then record the approval and clear the marker; a failure SHALL clear the marker. While the marker exists the chain state SHALL be 「正在通过…」 on the page and `approving` in `get_video_decision`, with a note to check again later, never 「待你看」. A marker older than 5 minutes SHALL be ignored.

#### Scenario: Model asks right after the user clicks 通过
- **WHEN** the user approves the 小样 and the model calls get_video_decision while outputs are still being accepted
- **THEN** it reads state approving with the note to check again, not 小样待你看

### Requirement: Platform-written cover check is kept with the output

The platform-written `cover_check` result SHALL be an allowed output metadata field, so deliveries with a cover and a final are not refused, while an executor-supplied value is still discarded.

#### Scenario: Cover then final delivered
- **WHEN** a cover and then a final are delivered for one task
- **THEN** both are accepted and the cover check is stored and shown on the review page

### Requirement: Films default to 60 fps

When the edit is prepared for a work whose 导演稿 has no recorded frame rate, the platform SHALL set the 小样, the 成片 and every AE intermediate composition to 60 frames per second. A work whose 导演稿 already records a frame rate SHALL keep it, so videos already made are not redone. The Resolve timeline and delivery SHALL use the 导演稿's recorded frame rate.

#### Scenario: New work
- **WHEN** the model prepares the edit of a work that has never been prepared
- **THEN** the 导演稿 records 60 fps for the 小样, the 成片 and its AE compositions, and a 30 fps upload is rejected

#### Scenario: Work already at 30 fps
- **WHEN** the model prepares the 成片 of a work whose 小样 was made at 30 fps
- **THEN** the 导演稿 keeps 30 fps

### Requirement: One DaVinci edit at a time

The platform SHALL let only one video edit task (executor `codex-video-production`) be worked at a time across all works. A claim SHALL be refused with `video_edit_queue_busy` while another work's edit task is claimed, in progress or blocked and has had activity (a state change, a progress report or a submitted file) within the last 30 minutes. The refusal SHALL name the work being edited and how many other edit tasks are waiting, and tell the model to try again later. An edit task SHALL stop holding the slot once it reaches result_ready or any later state, or after 30 minutes without activity; the timeout SHALL NOT change that task's state.

#### Scenario: Second work waits
- **WHEN** the model claims work B's edit task while work A's edit task is in progress with a progress report 5 minutes ago
- **THEN** the claim is refused with `video_edit_queue_busy` naming work A, and work B's task stays prepared

#### Scenario: Slot frees on hand-in
- **WHEN** work A's edit task reaches result_ready and the model claims work B's edit task again
- **THEN** the claim succeeds

#### Scenario: Abandoned session
- **WHEN** work A's edit task has had no activity for more than 30 minutes and the model claims work B's edit task
- **THEN** the claim succeeds and work A's task keeps its state

### Requirement: Edit work files on the drive are kept

The platform SHALL NOT delete files in a work's `工作/` folder when a newer 小样 is returned or when the 成片 is approved; renders, AE shots, images and project files there stay.

#### Scenario: 成片 approved
- **WHEN** the user approves a work's 成片 while earlier task folders hold unregistered renders
- **THEN** every file in the work's `工作/` folder is still there

### Requirement: One Resolve project per work

The edit instructions SHALL tell the model to delete the `-reopen` Resolve project right after the reopen check, and, when it starts a new edit task of a work, to delete that work's Resolve projects from earlier tasks, whose exported .drp files stay on the drive.

#### Scenario: Third task of a work
- **WHEN** the model starts task 47 of a work whose tasks 43 to 46 left Resolve projects
- **THEN** after the reopen check only that work's task 47 project remains in the Resolve project list

### Requirement: Paid generations check the material drive first

Voiceover, image, shot image, shot video and storyboard grid generation SHALL check that the material library is writable before calling the provider. When it is not, the platform SHALL return `material_library_unavailable` with the message 「素材库盘没连接」 and SHALL NOT call the provider. Through MCP the model SHALL receive that code and message.

#### Scenario: Drive unplugged
- **WHEN** the material drive is not mounted and the model calls `generate_video_voiceover`
- **THEN** no request reaches MiniMax and MCP returns `material_library_unavailable` with 「素材库盘没连接」

#### Scenario: Drive mounted
- **WHEN** the drive is mounted and the model calls `generate_video_voiceover`
- **THEN** the voiceover is generated and stored as before

