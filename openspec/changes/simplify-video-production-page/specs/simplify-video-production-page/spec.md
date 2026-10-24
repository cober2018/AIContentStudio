## ADDED Requirements

### Requirement: One table and one primary action on the video plan page

For a non-product video work, the 内容方案 page SHALL show the storyboard table once and one primary button whose action follows the state. All other controls SHALL sit in a collapsed 更多 area.

#### Scenario: No draft yet
- **WHEN** the work has no 导演稿 draft
- **THEN** the page shows an empty table area and the button 生成导演稿

#### Scenario: Draft waiting
- **WHEN** a 导演稿 draft is waiting for review
- **THEN** the table is shown once, without the video editor below it, and the button is 采用这版

#### Scenario: Adopt
- **WHEN** the user clicks 采用这版
- **THEN** the draft is accepted, saved as the master and AI 补齐素材 starts without another click, and the button shows filling progress

#### Scenario: A step fails
- **WHEN** saving the master or starting autofill fails
- **THEN** the page shows the reason in plain words and the button retries from the failed step

### Requirement: Production page for video is table, voice, edit package

The 制作内容 page for a non-product video work SHALL show the storyboard table with an editable 素材 column, then 生成配音 and 准备剪辑包 in order. Subtitles, timeline, ASR and per-shot tools SHALL sit in a collapsed 更多 area.

#### Scenario: Open production
- **WHEN** the user opens 制作内容 after adopting the draft
- **THEN** they see the table, ① 生成配音 and ② 准备剪辑包, and nothing else unless they open 更多

### Requirement: Nothing is removed

Every panel that was reachable before SHALL still be reachable through 更多.

#### Scenario: Advanced user
- **WHEN** the user opens 更多 on either page
- **THEN** stage controls, history versions, checks and the timeline tools are available as before
