## ADDED Requirements

### Requirement: One storyboard stage for video

New video workflows SHALL have a single AI stage, 导演稿, followed by 专业执行准备. They SHALL NOT have separate 视频脚本 or 镜头计划 stages. Existing workflow versions and runs SHALL keep their stages.

#### Scenario: New video project
- **WHEN** a new video workflow is created from the starter or product definition
- **THEN** its stages are 导演稿 and 专业执行准备 only

#### Scenario: Existing run
- **WHEN** a run was created with the old definition, such as U80
- **THEN** its stages are unchanged and its 导演稿 follows the accepted shot plan

### Requirement: The director draft is a storyboard table

Each 导演稿 candidate SHALL be one table produced in one model answer. Each row is one shot with: 镜头 number, start and end time, 信息点, 画面, 运镜, 台词 with its speaker type, 声音, 备注 and 素材. The platform SHALL compute start, end and total from the shot durations. Durations are estimates, and the final timing follows the narration audio.

#### Scenario: Generate the table
- **WHEN** the user generates the 导演稿 for a new video
- **THEN** the candidate shows one row per shot with all columns, numbered L01, L02… and the total equals the sum of shot durations

#### Scenario: Shot without speech
- **WHEN** a shot has no spoken line
- **THEN** its 台词 shows 无台词

#### Scenario: Older master
- **WHEN** a master made before this change is shown
- **THEN** it shows as a table with 画面 from the shot label and the new columns empty

### Requirement: Material is picked once

A shot's material picked in the shot slot SHALL be carried to the per-shot material choice without picking again. Binding SHALL still happen only when the user saves.

#### Scenario: One pick
- **WHEN** a shot has exactly one slot pick and no bound material
- **THEN** the per-shot choice already shows that pick, and saving binds it

#### Scenario: Several picks
- **WHEN** a shot has more than one slot pick
- **THEN** the per-shot choice lists only those picks for the user to choose
