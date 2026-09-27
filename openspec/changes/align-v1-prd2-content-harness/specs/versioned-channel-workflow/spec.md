## ADDED Requirements

### Requirement: Workflow definitions are immutable after publish

已发布 Workflow 被修改时，系统 SHALL 创建新 Workflow Version，且历史 Run 的 definition checksum 不变化。

#### Scenario: 修改已发布工作流

- **WHEN** 用户修改一个 published Workflow 的定义
- **THEN** 系统创建新 Workflow Version
- **AND** 历史 Run 引用的 definition checksum 保持不变

### Requirement: Platform branches are independent

同一 Topic 选择多个 target 时，系统 SHALL 为每个 `channel × content_form` 创建独立 WorkflowRun。

#### Scenario: 一个目标失败不影响其他目标

- **WHEN** 同一 Topic 的多个 target 中某个 Run failed/waiting
- **THEN** 其他 Run 的状态与推进不受影响
