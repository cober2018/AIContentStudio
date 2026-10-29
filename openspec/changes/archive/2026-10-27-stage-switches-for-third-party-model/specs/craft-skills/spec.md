## ADDED Requirements

### Requirement: One switch per work controls platform writing skills for third-party models

Each work SHALL have one switch, set by people on its production page and on by default. When on, a third-party model SHALL be able to read the platform's built-in writing skills through get_craft_skill. When off, those reads SHALL be refused. craft-resolve and craft-ae SHALL always be readable regardless of the switch. The model SHALL NOT be able to change the switch.

#### Scenario: Switch off
- **WHEN** the user turns off the switch for project 42's video and the model reads studio.video.product-script@1
- **THEN** the platform refuses with platform_skills_disabled

#### Scenario: Editing skills stay on
- **WHEN** the switch is off and the model reads craft-resolve choose.md
- **THEN** the platform returns choose.md

#### Scenario: Default
- **WHEN** the switch was never touched and the model reads studio.video.product-script@1
- **THEN** the platform returns that skill's instructions

### Requirement: The model is told the switch state

get_video_brief and get_article_brief SHALL include the switch state and the list of platform skills the model can read, with how to read them.

#### Scenario: Brief with switch off
- **WHEN** the switch is off and the model reads the video brief
- **THEN** platform_skills says writing skills are off and lists only craft-resolve and craft-ae as readable
