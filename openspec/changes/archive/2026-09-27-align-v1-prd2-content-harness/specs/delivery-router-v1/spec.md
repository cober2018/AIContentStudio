## ADDED Requirements

### Requirement: Delivery target resolves explicit action

系统 SHALL 按 account capability 选择/展示 `copy_package / assisted_draft / auto_draft`，MUST NOT 将 unavailable action 显示为可执行。

#### Scenario: 选择交付动作

- **WHEN** 用户选择「交付」
- **THEN** 系统按 account capability 选择/展示 `copy_package / assisted_draft / auto_draft`
- **AND** 不将 unavailable action 显示为可执行

### Requirement: WeChat auto draft is candidate-bound

WeChat auto_draft SHALL 绑定 approved Candidate：先创建并提交 DeliveryAttempt(prepared)，publisher MUST 使用批准 render payload 和批准媒体，成功后 SHALL 保存 remote media_id。

#### Scenario: 授权自动草稿

- **WHEN** approved WeChat Candidate 授权 `auto_draft`
- **THEN** 系统先创建并提交 DeliveryAttempt(prepared)
- **AND** publisher 使用批准 render payload 和批准媒体
- **AND** 成功保存 remote media_id

### Requirement: Timeout becomes unknown

publisher 调用超时且无法确认远端结果时，系统 SHALL 置 attempt=unknown、target=reconciliation_needed，且 MUST NOT 自动再次创建远端草稿。

#### Scenario: 远端超时

- **WHEN** publisher 调用超时且无法确认远端结果
- **THEN** attempt=unknown
- **AND** target=reconciliation_needed
- **AND** 系统不得自动再次创建远端草稿

### Requirement: Copy package is universal fallback

对没有 verified draft publisher 的平台，系统 SHALL 保证 approved Candidate 至少可以生成格式完整的 Copy Package，包 MUST 保留 media order/placement 和平台交付说明。

#### Scenario: 无发布器的平台交付

- **WHEN** 平台没有 verified draft publisher
- **THEN** approved Candidate 至少可以生成格式完整的 Copy Package
- **AND** 包保留 media order/placement 和平台交付说明
