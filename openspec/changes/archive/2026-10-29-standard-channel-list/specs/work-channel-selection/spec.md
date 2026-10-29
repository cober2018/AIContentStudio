## ADDED Requirements

### Requirement: Standard channel list

The platform SHALL keep one standard channel list. Each entry names a channel, its content forms, and per form whether it is ready (built) or planned (listed as a target, not built). Planned entries SHALL NOT trigger any generation, rendering or publishing. When a planned channel is built it SHALL appear as ready and its planned entry SHALL be removed.

#### Scenario: Full list
- **WHEN** the user opens the channel choice of a work
- **THEN** ready channels are selectable and planned channels such as 视频号 show as 待接入 and cannot be chosen

### Requirement: Work channel picked from the list

A work's channel SHALL be chosen from the ready channels that support the work's modality, or left empty. Creating or changing a work with a channel outside the ready list SHALL be refused. Existing works keep their stored channel for reading.

#### Scenario: Graphic work
- **WHEN** the user creates a 图文 work
- **THEN** only 小红书图文 and B站图文笔记 are selectable

#### Scenario: Unknown channel refused
- **WHEN** a request creates a work with channel `abc`
- **THEN** the platform refuses with a plain message and saves nothing

### Requirement: Personas are created only through the persona form

The project page SHALL NOT create personas by name only; it SHALL link to the persona form where brand and voice are required. The page SHALL say 角色 and 作品 instead of 内容身份 and 内容单元.

#### Scenario: Need a new persona while adding a work
- **WHEN** the user wants a persona that does not exist yet
- **THEN** the page offers 新建角色, which opens the persona form
