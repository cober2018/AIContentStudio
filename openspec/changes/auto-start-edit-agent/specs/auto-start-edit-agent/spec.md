## ADDED Requirements

### Requirement: Edit starts by itself after the 导演包 is ready

When a video's 导演包 is accepted, the platform SHALL prepare its rough-cut edit task, and the local dispatcher SHALL start the configured assistant for it without user action, one task at a time.

#### Scenario: Auto start
- **WHEN** 准备剪辑 finishes for a video and 自动剪辑 is on
- **THEN** within a few minutes the 制作内容 page shows 剪辑中, and a Claude Code session has claimed the task

#### Scenario: Auto start off
- **WHEN** 自动剪辑 is off
- **THEN** the task stays prepared and the page says it is waiting for an assistant

### Requirement: Rough cut comes back for review only

The assistant SHALL submit the rough cut through the platform and SHALL NOT accept it. The user reviews it on the 制作内容 page.

#### Scenario: Rough cut returned
- **WHEN** the session submits its output
- **THEN** the page shows 粗剪待审 with the video, and nothing is accepted until the user decides

### Requirement: Failures are visible and never silently retried

A failed, timed-out or uncertain start SHALL mark the task with the reason and log path and SHALL NOT be retried automatically.

#### Scenario: DaVinci not available
- **WHEN** the session cannot reach DaVinci
- **THEN** the task shows 出错：达芬奇没打开, with 重试
